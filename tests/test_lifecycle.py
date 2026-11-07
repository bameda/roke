from helpers import compose_files


def test_build_only_builds(env):
    shop = env.project()
    r = env.roke("build", cwd=shop)
    assert r.code == 0
    assert "--pull" in r.last("build")["args"] and "--no-cache" not in r.last("build")["args"]
    assert not r.compose_calls("run")
    assert "--no-cache" in env.roke("build", "--no-cache", cwd=shop).last("build")["args"]


def test_down_and_purge_load_every_service(env):
    shop = env.project()
    r = env.roke("down", cwd=shop)
    call = r.last("down")
    assert "--volumes" not in call["args"]
    assert len([f for f in compose_files(call) if "/services/" in f]) > 10
    assert "--volumes" in env.roke("purge", cwd=shop).last("down")["args"]


def test_down_all(env):
    r = env.roke("down", "--all", cwd=env.home, env={"FAKE_COMPOSE_LS": "roke-a-1 roke-b-2"})
    assert r.code == 0
    downs = r.compose_calls("down")
    assert [c["args"][c["args"].index("-p") + 1] for c in downs] == ["roke-a-1", "roke-b-2"]
    r = env.roke("down", "--all", cwd=env.home)
    assert "no roke project is running" in r.text


def test_settings(env):
    shop = env.project()
    env.write_project_env('ROKE_SERVICES=postgres\nROKE_PORTS="5173"\n')
    out = env.roke("settings", cwd=shop).out
    for part in (
        f"Project   {shop}",
        "Agent     claude (default agent, roke.env)",
        "Network   restricted (built-in default): ",
        "destinations allowed (roke network)",
        "Services  postgres ",
        "Ports     5173",
        "Serena    off",
        ".git      read-only",
    ):
        assert part in out
    assert "github.com" not in out  # the list is in roke network
