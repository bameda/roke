"""The installer, run as `curl ... | bash` would run it, against a local
clone of this repository standing in for GitHub."""

import os
import subprocess

import pytest
from conftest import REPO

INSTALLER = (REPO / "install.sh").read_text()


@pytest.fixture
def origin(tmp_path):
    bare = tmp_path / "roke.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(REPO), str(bare)], check=True)
    branch = (
        subprocess.run(
            ["git", "-C", str(REPO), "branch", "--show-current"], capture_output=True, text=True
        ).stdout.strip()
        or "main"
    )
    return bare, branch


def pipe_install(home, origin, cwd=None, script=INSTALLER, **extra):
    bare, branch = origin
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "ROKE_REPO": str(bare),
        "ROKE_VERSION": branch,
        **extra,
    }
    return subprocess.run(
        ["bash"],
        input=script,
        env=env,
        cwd=cwd or home,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_fresh_install(tmp_path, origin):
    home = tmp_path / "home"
    home.mkdir()
    r = pipe_install(home, origin)
    assert r.returncode == 0, r.stderr
    link = home / ".local" / "bin" / "roke"
    assert os.readlink(link) == str(home / ".local" / "share" / "roke" / "bin" / "roke")
    assert (home / ".config" / "roke" / "roke.env").is_file()
    assert "installing into" in r.stdout


def test_reinstall_updates(tmp_path, origin):
    home = tmp_path / "home"
    home.mkdir()
    pipe_install(home, origin)
    r = pipe_install(home, origin)
    assert r.returncode == 0, r.stderr
    assert "updating" in r.stdout


def test_piped_from_inside_a_clone_still_installs(tmp_path, origin):
    home = tmp_path / "home"
    home.mkdir()
    r = pipe_install(home, origin, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert "installing into" in r.stdout and "using this clone" not in r.stdout


def test_truncated_download_runs_nothing(tmp_path, origin):
    home = tmp_path / "home"
    home.mkdir()
    half = "\n".join(INSTALLER.splitlines()[:60])
    pipe_install(home, origin, script=half)
    assert not (home / ".local").exists()
