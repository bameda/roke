"""roke itself: init and update."""

import shutil
import subprocess

from roke import releases
from roke.paths import BOX_DIR, config_dir
from roke.ui import die


def init(req) -> None:
    """Create the configuration directory from examples/config, cloning the
    given repository first; never overwrite existing files."""
    target, repo = config_dir(), (req.values[0] if req.values else "")
    if repo:
        if target.exists():
            die(f"{target} already exists; remove it or move it away to clone {repo}")
        if not shutil.which("git"):
            die("git is not installed")
        if subprocess.run(["git", "clone", repo, str(target)]).returncode != 0:
            die(f"could not clone {repo}")
    target.mkdir(parents=True, exist_ok=True)
    examples = BOX_DIR / "examples" / "config"
    created = False
    for src in sorted(p for p in examples.rglob("*") if p.is_file()):
        rel = str(src.relative_to(examples)).removesuffix(".example")
        dest = target / rel
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            print(f"  created {rel}")
            created = True
    secrets = target / "secrets.env"
    if secrets.exists():
        secrets.chmod(0o600)
    if not created:
        print("  nothing to do: every file already exists")
    print(f"Configuration directory: {target}")
    if not (target / ".git").is_dir():
        print(f'Tip: make it a private git repo: git -C "{target}" init')


def update(req) -> int:
    return releases.update(req.channel)
