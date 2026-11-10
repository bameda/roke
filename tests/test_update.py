"""Updates use real Git checkouts, with GitHub replies supplied by a test shim."""

import json

import pytest


def test_default_install_selects_published_release_not_newer_main(release_repo):
    repo = release_repo
    repo.git(repo.source, "tag", "v99.0.0")  # A tag alone is not a published release.
    repo.publish()
    result = repo.install()
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.1.0\n"
    assert repo.git(repo.installed, "config", "--get", "roke.channel") == "stable"
    assert repo.git(repo.installed, "rev-parse", "HEAD") == repo.git(
        repo.source, "rev-parse", "v0.1.0^{commit}"
    )
    assert (repo.home.parent / "requests.log").read_text().splitlines() == [
        "https://api.github.com/repos/bameda/roke/releases/latest"
    ]


def test_stable_update_and_reinstall_follow_latest_published_release(release_repo):
    repo = release_repo
    assert repo.install().returncode == 0
    config = repo.home / ".config" / "roke" / "roke.env"
    config.write_text("# keep my settings\n")
    repo.commit_version("0.2.0")
    repo.git(repo.source, "tag", "v0.2.0")
    repo.commit_version("0.3.0-dev")
    repo.publish()
    repo.env["RELEASE_RESPONSE"] = json.dumps(
        {"tag_name": "v0.2.0", "draft": False, "prerelease": False}
    )
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.2.0\n"
    assert config.read_text() == "# keep my settings\n"
    result = repo.install()
    assert result.returncode == 0, result.stderr
    assert "installed v0.2.0 (update channel: stable)" in result.stdout


def test_channel_switches_persist_and_do_not_require_project_settings(release_repo):
    repo = release_repo
    assert repo.install().returncode == 0
    result = repo.roke("update", "--main")
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.2.0-dev\n"
    assert repo.git(repo.installed, "config", "--get", "roke.channel") == "main"
    repo.commit_version("0.3.0-dev")
    repo.publish()
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.3.0-dev\n"
    result = repo.roke("update", "--stable")
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.1.0\n"
    assert repo.git(repo.installed, "config", "--get", "roke.channel") == "stable"


def test_main_install_and_legacy_main_install_stay_on_main(release_repo):
    repo = release_repo
    result = repo.install("main")
    assert result.returncode == 0, result.stderr
    repo.git(repo.installed, "config", "--unset", "roke.channel")
    repo.commit_version("0.3.0-dev")
    repo.publish()
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.3.0-dev\n"
    assert repo.git(repo.installed, "symbolic-ref", "--short", "HEAD") == "main"
    result = repo.install()
    assert result.returncode == 0, result.stderr
    assert "installed main (update channel: main)" in result.stdout


@pytest.mark.parametrize("command", ["installer", "update"])
def test_dirty_checkout_is_not_changed(release_repo, command):
    repo = release_repo
    assert repo.install("main").returncode == 0
    modified = repo.installed / "VERSION"
    modified.write_text("my-local-work\n")
    before = repo.git(repo.installed, "rev-parse", "HEAD")
    result = repo.install() if command == "installer" else repo.roke("update", "--stable")
    assert result.returncode != 0
    assert "local changes" in result.stderr
    assert modified.read_text() == "my-local-work\n"
    assert repo.git(repo.installed, "rev-parse", "HEAD") == before
    assert repo.git(repo.installed, "config", "--get", "roke.channel") == "main"


def test_unpushed_main_commit_and_development_branch_are_preserved(release_repo):
    repo = release_repo
    assert repo.install("main").returncode == 0
    repo.git(repo.installed, "config", "user.name", "Test")
    repo.git(repo.installed, "config", "user.email", "test@example.invalid")
    (repo.installed / "VERSION").write_text("local\n")
    repo.git(repo.installed, "commit", "-qam", "local work")
    before = repo.git(repo.installed, "rev-parse", "HEAD")
    result = repo.roke("update")
    assert result.returncode != 0
    assert "local main has commits" in result.stderr
    assert repo.git(repo.installed, "rev-parse", "HEAD") == before
    repo.git(repo.installed, "checkout", "-qb", "feature")
    result = repo.roke("update")
    assert result.returncode != 0
    assert "checkout differs" in result.stderr
    assert repo.git(repo.installed, "symbolic-ref", "--short", "HEAD") == "feature"


