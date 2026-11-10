"""Prepare and publish releases. Runs in CI or a disposable maintainer checkout.

No third-party Python packages; GitHub operations use the runner's gh CLI.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
HEADING = re.compile(rf"^## \[({VERSION})\] - (\d{{4}}-\d{{2}}-\d{{2}})$", re.M)
GROUPS = {
    "feat": "Features",
    "fix": "Fixes",
    "docs": "Documentation",
    "test": "Tests",
    "perf": "Performance",
    "refactor": "Refactoring",
    "build": "Build and dependencies",
    "chore": "Maintenance",
    "ci": "CI",
}


def command(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if check and result.returncode:
        raise ValueError(f"{args[0]} failed: {result.stderr.strip()}")
    return result


def git(*args: str) -> str:
    return command("git", *args).stdout.strip()


def clean() -> None:
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("use a clean checkout before preparing or publishing a release")


def repository(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise argparse.ArgumentTypeError("expected GitHub OWNER/REPO")
    return value


def number(value: str) -> tuple[int, ...]:
    if not re.fullmatch(VERSION, value):
        raise ValueError(f"invalid stable version: {value}")
    return tuple(map(int, value.split(".")))


def next_version(current: str, bump: str) -> str:
    development = current.endswith("-dev")
    major, minor, patch = number(current.removesuffix("-dev"))
    if bump == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump == "minor":
        minor, patch = minor + 1, 0
    elif not development:
        patch += 1
    return f"{major}.{minor}.{patch}"


def previous_release(changelog: str, base: str) -> str:
    heading = HEADING.search(changelog)
    if not heading:
        return ""
    tag = f"v{heading[1]}"
    if command("git", "merge-base", "--is-ancestor", tag, base, check=False).returncode:
        raise ValueError(
            f"previous release {tag} must exist and be an ancestor of the release base"
        )
    return tag


def commits(previous: str, base: str) -> list[tuple[str, str, str]]:
    revision = f"{previous}..{base}" if previous else base
    raw = command(
        "git", "log", "--reverse", "--no-merges", "--format=%H%x1f%s%x1f%b%x1e", revision
    ).stdout
    records = [
        tuple(record.strip("\n").split("\x1f", 2))
        for record in raw.split("\x1e")
        if record.strip("\n")
    ]
    result = []
    for sha, subject, body in records:
        if re.fullmatch(rf"chore\(release\): v{VERSION}(?: \(#[0-9]+\))?", subject):
            paths = set(
                git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha).splitlines()
            )
            if paths <= {"VERSION", "CHANGELOG.md"}:
                continue
        result.append((sha, subject, body))
    return result


def escape(value: str) -> str:
    return re.sub(r"([\\`*_[\]<>])", r"\\\1", value)


def notes(version: str, date: str, base: str, previous: str, repo: str) -> str:
    groups: dict[str, list[str]] = {}
    breaking = []
    for sha, subject, body in commits(previous, base):
        link = f"[{sha[:8]}](https://github.com/{repo}/commit/{sha})"
        entry = f"- {escape(subject)} ({link})"
        match = re.match(r"([a-z]+)(?:\([^\n)]+\))?(!)?: ", subject)
        kind = match[1] if match else ""
        groups.setdefault(GROUPS.get(kind, "Other changes"), []).append(entry)
        footer = re.search(r"^BREAKING[ -]CHANGE:\s*(.*)", body, re.M)
        if footer or (match and match[2]):
            detail = "Review this commit for migration steps."
            if footer:
                detail = re.split(
                    r"\n(?=[A-Za-z][A-Za-z-]+: )", body[footer.start(1) :], maxsplit=1
                )[0].strip()
            breaking.append(entry + "\n" + "\n".join(f"  {line}" for line in detail.splitlines()))
    if not groups:
        raise ValueError("there are no commits to release")
    lines = [f"## [{version}] - {date}", "", f"<!-- roke-release-base: {base} -->", ""]
    if breaking:
        lines += ["### Breaking changes", "", "\n".join(breaking), ""]
    for title in dict.fromkeys([*GROUPS.values(), "Other changes"]):
        if title in groups:
            lines += [f"### {title}", "", "\n".join(groups[title]), ""]
    url = (
        f"https://github.com/{repo}/compare/{previous}...v{version}"
        if previous
        else f"https://github.com/{repo}/commits/v{version}"
    )
    lines.append(f"[All commits]({url})")
    return "\n".join(lines) + "\n"


def prepare(args) -> str:
    clean()
    base = git("rev-parse", "HEAD")
    changelog = Path("CHANGELOG.md").read_text()
    current = Path("VERSION").read_text().strip()
    headings = list(HEADING.finditer(changelog))
    pending = (
        bool(headings)
        and headings[0][1] == current
        and command("git", "rev-parse", "--verify", f"refs/tags/v{current}", check=False).returncode
        != 0
    )
    history = changelog
    if pending:
        if args.bump != "patch":
            raise ValueError("finish the unpublished release first; patch refreshes its notes")
        history = changelog[headings[1].start() :] if len(headings) > 1 else ""
    previous = previous_release(history, base)
    version = current if pending else next_version(current, args.bump)
    if previous and number(version) <= number(previous[1:]):
        raise ValueError("the new version must be newer than the previous release")
    if (
        command("git", "rev-parse", "--verify", f"refs/tags/v{version}", check=False).returncode
        == 0
    ):
        raise ValueError(f"tag v{version} already exists")
    date = dt.date.fromisoformat(args.date).isoformat()
    section = notes(version, date, base, previous, args.repository)
    first = HEADING.search(changelog)
    header = changelog[: first.start()] if first else changelog
    header = header.replace("The first release has not been published yet.", "").rstrip()
    if not pending:
        history = changelog[first.start() :] if first else ""
    Path("VERSION").write_text(version + "\n")
    Path("CHANGELOG.md").write_text(header + "\n\n" + section + ("\n" + history if history else ""))
    Path(args.notes_file).write_text(section)
    return version


def candidate(output: Path, check: bool = False) -> None:
    current = Path("VERSION").read_text().strip()
    previous = command("git", "show", "HEAD^:VERSION", check=False).stdout.strip()
    ready = bool(re.fullmatch(VERSION, current)) and current != previous
    if not ready and re.fullmatch(VERSION, current):
        tagged = (
            command("git", "rev-parse", "--verify", f"refs/tags/v{current}", check=False).returncode
            == 0
        )
        old_notes = command("git", "show", "HEAD^:CHANGELOG.md", check=False).stdout
        ready = not tagged and Path("CHANGELOG.md").read_text() != old_notes
    if ready and check:
        verify()
    with output.open("a") as stream:
        stream.write(f"candidate={str(ready).lower()}\n")


def verify() -> tuple[str, str]:
    clean()
    version = Path("VERSION").read_text().strip()
    number(version)
    changelog = Path("CHANGELOG.md").read_text()
    headings = list(HEADING.finditer(changelog))
    if not headings or headings[0][1] != version:
        raise ValueError("VERSION must match the first release in CHANGELOG.md")
    end = headings[1].start() if len(headings) > 1 else len(changelog)
    section = changelog[headings[0].start() : end].strip() + "\n"
    marker = re.search(r"^<!-- roke-release-base: ([0-9a-f]{40}|[0-9a-f]{64}) -->$", section, re.M)
    if not marker:
        raise ValueError("release notes are missing the source commit")
    base = marker[1]
    git("merge-base", "--is-ancestor", base, "HEAD")
    revisions = git("rev-list", "--no-merges", f"{base}..HEAD").splitlines()
    paths = set(git("diff", "--name-only", base, "HEAD").splitlines())
    for revision in revisions:
        paths.update(
            git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", revision).splitlines()
        )
    if paths - {"VERSION", "CHANGELOG.md"}:
        raise ValueError("main changed after release preparation; run Prepare release again")
    previous = previous_release(changelog[end:], base)
    if previous and number(version) <= number(previous[1:]):
        raise ValueError("the new version must be newer than the previous release")
    for sha, _, _ in commits(previous, base):
        if f"/commit/{sha})" not in section:
            raise ValueError(f"release notes are missing commit {sha}")
    return version, section


def gh(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return command("gh", *args, "--repo", repo, check=check)


def publish(args) -> str:
    version, section = verify()
    tag, sha = f"v{version}", git("rev-parse", "HEAD")
    remote = git("ls-remote", "--tags", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}")
    if remote:
        targets = dict(line.split()[::-1] for line in remote.splitlines())
        target = targets.get(f"refs/tags/{tag}^{{}}", targets[f"refs/tags/{tag}"])
        if target != sha:
            raise ValueError(f"remote tag {tag} points to another commit; it will not be moved")
    else:
        local = command("git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}", check=False)
        if local.returncode == 0 and local.stdout.strip() != sha:
            raise ValueError(f"local tag {tag} points to another commit")
    existing = gh(args.repository, "release", "view", tag, "--json", "isDraft", check=False)
    if existing.returncode == 0 and not json.loads(existing.stdout)["isDraft"]:
        return f"{tag} is already published"
    releases = json.loads(
        gh(
            args.repository,
            "release",
            "list",
            "--limit",
            "100",
            "--json",
            "tagName,isDraft,isPrerelease",
        ).stdout
    )
    for release in releases:
        name = release["tagName"]
        if (
            not release["isDraft"]
            and not release["isPrerelease"]
            and re.fullmatch(f"v{VERSION}", name)
            and number(name[1:]) > number(version)
        ):
            raise ValueError(f"a newer release ({name}) is already published")
    if not remote:
        if local.returncode:
            git("tag", "-a", tag, "-m", f"roke {tag}", sha)
        git("push", "origin", f"refs/tags/{tag}")
    with tempfile.TemporaryDirectory(prefix="roke-release-") as directory:
        dest = Path(directory)
        notes_file = dest / "notes.md"
        notes_file.write_text(section)
        installer = dest / "install.sh"
        installer.write_bytes(Path("install.sh").read_bytes())
        checksums = dest / "SHA256SUMS"
        checksums.write_text(f"{hashlib.sha256(installer.read_bytes()).hexdigest()}  install.sh\n")
        if existing.returncode:
            gh(
                args.repository,
                "release",
                "create",
                tag,
                "--verify-tag",
                "--draft",
                "--title",
                f"roke {tag}",
                "--notes-file",
                str(notes_file),
            )
        gh(args.repository, "release", "upload", tag, str(installer), str(checksums), "--clobber")
        gh(
            args.repository,
            "release",
            "edit",
            tag,
            "--draft=false",
            "--latest",
            "--notes-file",
            str(notes_file),
        )
    return f"published {tag} at {sha}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="update VERSION and CHANGELOG.md")
    prep.add_argument("--bump", choices=("patch", "minor", "major"), required=True)
    prep.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    prep.add_argument("--repository", type=repository, required=True)
    prep.add_argument("--notes-file", required=True)
    inspect = sub.add_parser("candidate", help="write whether HEAD changes the stable version")
    inspect.add_argument("--output", type=Path, required=True)
    inspect.add_argument(
        "--verify", action="store_true", help="verify release candidates during CI"
    )
    sub.add_parser("verify", help="validate that the notes cover the release's code")
    release = sub.add_parser("publish", help="publish the verified tag, notes and installer")
    release.add_argument("--repository", type=repository, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            print(prepare(args))
        elif args.command == "candidate":
            candidate(args.output, args.verify)
        elif args.command == "verify":
            print(verify()[0])
        else:
            print(publish(args))
    except (ValueError, OSError) as error:
        print(f"release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
