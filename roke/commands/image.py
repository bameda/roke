"""roke image: the images roke builds on this machine, and removing the ones
no project needs.

The box's image tag is a hash of roke's recipe and of a project's build
settings (roke/images.py); a catalog service with a Dockerfile, such as
playwright, builds roke-NAME:VERSION, the version being the project's. An
image is needed when some registered project would build that tag today;
after a roke update or a change of settings, the old tags are left behind.
"""

import re
from pathlib import Path

from roke import docker
from roke import project as registry
from roke.paths import BOX_DIR, config_dir
from roke.ui import Fail, die, info
from roke.workspace import Workspace

BUILT = re.compile(r"^\s*image:\s*(roke-[^\s#]+)", re.M)
VARIABLE = re.compile(r"\$\{([A-Za-z_]\w*)(?::-([^}]*))?\}")


def catalog_builds() -> dict[str, list[str]]:
    """The image tags, as written in their compose files, of the catalog's
    services that roke builds from a Dockerfile: {"playwright": [...]}."""
    builds = {}
    for dockerfile in sorted((BOX_DIR / "catalog" / "services").glob("*/Dockerfile")):
        compose = dockerfile.parent / "compose.yaml"
        templates = BUILT.findall(compose.read_text()) if compose.is_file() else []
        if templates:
            builds[dockerfile.parent.name] = templates
    return builds


def _expand(template: str, env: dict[str, str]) -> str:
    """${VAR:-default} as compose reads it, with the project's settings."""
    return VARIABLE.sub(lambda m: env.get(m.group(1)) or m.group(2) or "", template)


def repositories(builds: dict[str, list[str]]) -> set[str]:
    return {"roke"} | {t.partition(":")[0] for templates in builds.values() for t in templates}


def _used(req, builds: dict[str, list[str]]) -> tuple[dict[str, list[str]], list[str]]:
    """Which registered projects use each image tag, and the projects whose
    images could not be worked out, as "ID: reason"."""
    config = config_dir()
    if not config.is_dir():
        die(f"configuration directory not found: {config} (create it with: roke init)")
    used: dict[str, list[str]] = {}
    problems: list[str] = []
    for name, entry in sorted(registry.registered(config.resolve()).items()):
        try:
            ws = Workspace(req).open(guards=False, registered_id=name)
            ws.load_settings()
            ws.select_services()
            tags = [ws.box_image()]
            for service in ws.selected:
                tags += [_expand(t, ws.env) for t in builds.get(service, [])]
        except Fail as exc:
            problems.append(f"{name}: {exc}")
            continue
        gone = "" if Path(entry["path"]).is_dir() else " (directory missing)"
        for tag in tags:
            used.setdefault(tag, []).append(name + gone)
    return used, problems


def show(req) -> None:
    docker.require_docker(compose=False)
    builds = catalog_builds()
    used, problems = _used(req, builds)
    images = docker.images(repositories(builds))
    if not images:
        print("No images built by roke on this machine. roke build creates them.")
        return
    width = max(len(image["tag"]) for image in images)
    print("Images built by roke on this machine:")
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
        print("Could not work out the images of these projects, so none is called unused:")
        print("\n".join(f"  {problem}" for problem in problems))
        print("Fix them, or forget them with roke project rm ID.")
    elif unused:
        print(f"{unused} unused: roke image prune removes them")
    else:
        print("Every image is used by a project.")
    if any("(directory missing)" in u for users in used.values() for u in users):
        print("A project whose directory is gone keeps its images until roke project rm ID.")


def prune(req) -> None:
    docker.require_docker(compose=False)
    builds = catalog_builds()
    used, problems = _used(req, builds)
    if problems:
        die(
            "cannot tell which images are needed: "
            + "; ".join(problems)
            + " (fix them, or forget them with roke project rm ID)"
        )
    removed = kept = 0
    for image in docker.images(repositories(builds)):
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
        info("no unused images")
    elif kept:
        info(f"{removed} removed; {kept} kept, because a container still uses them")
    info(
        "roke only removes the images it can tell are its own; for the rest "
        "(base images, dangling images, the build cache) see docker image prune "
        "and docker builder prune"
    )
