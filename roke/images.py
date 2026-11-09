"""Image names derived from the box's recipe and build arguments."""

import hashlib
import json
from pathlib import Path

# Keep in sync with box.build.args in compose.yaml. Defaults remain in the
# Dockerfile; unset and explicitly empty arguments have different meanings.
BOX_BUILD_ARGS = (
    "HOST_UID",
    "HOST_GID",
    "ROKE_AGENTS",
    "ROKE_AGENT_VERSIONS",
    "POSTGRES_CLIENT_VERSION",
    "INSTALL_SERENA",
    "SERENA_VERSION",
)


def box_image(repo: Path, env: dict[str, str]) -> str:
    recipe = [repo / "Dockerfile", repo / "docker" / "entrypoint.sh"]
    recipe += sorted((repo / "catalog" / "agents").glob("*/install.sh"))
    contents = {
        str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in recipe
    }
    inputs = {"args": {key: env.get(key) for key in BOX_BUILD_ARGS}, "recipe": contents}
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:20]
    return f"roke:build-{digest}"
