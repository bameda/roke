"""Local Git repositories and simulated GitHub replies for installer/update tests."""

import json
import os
import shutil
import subprocess
import sys

from conftest import FAKES, REPO


class ReleaseRepo:
    def __init__(self, tmp_path):
        self.source = tmp_path / "source"
        self.source.mkdir()
        files = (
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(REPO),
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                ]
            )
            .decode()
            .split("\0")
        )
        for name in filter(None, files):
            source = REPO / name
            if source.is_file():
                dest = self.source / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.remote = tmp_path / "remote.git"
        self.installed = self.home / ".local" / "share" / "roke"
        shim_dir = tmp_path / "shim"
        shim_dir.mkdir()
        # The launcher still runs with -I. Only external GitHub responses are
        # replaced, before its original bootstrap, in this disposable Python shim.
        mock = """
import io
import os
import urllib.error
import urllib.request
def _release_response(request, timeout=30):
    with open(os.environ["RELEASE_REQUEST_LOG"], "a") as log:
        log.write(request.full_url + "\\n")
    status = os.environ.get("RELEASE_HTTP_STATUS")
    if status:
        raise urllib.error.HTTPError(request.full_url, int(status), "test error", {}, None)
    if os.environ.get("RELEASE_NETWORK_ERROR"):
        raise urllib.error.URLError("test network error")
    return io.BytesIO(os.environ["RELEASE_RESPONSE"].encode())
urllib.request.urlopen = _release_response
"""
        shim = shim_dir / "python3"
        shim.write_text(
            f"#!{sys.executable}\nimport os, sys\nargs = sys.argv[1:]\n"
            f"prefix = {mock!r}\n"
            "if '-c' in args:\n"
            "    index = args.index('-c') + 1\n"
            "    args[index] = prefix + '\\n' + args[index]\n"
            "elif '-' in args:\n"
            "    index = args.index('-')\n"
            "    args = [*args[:index], '-c', prefix + '\\n' + sys.stdin.read(), *args[index+1:]]\n"
            f"os.execv({sys.executable!r}, [{sys.executable!r}, *args])\n"
        )
        shim.chmod(0o755)
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{shim_dir}:{FAKES}:{os.environ['PATH']}",
            "FAKE_DOCKER_LOG": str(tmp_path / "docker.log"),
            "RELEASE_REQUEST_LOG": str(tmp_path / "requests.log"),
            "RELEASE_RESPONSE": json.dumps(
                {"tag_name": "v0.1.0", "draft": False, "prerelease": False}
            ),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"url.{self.remote}.insteadOf",
            "GIT_CONFIG_VALUE_0": "https://github.com/bameda/roke.git",
        }
        self.git(self.source, "init", "-q", "-b", "main")
        self.git(self.source, "config", "user.name", "Release test")
        self.git(self.source, "config", "user.email", "release@example.invalid")
        self.commit_version("0.1.0")
        self.git(self.source, "tag", "-a", "v0.1.0", "-m", "First release")
        self.commit_version("0.2.0-dev")
        self.git(self.source, "init", "-q", "--bare", str(self.remote))
        self.git(self.source, "remote", "add", "origin", str(self.remote))
        self.publish()

    def git(self, directory, *args):
        return subprocess.check_output(
            ["git", "-C", str(directory), *args], env=self.env, stderr=subprocess.PIPE, text=True
        ).strip()

    def commit_version(self, value):
        (self.source / "VERSION").write_text(value + "\n")
        self.git(self.source, "add", ".")
        self.git(self.source, "commit", "-q", "-m", f"test: version {value}")

    def publish(self):
        self.git(self.source, "push", "-q", "--tags", "origin", "main")

    def install(self, version=None, **extra):
        env = {**self.env, **extra}
        if version is not None:
            env["ROKE_VERSION"] = version
        return subprocess.run(
            ["bash"],
            input=(REPO / "install.sh").read_text(),
            cwd=self.home,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def roke(self, *args, **extra):
        return subprocess.run(
            [str(self.installed / "bin" / "roke"), *args],
            cwd=self.home,
            env={**self.env, **extra},
            capture_output=True,
            text=True,
            timeout=60,
        )
