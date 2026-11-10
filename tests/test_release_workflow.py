"""Release preparation and publication in disposable Git repositories."""

import hashlib
import json
import os
import subprocess
import sys

import pytest
from conftest import FAKES, REPO

SCRIPT = REPO / "scripts" / "release.py"


class Release:
    def __init__(self, directory):
        self.root = directory / "repo"
        self.root.mkdir()
        self.remote = directory / "remote.git"
        self.notes = directory / "notes.md"
        self.output = directory / "output"
        self.state = directory / "github.json"
        self.state.write_text("{}")
        self.log = directory / "gh.log"
        self.env = {
            **os.environ,
            "PATH": f"{FAKES}:{os.environ['PATH']}",
            "FAKE_GH_LOG": str(self.log),
            "FAKE_GH_STATE": str(self.state),
        }
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Release test")
        self.git("config", "user.email", "release@example.invalid")
        (self.root / "VERSION").write_text("0.1.0-dev\n")
        (self.root / "CHANGELOG.md").write_text(
            "# Changelog\n\nThe first release has not been published yet.\n"
        )
        (self.root / "install.sh").write_text((REPO / "install.sh").read_text())
        (self.root / "app.py").write_text("# initial\n")
        self.commit("feat: first implementation")
        self.git("init", "-q", "--bare", str(self.remote))
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "origin", "main")

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.root, env=self.env, stderr=subprocess.PIPE, text=True
        ).strip()

    def commit(self, subject, body=""):
        self.git("add", ".")
        self.git("commit", "--allow-empty", "-qm", subject, "-m", body)
        return self.git("rev-parse", "HEAD")

    def run(self, *args, **extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            env={**self.env, **extra},
            capture_output=True,
            text=True,
            timeout=30,
        )

    def prepare(self, bump="patch"):
        return self.run(
            "prepare",
            "--bump",
            bump,
            "--repository",
            "example/roke",
            "--date",
            "2026-11-10",
            "--notes-file",
            str(self.notes),
        )

    def ready(self):
        result = self.prepare()
        assert result.returncode == 0, result.stderr
        return self.commit(f"chore(release): v{result.stdout.strip()}")


@pytest.fixture
def release(tmp_path):
    return Release(tmp_path)


def test_first_release_groups_all_commits_and_promotes_migration_notes(release):
    commits = [release.git("rev-parse", "HEAD")]
    for subject in (
        "fix: a bug",
        "docs: explain setup",
        "test: cover setup",
        "chore(deps): update",
        "An old commit",
    ):
        (release.root / "app.py").write_text(subject + "\n")
        commits.append(release.commit(subject))
    (release.root / "app.py").write_text("# new config\n")
    commits.append(
        release.commit(
            "feat(config)!: rename a setting",
            "BREAKING CHANGE: Rename OLD_SETTING to NEW_SETTING.\nRestart the session.\n\n"
            "Signed-off-by: Person <person@example.invalid>",
        )
    )
    result = release.prepare()
    assert result.returncode == 0, result.stderr
    assert result.stdout == "0.1.0\n"
    changelog = (release.root / "CHANGELOG.md").read_text()
    assert "## [0.1.0] - 2026-11-10" in changelog
    for title in (
        "Breaking changes",
        "Features",
        "Fixes",
        "Documentation",
        "Tests",
        "Maintenance",
        "Other changes",
    ):
        assert f"### {title}" in changelog
    assert changelog.index("### Breaking changes") < changelog.index("### Features")
    assert "Rename OLD_SETTING to NEW_SETTING." in changelog
    assert "Restart the session." in changelog
    assert "Signed-off-by" not in changelog
    for sha in commits:
        assert f"https://github.com/example/roke/commit/{sha}" in changelog
    assert "first release has not been published" not in changelog
    release.commit("chore(release): v0.1.0")
    assert release.run("verify").returncode == 0


@pytest.mark.parametrize(
    "current,bump,expected",
    [
        ("0.1.0-dev", "patch", "0.1.0"),
        ("0.1.0-dev", "minor", "0.2.0"),
        ("0.1.0-dev", "major", "1.0.0"),
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
    ],
)
def test_version_increments(release, current, bump, expected):
    (release.root / "VERSION").write_text(current + "\n")
    release.commit("chore: select development version")
    result = release.prepare(bump)
    assert result.returncode == 0, result.stderr
    assert (release.root / "VERSION").read_text() == expected + "\n"


def test_subsequent_release_preserves_history_and_only_lists_new_commits(release):
    first = release.ready()
    history = release.notes.read_text()
    release.git("tag", "v0.1.0", first)
    (release.root / "app.py").write_text("# fixed\n")
    fix = release.commit("fix: new correction")
    result = release.prepare()
    assert result.returncode == 0, result.stderr
    assert result.stdout == "0.1.1\n"
    assert history in (release.root / "CHANGELOG.md").read_text()
    assert fix in release.notes.read_text()
    assert "first implementation" not in release.notes.read_text()
    release.commit("chore(release): v0.1.1")
    assert release.run("verify").returncode == 0


def test_dirty_tree_and_existing_tag_stop_preparation(release):
    (release.root / "app.py").write_text("# unfinished\n")
    assert release.prepare().returncode != 0
    assert (release.root / "VERSION").read_text() == "0.1.0-dev\n"
    release.commit("fix: finish work")
    release.git("tag", "v0.1.0")
    result = release.prepare()
    assert result.returncode != 0
    assert "already exists" in result.stderr


