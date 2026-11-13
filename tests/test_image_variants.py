"""Projects share images when build inputs match, without overwriting other variants."""

import re

import pytest
from conftest import REPO


def image(result, verb):
    return result.last(verb)["env"]["ROKE_BOX_IMAGE"]


def test_build_and_run_select_the_same_image(env):
    shop = env.project()
    built = image(env.roke("build", cwd=shop), "build")
    assert built.startswith("roke:build-")
    assert image(env.roke(cwd=shop), "run") == built
    assert image(env.roke("build", "--no-cache", cwd=shop), "build") == built


def test_equivalent_projects_share_image_and_runtime_options_do_not_change_it(env):
    first = image(env.roke("build", cwd=env.project("first")), "build")
    second = env.project("second")
    env.write_project_env(
        'ROKE_AGENT=codex\nROKE_SERVICES=postgres\nROKE_PORTS="5173"\n', name="second"
    )
    assert image(env.roke(cwd=second), "run") == first


@pytest.mark.parametrize(
    "setting",
    [
        'ROKE_AGENTS="claude"',
        'ROKE_AGENT_VERSIONS="claude=1.2.3"',
        "ROKE_HOST_UID=1234",
        "ROKE_HOST_GID=1234",
        "POSTGRES_CLIENT_VERSION=99",
        "INSTALL_SERENA=0",
        "SERENA_VERSION=0.0.1",
    ],
)
def test_different_build_settings_select_independent_images(env, setting):
    first = env.project("first")
    original = image(env.roke("build", cwd=first), "build")
    second = env.project("second")
    env.write_project_env(setting + "\n", name="second")
    variant = image(env.roke("build", cwd=second), "build")
    assert variant != original
    assert image(env.roke("build", cwd=first), "build") == original


def test_doctor_inspects_selected_variant(env):
    shop = env.project()
    expected = image(env.roke("build", cwd=shop), "build")
    r = env.roke("doctor", cwd=shop)
    assert r.code == 0, r.text
    assert any(call["args"] == ["image", "inspect", expected] for call in r.calls)


def test_signature_covers_all_compose_box_build_arguments():
    # Contract between the recipe and the signature: adding an argument to
    # Compose without hashing it could make projects overwrite one another.
    import sys

    sys.path.insert(0, str(REPO))
    from roke.images import BOX_BUILD_ARGS

    text = (REPO / "compose.yaml").read_text().split("    build:\n      context: .\n")[1]
    args = text.split("      args:\n")[1].split("    init:")[0]
    assert set(re.findall(r"^        - ([A-Z_]+)$", args, re.M)) == set(BOX_BUILD_ARGS)


def test_recipe_changes_require_new_image_but_mounted_setup_does_not(tmp_path):
    import sys

    sys.path.insert(0, str(REPO))
    from roke.images import box_image

    recipe = [
        tmp_path / "Dockerfile",
        tmp_path / "docker" / "entrypoint.sh",
        tmp_path / "catalog" / "agents" / "fixture" / "install.sh",
        tmp_path / "catalog" / "agents" / "install-acp.sh",
    ]
    for path in recipe:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original")
    original = box_image(tmp_path, {})
    for path in recipe:
        path.write_text("changed")
        assert box_image(tmp_path, {}) != original
        path.write_text("original")
    recipe[2].with_name("setup.sh").write_text("mounted at runtime")
    assert box_image(tmp_path, {}) == original


def test_doctor_uses_explicit_compose_image_override(env, compose):
    shop = env.project()
    override = env.config / "projects" / "shop" / "compose.yaml"
    override.parent.mkdir(parents=True)
    override.write_text("services:\n  box:\n    image: custom-box:test\n")
    r = env.roke("doctor", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    assert any(call["args"] == ["image", "inspect", "custom-box:test"] for call in r.calls)
