"""roke image: which box images the registered projects use, and removing the rest."""

import pytest


def tag(env, name="shop", setting=None):
    """The box image a project builds, after registering it."""
    path = env.project(name)
    if setting:
        env.write_project_env(setting + "\n", name=name)
    return env.roke("build", cwd=path).last("build")["env"]["ROKE_BOX_IMAGE"]


def images(*tags):
    return {"FAKE_IMAGES": ",".join(tags)}


def removed(result):
    return [c["args"][1] for c in result.calls if c["args"][:1] == ["rmi"]]


def test_list_says_which_projects_use_each_image(env):
    first = tag(env, "first")
    second = tag(env, "second", 'ROKE_AGENTS="claude"')
    assert first != second
    r = env.roke("image", env=images(first, second, "roke:build-0123abcd", "roke:latest"))
    assert r.code == 0, r.text
    by_tag = {line.split()[0]: line for line in r.out.splitlines() if line.startswith("  roke:")}
    assert by_tag[first].rstrip().endswith("used by first")
    assert by_tag[second].rstrip().endswith("used by second")
    assert by_tag["roke:build-0123abcd"].rstrip().endswith("unused")
    assert "built by a roke before images per configuration" in by_tag["roke:latest"]
    assert "2 unused: roke image prune removes them" in r.out
    assert not removed(r)


def test_projects_with_the_same_build_settings_share_an_image(env):
    shared = tag(env, "first")
    assert tag(env, "second") == shared
    r = env.roke("image", env=images(shared))
    assert "used by first, second" in r.out
    assert "Every image is used by a project." in r.out


def test_no_images_and_no_projects(env):
    assert "No box images on this machine" in env.roke("image").out
    r = env.roke("image", "prune", env=images("roke:build-0123abcd"))
    assert r.code == 0 and removed(r) == ["roke:build-0123abcd"]


def test_prune_removes_only_what_no_project_uses(env):
    used = tag(env)
    r = env.roke("image", "prune", env=images(used, "roke:build-aaaa", "roke:latest"))
    assert r.code == 0, r.text
    assert sorted(removed(r)) == ["roke:build-aaaa", "roke:latest"]
    assert "removed roke:build-aaaa" in r.err and "removed roke:latest" in r.err
    assert used not in removed(r)


def test_prune_with_nothing_to_remove(env):
    used = tag(env)
    r = env.roke("image", "prune", env=images(used))
    assert r.code == 0 and "no unused box images" in r.err and not removed(r)


def test_images_a_container_uses_are_kept(env):
    r = env.roke(
        "image",
        "prune",
        env={**images("roke:build-aaaa", "roke:build-bbbb"), "FAKE_RMI_FAIL": "roke:build-aaaa"},
    )
    assert r.code == 0, r.text
    assert "kept roke:build-aaaa: conflict" in r.err and "container 0123456789ab" in r.err
    assert "removed roke:build-bbbb" in r.err
    assert "1 removed; 1 kept" in r.err


def test_a_project_whose_directory_is_gone_keeps_its_image_until_forgotten(env):
    shop = env.project()
    gone = tag(env)
    shop.rename(shop.with_name("moved"))
    r = env.roke("image", env=images(gone))
    assert "used by shop (directory missing)" in r.out
    assert "roke project rm ID" in r.out
    assert not removed(env.roke("image", "prune", env=images(gone)))
    assert env.roke("project", "rm", "shop").code == 0
    assert removed(env.roke("image", "prune", env=images(gone))) == [gone]


def test_a_build_setting_change_leaves_the_old_image_unused(env):
    old = tag(env)
    new = tag(env, setting='ROKE_AGENTS="claude"')
    assert old != new
    r = env.roke("image", "prune", env=images(old, new))
    assert removed(r) == [old]


def test_an_unreadable_project_stops_the_prune(env):
    tag(env, "good")
    tag(env, "broken")
    env.write_project_env('ROKE_SERVICES="unclosed\n', name="broken")
    r = env.roke("image", "prune", env=images("roke:build-aaaa"))
    assert r.code != 0 and "cannot tell which images are needed: broken:" in r.err
    assert not removed(r)
    r = env.roke("image", env=images("roke:build-aaaa"))
    assert r.code == 0 and "Could not work out the image of these projects" in r.out
    assert "unused: roke image prune" not in r.out


def test_other_roke_images_are_left_alone(env):
    r = env.roke("image", "prune", env=images("roke:build-aaaa", "roke:custom", "roke:v1"))
    assert removed(r) == ["roke:build-aaaa"]


@pytest.mark.parametrize(
    "args,message",
    [
        (("image", "--global"), "roke image works on this machine as a whole"),
        (("--id", "x", "image"), "roke image does not work on a project"),
        (("image", "rm"), "unknown command: roke image rm"),
        (("image", "prune", "extra"), "unexpected argument for roke image: extra"),
    ],
)
def test_invalid_arguments(env, args, message):
    r = env.roke(*args)
    assert r.code != 0 and message in r.err


def test_image_needs_configuration(bare_env):
    r = bare_env.roke("image", env=images("roke:build-aaaa"))
    assert r.code != 0 and "roke init" in r.err