def test_verify_rejects_main_changes_after_preparation(release):
    release.ready()
    (release.root / "app.py").write_text("# more code\n")
    release.commit("fix: arrived after preparation")
    result = release.run("verify")
    assert result.returncode != 0
    assert "main changed" in result.stderr
    assert not release.log.exists()


def test_verify_rejects_removed_commit_links(release):
    original = release.git("rev-parse", "HEAD")
    release.ready()
    path = release.root / "CHANGELOG.md"
    path.write_text(path.read_text().replace(f"/commit/{original}", "/commit/missing"))
    release.commit("docs: accidentally remove a commit")
    result = release.run("verify")
    assert result.returncode != 0
    assert "missing commit" in result.stderr


def test_stale_merge_fails_ci_and_patch_refreshes_the_unpublished_version(release):
    release.git("checkout", "-qb", "release/next")
    release.ready()
    release.git("checkout", "-q", "main")
    (release.root / "app.py").write_text("# arrived on main while the PR was open\n")
    fix = release.commit("fix: concurrent work on main")
    release.git("merge", "--no-ff", "release/next", "-m", "Merge release PR")
    result = release.run("candidate", "--verify", "--output", str(release.output))
    assert result.returncode != 0
    assert "main changed" in result.stderr
    result = release.prepare()
    assert result.returncode == 0, result.stderr
    assert result.stdout == "0.1.0\n"
    assert fix in release.notes.read_text()
    assert "chore(release)" not in release.notes.read_text()
    assert (release.root / "CHANGELOG.md").read_text().count("## [0.1.0]") == 1
    release.commit("chore(release): v0.1.0")
    result = release.run("candidate", "--verify", "--output", str(release.output))
    assert result.returncode == 0, result.stderr
    assert release.output.read_text() == "candidate=true\n"
    result = release.run("publish", "--repository", "example/roke")
    assert result.returncode == 0, result.stderr


def test_preparation_refuses_empty_releases(release):
    release.ready()
    release.git("tag", "v0.1.0")
    result = release.prepare()
    assert result.returncode != 0
    assert "no commits" in result.stderr


def test_candidate_only_when_commit_changes_to_a_stable_version(release):
    assert release.run("candidate", "--output", str(release.output)).returncode == 0
    assert release.output.read_text() == "candidate=false\n"
    release.ready()
    release.output.unlink()
    assert release.run("candidate", "--output", str(release.output)).returncode == 0
    assert release.output.read_text() == "candidate=true\n"
    (release.root / "app.py").write_text("# subsequent work\n")
    release.commit("fix: later work")
    release.output.unlink()
    assert release.run("candidate", "--output", str(release.output)).returncode == 0
    assert release.output.read_text() == "candidate=false\n"


def test_publish_creates_tag_notes_installer_and_checksum_then_is_idempotent(release):
    sha = release.ready()
    result = release.run("publish", "--repository", "example/roke")
    assert result.returncode == 0, result.stderr
    state = json.loads(release.state.read_text())["v0.1.0"]
    assert not state["isDraft"]
    assert state["notes"] == release.notes.read_text()
    installer = state["assets"]["install.sh"]
    assert installer == (release.root / "install.sh").read_text()
    assert (
        state["assets"]["SHA256SUMS"]
        == f"{hashlib.sha256(installer.encode()).hexdigest()}  install.sh\n"
    )
    assert release.git("ls-remote", "origin", "refs/tags/v0.1.0^{}").split()[0] == sha
    calls = [json.loads(line)[1] for line in release.log.read_text().splitlines()]
    assert calls.index("create") < calls.index("upload") < calls.index("edit")
    result = release.run("publish", "--repository", "example/roke")
    assert result.returncode == 0, result.stderr
    assert "already published" in result.stdout
    assert json.loads(release.state.read_text())["v0.1.0"] == state


def test_failed_upload_leaves_draft_and_can_be_retried(release):
    release.ready()
    result = release.run("publish", "--repository", "example/roke", FAKE_GH_FAIL="upload")
    assert result.returncode != 0
    assert json.loads(release.state.read_text())["v0.1.0"]["isDraft"]
    result = release.run("publish", "--repository", "example/roke")
    assert result.returncode == 0, result.stderr
    assert not json.loads(release.state.read_text())["v0.1.0"]["isDraft"]
    calls = [json.loads(line)[1] for line in release.log.read_text().splitlines()]
    assert calls.count("create") == 1


def test_remote_tag_pointing_elsewhere_is_never_moved(release):
    release.ready()
    release.git("tag", "v0.1.0", "HEAD^")
    release.git("push", "-q", "origin", "refs/tags/v0.1.0")
    before = release.git("ls-remote", "origin", "refs/tags/v0.1.0")
    result = release.run("publish", "--repository", "example/roke")
    assert result.returncode != 0
    assert "will not be moved" in result.stderr
    assert release.git("ls-remote", "origin", "refs/tags/v0.1.0") == before
    assert not release.log.exists()


def test_older_release_cannot_replace_a_newer_published_release(release):
    release.ready()
    release.state.write_text(
        json.dumps({"v9.0.0": {"tagName": "v9.0.0", "isDraft": False, "isPrerelease": False}})
    )
    result = release.run("publish", "--repository", "example/roke")
    assert result.returncode != 0
    assert "newer release" in result.stderr
    assert "v0.1.0" not in json.loads(release.state.read_text())
    assert not release.git("ls-remote", "origin", "refs/tags/v0.1.0")
