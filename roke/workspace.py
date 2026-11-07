"""A Workspace: the project, your configuration and everything that follows
from them for a command (settings, agent, services, network, compose).
Each command builds one, calling the steps it needs in this order:

  open()            the configuration, the project and its guards
  load_settings()   roke.env and the project's settings (the last one wins)
  choose_agent()    the agent to run, and where that choice comes from
  select_services() the services to start
  choose_network()  the network mode and the allowed destinations
  prepare_compose() the compose files, published ports and environment
"""

import os
import sys
from pathlib import Path

from roke import settings
from roke.agents import DEFAULT_INSTALLED, Agents
from roke.docker import Compose, require_docker
from roke.paths import BOX_DIR, config_dir
from roke.project import check_guards, resolve
from roke.services import Services
from roke.ui import die

SERENA_DASHBOARD = "24282"


class Workspace:
    def __init__(self, req):
        self.req = req

    # --- the configuration and the project ------------------------------------------
    def open(self, guards: bool = True, docker: bool = False) -> "Workspace":
        config = config_dir()
        if not config.is_dir():
            die(f"configuration directory not found: {config} (create it with: roke init)")
        self.config = config.resolve()
        if self.config == BOX_DIR or self.config.is_relative_to(BOX_DIR):
            die("the configuration directory must live outside the roke repo")
        self.global_env = self.config / "roke.env"
        self.project = resolve(self.req.project or os.getcwd(), self.config)
        self.agents = Agents(BOX_DIR)
        self.services = Services(BOX_DIR, self.config / "services", self.project.services_dir)
        if docker:
            require_docker()
        if guards:
            check_guards(self.project.dir, Path.home().resolve(), BOX_DIR, self.config)
        return self

    def installed_agents(self, env=None) -> list[str]:
        """The agents in the image (ROKE_AGENTS)."""
        if env is None:
            env = settings.load([self.global_env], os.environ.copy())
        return env.get("ROKE_AGENTS", DEFAULT_INSTALLED).split()

    # --- settings ----------------------------------------------------------------------
    def load_settings(self) -> None:
        """Global settings, then the project's (the last one wins). The allowed
        destinations are the exception: the project's add to the global ones."""
        p, r = self.project, self.req
        env = settings.load([self.global_env, self.config / "secrets.env"], os.environ.copy())
        self.global_allow = env.pop("ROKE_NETWORK_ALLOW", "")
        env = settings.load([p.env_file, p.config / "secrets.env"], env)
        self.project_allow = env.get("ROKE_NETWORK_ALLOW", "")
        self.env = env
        self.services_text = r.services if r.services is not None else env.get("ROKE_SERVICES", "")
        self.ports = list(r.ports) or env.get("ROKE_PORTS", "").split()
        self.git_rw = r.git_rw or env.get("ROKE_GIT_RW", "0") == "1"
        self.serena = r.serena if r.serena is not None else env.get("ROKE_SERENA", "0") == "1"
        env["ROKE_SERENA"] = "1" if self.serena else "0"
        env.setdefault("ROKE_SERENA_DASHBOARD", "0")

    # --- the agent ---------------------------------------------------------------------
    def choose_agent(self, required: bool = False) -> None:
        """REQUIRED: the agent will run, so it must exist and be installed."""
        env, r = self.env, self.req
        installed = self.installed_agents(env)
        self.agent_source = "default agent, roke.env"
        if settings.defines(self.project.env_file, "ROKE_AGENT"):
            self.agent_source = "this project"
        if r.agent:
            self.agent_source = "--agent"
        agent = r.agent or env.get("ROKE_AGENT", "")
        if not agent:
            if len(installed) == 1:
                agent, self.agent_source = installed[0], "the only one installed"
            elif required:
                die(
                    "choose a coding agent: roke agent use NAME --global "
                    f"(installed: {' '.join(installed)})"
                )
            else:
                agent = "none"  # not needed to stop, build or inspect
        if required:
            if not self.agents.exists(agent):
                die(f"unknown agent: '{agent}' (available: {' '.join(self.agents.names())})")
            if agent not in installed:
                die(
                    f"the agent '{agent}' is not in ROKE_AGENTS ({' '.join(installed)}): "
                    "add it there and run roke build"
                )
        self.installed = installed
        self.agent = agent
        env["ROKE_AGENT"] = agent

    # --- the services ------------------------------------------------------------------
    def select_services(self) -> None:
        self.selected: list[str] = []
        for name in (s.strip() for s in self.services_text.split(",")):
            if not name:
                continue
            if not self.services.exists(name):
                print(self.services.render(self.services_text), file=sys.stderr)
                die(f"unknown service: '{name}'")
            if name not in self.selected:
                self.selected.append(name)

    # --- the network -------------------------------------------------------------------
    def choose_network(self) -> None:
        env, r = self.env, self.req
        self.network_source = "built-in default"
        if settings.defines(self.global_env, "ROKE_NETWORK"):
            self.network_source = "roke.env"
        if settings.defines(self.project.env_file, "ROKE_NETWORK"):
            self.network_source = "this project"
        if r.network:
            self.network_source = "--network"
        mode = r.network or env.get("ROKE_NETWORK", "restricted")
        if mode not in ("restricted", "open"):
            die(f"network mode must be restricted or open, not '{mode}'")
        env["ROKE_NETWORK"] = self.network = mode
        env["ROKE_NETWORK_ALLOW_ALL"] = " ".join(
            sorted({d for _, _, entries in self.allow_layers() for d in entries})
        )

    def allow_layers(self) -> list:
        """The allowed destinations by layer: (label, source, entries)."""
        layers = [
            (
                "base",
                "docker/gateway/allow.txt",
                settings.file_entries(BOX_DIR / "docker" / "gateway" / "allow.txt"),
            )
        ]
        if self.agent != "none":
            layers.append(
                (
                    "agent",
                    f"agents/{self.agent}/allow.txt",
                    settings.file_entries(self.agents.file(self.agent, "allow.txt")),
                )
            )
        service_allow = []
        for name in self.selected:
            service_allow += settings.file_entries(self.services.file(name).parent / "allow.txt")
        return layers + [
            ("services", "services/<name>/allow.txt", service_allow),
            (
                "global",
                "ROKE_NETWORK_ALLOW in roke.env (roke network add --global)",
                settings.entries(self.global_allow),
            ),
            (
                "project",
                "ROKE_NETWORK_ALLOW in project.env (roke network add)",
                settings.entries(self.project_allow),
            ),
        ]

    # --- docker compose ------------------------------------------------------------------
    def prepare_compose(self, all_services: bool = False, publish: bool = False) -> Compose:
        """ALL_SERVICES: load every service, so that down and purge know all the
        volumes. PUBLISH: publish the box's ports, through the gateway."""
        p, env = self.project, self.env
        services = self.services.names() if all_services else self.selected
        files = [BOX_DIR / "compose.yaml"] + [self.services.file(s) for s in services]
        if (p.config / "compose.yaml").is_file():
            files.append(p.config / "compose.yaml")
        self.base_files = [files[0]]

        # The box shares the gateway's network, so its ports are published on
        # the gateway, through a compose file generated for this run.
        ports = [port if ":" in port else f"127.0.0.1:{port}:{port}" for port in self.ports]
        if self.serena and env.get("ROKE_SERENA_DASHBOARD") == "1":
            port = env.get("ROKE_SERENA_DASHBOARD_PORT", SERENA_DASHBOARD)
            ports.append(f"127.0.0.1:{port}:{SERENA_DASHBOARD}")
        if ports and publish:
            runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / "roke"
            runtime.mkdir(parents=True, exist_ok=True)
            ports_file = runtime / f"{p.compose_name}.ports.yaml"
            ports_file.write_text(
                "services:\n  gateway:\n    ports:\n" + "".join(f'      - "{x}"\n' for x in ports)
            )
            files.append(ports_file)
            self.base_files.append(ports_file)

        env.update(
            {
                "PROJECT_DIR": str(p.dir),
                "ROKE_CONFIG_DIR": str(self.config),
                "ROKE_PROJECT_CONFIG": str(p.config),
                "ROKE_SERVICES": ",".join(self.selected),
                "HOST_UID": env.get("ROKE_HOST_UID") or str(os.getuid()),
                "HOST_GID": env.get("ROKE_HOST_GID") or str(os.getgid()),
            }
        )
        if self.agent != "none":
            (self.config / "agents" / self.agent).mkdir(parents=True, exist_ok=True)
        self.compose = Compose(BOX_DIR, p.compose_name, files, env)
        return self.compose

    # --- shortcuts ----------------------------------------------------------------------
    def load_all(self, required_agent: bool = False) -> None:
        """Settings, agent, services and network, in that order."""
        self.load_settings()
        self.choose_agent(required=required_agent)
        self.select_services()
        self.choose_network()
