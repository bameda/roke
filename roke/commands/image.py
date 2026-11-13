"""roke image: the box images on this machine, and removing the ones no
project needs.

A box image's tag is a hash of roke's recipe and of a project's build
settings (roke/images.py). An image is needed when some registered project
would build that tag today; after a roke update or a change of build
settings, the old tags are left behind.
"""

from pathlib import Path

from roke import docker
from roke import project as registry
from roke.paths import config_dir
from roke.ui import Fail, die, info
from roke.workspace import Workspace


def _used(req) -> tuple[dict[str, list[str]], list[str]]:
    """Which registered projects use each image tag, and the projects whose
    image could not be worked out, as "ID: reason"."""
    config = config_dir()
    if not config.is_dir():
        die(f"configuration directory not found: {config} (create it with: roke init)")
    used: dict[str, list[str]] = {}
    problems: list[str] = []
    for name, entry in sorted(registry.registered(config.resolve()).items()):
        try:
            ws = Workspace(req).open(guards=False, registered_id=name)
            ws.load_settings()
            tag = ws.box_image()
        except Fail as exc:
            problems.append(f"{name}: {exc}")
            continue
        gone = "" if Path(entry["path"]).is_dir() else " (directory missing)"
        used.setdefault(tag, []).append(name + gone)
    return used, problems


def show(req) -> None:
    docker.require_docker(compose=False)
    used, problems = _used(req)
    images = docker.box_images()
    if not images:
        print("No box images on this machine. roke build creates them.")
        return
    width = max(len(image["tag"]) for image in images)
    print("Box images on this machine:")
    unused = 0
    for image in sorted(images, key=lambda i: i["tag"]):
        users = used.get(image["tag"])
        if users:
            status = "used by " + ", ".join(users)
        elif image["tag"] == "roke:latest":
            status = "unused (built by a roke before images per configuration)"
            unused += 1
        else:
            status = "unused"
            unused += 1
        print(f"  {image['tag']:<{width}}  {image['size']:>9}  {image['created']:<16}  {status}")
    print()
    if problems:
        print("Could not work out the image of these projects, so no image is called unused:")
        print("\n".join(f"  {problem}" for problem in problems))
        print("Fix them, or forget them with roke project rm ID.")
    elif unused:
        print(f"{unused} unused: roke image prune removes them")
    else:
        print("Every image is used by a project.")
    if any("(directory missing)" in u for users in used.values() for u in users):
        print("A project whose directory is gone keeps its image until roke project rm ID.")


def prune(req) -> None:
    docker.require_docker(compose=False)
    used, problems = _used(req)
    if problems:
        die(
            "cannot tell which images are needed: "
            + "; ".join(problems)
            + " (fix them, or forget them with roke project rm ID)"
        )
    removed = kept = 0
    for image in docker.box_images():
        if image["tag"] in used:
            continue
        reason = docker.remove_image(image["tag"])
        if reason:
            info(f"kept {image['tag']}: {reason}")
            kept += 1
        else:
            info(f"removed {image['tag']} ({image['size']})")
            removed += 1
    if not removed and not kept:
        info("no unused box images")
    elif kept:
        info(f"{removed} removed; {kept} kept, because a container still uses them")
