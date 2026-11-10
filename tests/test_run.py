import hashlib
import json
from pathlib import Path

import pytest
from helpers import after, compose_files, project_name


def test_compose_project_name(env):
    shop = env.project()
    digest = hashlib.sha1(str(shop.resolve()).encode()).hexdigest()[:8]
    assert project_name(env.roke(cwd=shop).last("run")) == f"roke-shop-{digest}"


def test_run_args_and_mounts(env):
    shop = env.project()
    (env.config / "projects" / "shop").mkdir(parents=True)
    (env.config / "projects" / "shop" / "AGENTS.md").write_text("# private\n")
    call = env.roke(cwd=shop).last("run")
    args = call["args"]
    assert args[args.index("run") + 1] == "--rm"
    assert "-T" in args
    assert f"{shop}/.git:{shop}/.git:ro" in args
    assert "ROKE_GIT_READONLY=1" in args
    assert any(a.endswith("/AGENTS.md:/run/roke/user-AGENTS.md:ro") for a in args)
    assert any(a.endswith("/projects/shop/AGENTS.md:/run/roke/project-AGENTS.md:ro") for a in args)
    assert after(call, "box") == []
    assert call["env"]["PROJECT_DIR"] == str(shop)
    assert call["env"]["ROKE_PROJECT_CONFIG"] == str(env.config / "projects" / "shop")


def test_git_rw_and_projects_without_git(env):
    shop = env.project()
    assert not any(".git:" in a for a in env.roke("--git-rw", cwd=shop).last("run")["args"])
    other = env.project("other", git=False)
    assert not any(".git:" in a for a in env.roke(cwd=other).last("run")["args"])


def test_continue_shell_exec(env):
    shop = env.project()
    call = env.roke("continue", cwd=shop).last("run")
    assert "ROKE_CONTINUE=1" in call["args"] and after(call, "box") == []
    assert after(env.roke("shell", cwd=shop).last("run"), "box") == ["bash"]
    call = env.roke("exec", "psql", "-c", "select 1", cwd=shop).last("run")
    assert after(call, "box") == ["psql", "-c", "select 1"]
    call = env.roke("exec", "-s", "postgres", "psql", cwd=shop).last("run")
    assert after(call, "box") == ["psql"] and call["env"]["ROKE_SERVICES"] == "postgres"


@pytest.mark.parametrize(
    ("args", "agent", "ports"),
    [(("--ui",), "opencode", "3000"), (("run", "-a", "opencode", "--ui"), "claude", "3000 4096")],
)
def test_opencode_ui_uses_project_and_publishes_on_loopback(env, args, agent, ports):
    shop = env.project()
    env.write_project_env(f'ROKE_AGENT={agent}\nROKE_SERVICES=postgres\nROKE_PORTS="{ports}"\n')

    result = env.roke(*args, cwd=shop)

    assert result.code == 0, result.text
    call = result.last("run")
    assert after(call, "box") == ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]
    assert call["env"]["ROKE_SERVICES"] == "postgres"
    assert "ROKE_GIT_READONLY=1" in call["args"]
    ports = Path(compose_files(call)[-1]).read_text()
    assert ports.count('"127.0.0.1:4096:4096"') == 1
    assert '"127.0.0.1:3000:3000"' in ports
    assert "http://127.0.0.1:4096" in result.text


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (("--ui",), "--ui is available for OpenCode"),
        (("continue", "--ui"), "select the conversation"),
        (("shell", "--ui"), "unknown option"),
    ],
)
def test_ui_rejects_unsupported_invocations(env, args, message):
    result = env.roke(*args, cwd=env.project())
    assert result.code != 0 and message in result.err
    assert not result.compose_calls("run")


def test_ui_rejects_public_port_mapping(env):
    config = {"services": {"gateway": {"ports": [{"target": 4096, "published": "9000"}]}}}
    result = env.roke(
        "-a",
        "opencode",
        "--ui",
        cwd=env.project(),
        env={"FAKE_CONFIG_JSON": json.dumps(config)},
    )
    assert result.code != 0 and "must be published on loopback only" in result.err
    assert not result.compose_calls("run")


def test_ports_are_published_by_the_gateway(env):
    shop = env.project()
    files = compose_files(env.roke("-p", "5173", "-p", "0.0.0.0:3000:3000", cwd=shop).last("run"))
    ports_file = Path(files[-1])
    assert ports_file.name.endswith(".ports.yaml")
    text = ports_file.read_text()
    assert '"127.0.0.1:5173:5173"' in text and '"0.0.0.0:3000:3000"' in text
    env.write_project_env('ROKE_PORTS="8080"\n')
    files = compose_files(env.roke(cwd=shop).last("run"))
    assert '"127.0.0.1:8080:8080"' in Path(files[-1]).read_text()


@pytest.mark.parametrize(
    "args",
    [
        ("-p", "3000 1275"),
        ("-p", "3000", "-p", "1275"),
        ("run", "-p", " 3000\t1275 "),
        ("-p", "3000 1275", "-p", "127.0.0.1:9000:8000"),
    ],
)
def test_port_lists_override_configured_ports(env, args):
    shop = env.project()
    env.write_project_env('ROKE_PORTS="8080"\n')
    files = compose_files(env.roke(*args, cwd=shop).last("run"))
    text = Path(files[-1]).read_text()
    assert '"127.0.0.1:3000:3000"' in text
    assert '"127.0.0.1:1275:1275"' in text
    assert "8080" not in text
    if "127.0.0.1:9000:8000" in args:
        assert '"127.0.0.1:9000:8000"' in text


def test_serena(env):
    shop = env.project()
    assert env.roke(cwd=shop).last("run")["env"]["ROKE_SERENA"] == "0"
    assert env.roke("--serena", cwd=shop).last("run")["env"]["ROKE_SERENA"] == "1"
    env.write_project_env("ROKE_SERENA=1\n")
    assert env.roke("--no-serena", cwd=shop).last("run")["env"]["ROKE_SERENA"] == "0"


def test_settings_files_precedence(env):
    shop = env.project()
    env.append(env.config / "roke.env", "POSTGRES_DB=global\nMAILPIT_UI_PORT=1\n")
    env.write_project_env("POSTGRES_DB=project\n")
    (env.config / "projects" / "shop" / "secrets.env").write_text("POSTGRES_DB=secret\n")
    exported = env.roke(cwd=shop).last("run")["env"]
    assert exported["POSTGRES_DB"] == "secret"
    assert exported["MAILPIT_UI_PORT"] == "1"


def test_another_project_with_C(env):
    shop = env.project()
    call = env.roke("-C", str(shop), "shell", cwd=env.home).last("run")
    assert call["env"]["PROJECT_DIR"] == str(shop)


def test_host_uid_override(env):
    env.append(env.config / "roke.env", "ROKE_HOST_UID=0\nROKE_HOST_GID=0\n")
    exported = env.roke(cwd=env.project()).last("run")["env"]
    assert exported["HOST_UID"] == "0" and exported["HOST_GID"] == "0"