@pytest.mark.parametrize(
    "failure",
    [
        {"RELEASE_HTTP_STATUS": "404"},
        {"RELEASE_HTTP_STATUS": "403"},
        {"RELEASE_NETWORK_ERROR": "1"},
        {"RELEASE_RESPONSE": "not json"},
        {"RELEASE_RESPONSE": '{"tag_name":"v0.2.0-rc.1","draft":false,"prerelease":true}'},
        {"RELEASE_RESPONSE": '{"tag_name":"v0.2.0","draft":true,"prerelease":false}'},
    ],
)
def test_release_lookup_failure_does_not_switch_channels_or_fall_back_to_main(
    release_repo, failure
):
    repo = release_repo
    result = repo.install(**failure)
    assert result.returncode != 0
    assert not repo.installed.exists()
    assert repo.install("main").returncode == 0
    before = repo.git(repo.installed, "rev-parse", "HEAD")
    result = repo.roke("update", "--stable", **failure)
    assert result.returncode != 0
    assert repo.git(repo.installed, "rev-parse", "HEAD") == before
    assert repo.git(repo.installed, "config", "--get", "roke.channel") == "main"


def test_update_rejects_conflicting_channels(env):
    result = env.roke("update", "--stable", "--main")
    assert result.code != 0
    assert not result.calls


def test_explicit_release_install_follows_stable_and_reports_provenance(release_repo):
    repo = release_repo
    result = repo.install("v0.1.0")
    assert result.returncode == 0, result.stderr
    assert not (repo.home.parent / "requests.log").exists()
    result = repo.roke("doctor", "--yaml")
    assert '  roke: "0.1.0"' in result.stdout
    assert 'installation:\n  channel: "stable"' in result.stdout
    commit = repo.git(repo.installed, "rev-parse", "HEAD")
    assert f'  commit: "{commit}"' in result.stdout
    assert str(repo.home) not in result.stdout
    assert "github.com" not in result.stdout
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert "already up to date" in result.stderr


def test_downgrade_requires_an_explicit_channel_choice(release_repo):
    repo = release_repo
    repo.commit_version("0.2.0")
    repo.git(repo.source, "tag", "v0.2.0")
    repo.publish()
    assert repo.install("v0.2.0").returncode == 0
    for result in (repo.roke("update"), repo.install()):
        assert result.returncode != 0
        assert "refusing to downgrade" in result.stderr
    assert repo.roke("version").stdout == "roke 0.2.0\n"
    result = repo.roke("update", "--stable")
    assert result.returncode == 0, result.stderr
    assert repo.roke("version").stdout == "roke 0.1.0\n"


def test_failed_fetch_keeps_checkout_and_channel(release_repo):
    repo = release_repo
    assert repo.install("main").returncode == 0
    before = repo.git(repo.installed, "rev-parse", "HEAD")
    result = repo.roke(
        "update", "--stable", GIT_CONFIG_KEY_0=f"url.{repo.home / 'missing.git'}.insteadOf"
    )
    assert result.returncode != 0
    assert "could not update roke" in result.stderr
    assert repo.git(repo.installed, "rev-parse", "HEAD") == before
    assert repo.git(repo.installed, "config", "--get", "roke.channel") == "main"


def test_main_update_shows_tag_distance_before_and_after(release_repo):
    repo = release_repo
    assert repo.install("main").returncode == 0
    before = repo.git(repo.installed, "rev-parse", "HEAD")
    repo.commit_version("0.3.0-dev")
    repo.publish()
    after = repo.git(repo.source, "rev-parse", "HEAD")
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert f"v0.1.0-1-g{before[:12]} → main" in result.stderr
    assert f"updated: v0.1.0-2-g{after[:12]} (main)" in result.stderr


def test_main_update_fetches_new_tags_even_when_main_has_not_moved(release_repo):
    repo = release_repo
    repo.commit_version("0.2.0")
    repo.publish()
    assert repo.install("main").returncode == 0
    before = repo.git(repo.installed, "rev-parse", "HEAD")
    repo.git(repo.source, "tag", "-a", "v0.2.0", "-m", "Second release")
    repo.publish()
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert "already up to date: v0.2.0 (main)" in result.stderr
    assert repo.git(repo.installed, "rev-parse", "HEAD") == before


def test_main_update_without_tags_falls_back_to_short_hash(release_repo):
    repo = release_repo
    repo.git(repo.source, "tag", "-d", "v0.1.0")
    repo.git(repo.source, "push", "origin", ":refs/tags/v0.1.0")
    assert repo.install("main").returncode == 0
    sha = repo.git(repo.installed, "rev-parse", "HEAD")
    result = repo.roke("update")
    assert result.returncode == 0, result.stderr
    assert f"{sha[:12]} → main" in result.stderr
    assert f"already up to date: {sha[:12]} (main)" in result.stderr
