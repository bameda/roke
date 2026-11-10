"""Stable releases and persistent update channels for Git installations."""

import json
import re
import subprocess
import urllib.error
import urllib.request

from roke import version
from roke.paths import BOX_DIR
from roke.ui import Fail, die, info

STABLE_TAG = r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def git(*args: str, check: bool = True) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(BOX_DIR), *args], capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.TimeoutExpired):
        die("could not run Git; check the installation, connectivity and file permissions")
    if check and result.returncode:
        die(f"could not update roke: {result.stderr.strip() or 'Git command failed'}")
    return result.stdout.strip() if result.returncode == 0 else ""


def channel() -> str:
    saved = git("config", "--local", "--get", "roke.channel", check=False)
    if saved:
        if saved not in ("stable", "main", "development"):
            die("unknown update channel in Git configuration; use --stable or --main")
        return saved
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch == "main":
        return "main"
    tag = git("describe", "--tags", "--exact-match", "HEAD", check=False)
    return "stable" if not branch and re.fullmatch(STABLE_TAG, tag) else "development"


def latest_release(repo: str) -> str:
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+/[\w.-]+?)(?:\.git)?/?",
        repo,
    )
    if not match:
        die("stable updates require a GitHub origin; use --main or update this clone with Git")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{match[1]}/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "roke"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            die("no stable release is available; use roke update --main to follow main")
        die(f"could not check the latest release (GitHub HTTP {error.code}); try again later")
    except (OSError, ValueError):
        die("could not check the latest release; check connectivity to api.github.com")
    if (
        not isinstance(release, dict)
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(release.get("tag_name"), str)
        or not re.fullmatch(STABLE_TAG, release["tag_name"])
    ):
        die("GitHub did not return a stable vMAJOR.MINOR.PATCH release")
    return release["tag_name"]


def installation() -> dict[str, str]:
    """Safe provenance for diagnostic reports; Git is optional for diagnostics."""
    try:
        commit = git("rev-parse", "HEAD")
        selected = channel()
    except Fail:
        return {}
    return (
        {"channel": selected, "commit": commit} if re.fullmatch(r"[0-9a-f]{40,64}", commit) else {}
    )


def describe() -> str:
    """Nearest reachable tag and commit distance, or the short hash without tags."""
    return git("describe", "--tags", "--always", "--abbrev=12", "HEAD")


def update(selected: str = "") -> int:
    if not (BOX_DIR / ".git").exists():
        die(f"{BOX_DIR} is not a Git clone; reinstall roke to update it")
    if git("status", "--porcelain", "--untracked-files=all"):
        die(f"{BOX_DIR} has local changes; commit or move them before updating (git status)")
    wanted = selected or channel()
    if wanted == "development":
        die("this is a development clone; update it with Git or choose --main or --stable")
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if not selected and (
        (wanted == "stable" and branch) or (wanted == "main" and branch != "main")
    ):
        die("the checkout differs from its update channel; update it with Git or choose a channel")

    before = git("rev-parse", "HEAD")
    target = (
        "main" if wanted == "main" else latest_release(git("config", "--get", "remote.origin.url"))
    )
    if wanted == "main":
        info(f"updating {BOX_DIR}: {describe()} → main")
    else:
        info(f"updating {BOX_DIR}: {version.current()} → {target} ({wanted})")
    if wanted == "main":
        git("fetch", "--tags", "origin", "refs/heads/main:refs/remotes/origin/main")
        ref = "refs/remotes/origin/main"
        local = git("rev-parse", "--verify", "refs/heads/main", check=False)
        if local and git("merge-base", local, ref) != local:
            die("local main has commits absent from origin/main; update it with Git")
    else:
        previous = git("describe", "--tags", "--exact-match", "HEAD", check=False)
        if (
            not selected
            and re.fullmatch(STABLE_TAG, previous)
            and tuple(map(int, target[1:].split("."))) < tuple(map(int, previous[1:].split(".")))
        ):
            die(f"refusing to downgrade from {previous} to {target}; choose --stable explicitly")
        git("fetch", "--no-tags", "origin", f"refs/tags/{target}:refs/tags/{target}")
        ref = f"refs/tags/{target}"
    if git("rev-list", "--max-count=1", "HEAD", "--not", "--remotes", "--tags"):
        die("the checkout has local commits not on the remote; update it with Git")
    if wanted == "main":
        git("checkout", "--quiet", "--no-overwrite-ignore", "main")
        git("merge", "--quiet", "--ff-only", ref)
    else:
        git("checkout", "--quiet", "--no-overwrite-ignore", "--detach", ref)
    git("config", "--local", "roke.channel", wanted)
    after = git("rev-parse", "HEAD")
    status = "already up to date" if before == after else "updated"
    if wanted == "main":
        info(f"{status}: {describe()} (main)")
    else:
        info(f"{status}: {target} ({after[:12]}; {wanted})")
    info("Rebuild the images in your projects with: roke build")
    return 0
