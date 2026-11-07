import stat
import subprocess


def test_init_creates_the_configuration(bare_env):
    r = bare_env.roke("init")
    assert r.code == 0, r.text
    c = bare_env.config
    for f in (
        "roke.env",
        "secrets.env",
        "AGENTS.md",
        ".gitignore",
        "README.md",
        "projects/README.md",
        "agents/claude/README.md",
        "agents/codex/README.md",
        "agents/opencode/opencode.jsonc",
    ):
        assert (c / f).is_file(), f
    assert stat.S_IMODE((c / "secrets.env").stat().st_mode) == 0o600


def test_init_never_overwrites(env):
    (env.config / "roke.env").write_text("MINE=1\n")
    r = env.roke("init")
    assert r.code == 0
    assert "nothing to do" in r.out
    assert (env.config / "roke.env").read_text() == "MINE=1\n"


def test_init_clones_a_configuration_repository(bare_env, tmp_path):
    repo = tmp_path / "cfg"
    repo.mkdir()
    (repo / "roke.env").write_text("ROKE_AGENT=codex\n")
    git = ["git", "-C", str(repo)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [*git, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "cfg"], check=True
    )
    r = bare_env.roke("init", str(repo))
    assert r.code == 0, r.text
    assert (bare_env.config / "roke.env").read_text() == "ROKE_AGENT=codex\n"
    assert (bare_env.config / "secrets.env").is_file()


def test_init_refuses_to_clone_over_a_configuration(env, tmp_path):
    r = env.roke("init", str(tmp_path / "whatever"))
    assert r.code != 0
    assert "already exists" in r.err


def test_commands_need_a_configuration(bare_env):
    bare_env.project()
    r = bare_env.roke(cwd=bare_env.src / "shop")
    assert r.code != 0
    assert "roke init" in r.err
