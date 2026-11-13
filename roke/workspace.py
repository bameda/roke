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

import json
import os
import sys
from pathlib import Path

from roke import mcp_permissions, settings
from roke.catalog.agents import DEFAULT_INSTALLED, Agents
from roke.catalog.mcps import Mcps
from roke.catalog.mcps import resolve as resolve_mcp
from roke.catalog.services import Services
from roke.destination import valid as valid_destination
from roke.docker import Compose, require_docker
from roke.images import box_image
from roke.paths import BOX_DIR, config_dir
from roke.ports import normalize as normalize_ports
from roke.project import by_id, check_guards, register, resolve
from roke.ui import die, info

SERENA_DASHBOARD = "24282"


class Workspace:
    def __init__(self, req):
        self.req = req

    # --- the configuration and the project ------------------------------------------
    def open(
        self,
        guards: bool = True,
        docker: bool = False,
        register_project: bool = False,
        registered_id: str = "",
    ) -> "Workspace":
        config = config_dir()
        if not config.is_dir():
            die(f"configuration directory not found: {config} (create it with: roke init)")
        self.config = config.resolve()
        if self.config == BOX_DIR or self.config.is_relative_to(BOX_DIR):
            die("the configuration directory must live outside the roke repo")
        self.global_env = self.config / "roke.env"
        self.project = (
            by_id(self.config, registered_id)
            if registered_id
            else resolve(
                self.req.project or os.getcwd(),
                self.config,
                self.req.project_id,
                lookup=not self.req.is_global,
            )
        )
        if docker:
            require_docker()
        if guards:
            check_guards(self.project.dir, Path.home().resolve(), BOX_DIR, self.config)
        if register_project:
            self.project = register(self.project, self.config, self.req.project_id)
        self.agents = Agents(BOX_DIR)
        self.services = Services(BOX_DIR, self.config / "services", self.project.services_dir)
        self.mcps = Mcps(BOX_DIR, self.config / "mcps", self.project.config / "mcps")
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
        self.global_mcps = env.pop("ROKE_MCPS", "")
        self.global_mcp_approvals = mcp_permissions.parse(env.pop(mcp_permissions.SETTING, ""))
        env = settings.load([p.env_file, p.config / "secrets.env"], env)
        self.project_allow = env.get("ROKE_NETWORK_ALLOW", "")
        self.project_mcps = env.get("ROKE_MCPS", "")
        self.project_mcp_approvals = mcp_permissions.parse(env.get(mcp_permissions.SETTING, ""))
        self.mcp_approvals = {**self.global_mcp_approvals, **self.project_mcp_approvals}
        self.env = env
        self.services_text = r.services if r.services is not None else env.get("ROKE_SERVICES", "")
        self.ports = list(r.ports) or split_list(env.get("ROKE_PORTS", ""))
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
        self.parallel_agents = split_list(env.get("ROKE_PARALLEL_AGENTS", ""))
        for name in self.parallel_agents:
            if not self.agents.exists(name):
                die(
                    f"unknown agent in ROKE_PARALLEL_AGENTS: '{name}' "
                    f"(available: {' '.join(self.agents.names())})"
                )

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
        # Services the project's MCP servers need, such as the server they talk to.
        self.mcp_services: dict[str, str] = {}
        for mcp in split_list(self.global_mcps) + split_list(self.project_mcps):
            if not self.mcps.exists(mcp):
                continue
            for name in self.mcps.definition(mcp).get("services", []):
                if not self.services.exists(name):
                    die(f"the MCP server {mcp} needs the service '{name}', which does not exist")
                if name not in self.selected:
                    self.selected.append(name)
                    self.mcp_services[name] = mcp

    # --- versions ----------------------------------------------------------------------
    def current_version(self, var: str, default: str, env=None) -> str:
        """The version a project gets when it does not pin VAR: roke.env's,
        or the service's default."""
        if env is None:
            env = settings.load([self.global_env, self.config / "secrets.env"], os.environ.copy())
        return env.get(var) or default

    def pin_versions(self, names: list[str]) -> None:
        """Pin, in the project's settings, the version of each service that
        is not pinned yet, so that updating roke does not change it."""
        p = self.project
        global_env = None
        for name in names:
            for var, default in self.services.versions(name).items():
                if settings.defines(p.env_file, var):
                    continue
                if global_env is None:
                    global_env = settings.load(
                        [self.global_env, self.config / "secrets.env"], os.environ.copy()
                    )
                value = self.current_version(var, default, global_env)
                settings.set_value(p.env_file, var, value)
                info(f"pinned for {p.name}: {var}={value}")

    # --- MCP servers -------------------------------------------------------------------
    def select_mcps(self) -> None:
        """The project's MCP servers, global ones first; those whose required
        variables are not set are left out, with a warning."""
        names: list[str] = []
        for name in split_list(self.global_mcps) + split_list(self.project_mcps):
            if not self.mcps.exists(name):
                die(f"unknown MCP server: '{name}' (see roke mcp)")
            if name not in names:
                names.append(name)
        self.selected_mcps = names
        self.resolved_mcps: dict[str, dict] = {}
        for name in names:
            definition = self.mcps.definition(name)
            missing = [v for v in definition.get("requires", []) if not self.env.get(v)]
            if missing:
                info(f"MCP {name} left out: set {', '.join(missing)} in secrets.env")
                continue
            resolved = resolve_mcp(definition, self.env)
            if resolved:
                self.resolved_mcps[name] = resolved

    def write_mcp_config(self) -> Path | None:
        """The resolved MCP servers, in a file for the box, readable only by
        you since it may hold tokens; None when there are none."""
        active = set(self.resolved_mcps) | ({"serena"} if self.serena else set())
        approvals = {name: mode for name, mode in self.mcp_approvals.items() if name in active}
        if not self.resolved_mcps and not approvals:
            return None
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / "roke"
        runtime.mkdir(parents=True, exist_ok=True)
        path = runtime / f"{self.project.compose_name}.mcp.json"
        path.touch(mode=0o600, exist_ok=True)
        path.chmod(0o600)
        data: dict = {"servers": self.resolved_mcps}
        if approvals:
            data["approvals"] = approvals
        path.write_text(json.dumps(data, indent=2) + "\n")
        return path

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
        """The allowed destinations by layer: (label, source, entries). Their
        notes, from the comments next to them, go to self.allow_notes, by
        (label, entry)."""
        self.allow_notes: dict[tuple[str, str], str] = {}

        def noted(label: str, pairs: list[tuple[str, str]], source: str) -> list[str]:
            for entry, note in pairs:
                if not valid_destination(entry):
                    die(f"invalid network destination '{entry}' in {source}")
                if note:
                    self.allow_notes[(label, entry)] = note
            return [entry for entry, _ in pairs]

        layers = [
            (
                "base",
                "docker/gateway/allow.txt",
                noted(
                    "base",
                    settings.file_noted_entries(BOX_DIR / "docker" / "gateway" / "allow.txt"),
                    "docker/gateway/allow.txt",
                ),
            )
        ]
        # The agent's destinations, and those of the agents allowed to run in
        # parallel in this project, so that the gateway is the same for all
        # of them and starting one does not recreate it under another.
        agents = network_agents(self.agent, self.parallel_agents)
        if agents:
            label = "agents" if len(agents) > 1 else "agent"
            entries: list[str] = []
            for name in agents:
                pairs = settings.file_noted_entries(self.agents.file(name, "allow.txt"))
                if len(agents) > 1:
                    pairs = [(e, f"{name}: {n}" if n else name) for e, n in pairs]
                entries += noted(label, pairs, f"catalog/agents/{name}/allow.txt")
            source = " ".join(f"catalog/agents/{name}/allow.txt" for name in agents)
            layers.append((label, source, entries))
        service_allow = []
        for name in self.selected:
            pairs = settings.file_noted_entries(self.services.file(name).parent / "allow.txt")
            service_allow += noted(
                "services",
                [(e, n or f"service {name}") for e, n in pairs],
                str(self.services.file(name).parent / "allow.txt"),
            )
        mcp_allow: list[str] = []
        for name in getattr(self, "resolved_mcps", {}):
            pairs = [(str(d), f"MCP {name}") for d in self.mcps.definition(name).get("allow", [])]
            mcp_allow += noted("mcps", pairs, str(self.mcps.file(name)))
        return layers + [
            ("services", "catalog/services/<name>/allow.txt", service_allow),
            ("mcps", "catalog/mcps/<name>/mcp.json", mcp_allow),
            (
                "global",
                "ROKE_NETWORK_ALLOW in roke.env (roke network add --global)",
                noted("global", settings.noted_entries(self.global_allow), str(self.global_env)),
            ),
            (
                "project",
                "ROKE_NETWORK_ALLOW in project.env (roke network add)",
                noted(
                    "project",
                    settings.noted_entries(self.project_allow),
                    str(self.project.env_file),
                ),
            ),
        ]

    # --- docker compose ------------------------------------------------------------------
    def prepare_compose(
        self, all_services: bool = False, publish: bool = False, create_agent_dir: bool = True
    ) -> Compose:
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
        source = "-p" if self.req.ports else "ROKE_PORTS"
        ports = normalize_ports(self.ports, source) if publish else []
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
        env["ROKE_BOX_IMAGE"] = self.box_image()
        if self.agent != "none" and create_agent_dir:
            (self.config / "agents" / self.agent).mkdir(parents=True, exist_ok=True)
        self.compose = Compose(BOX_DIR, p.compose_name, files, env)
        return self.compose

    def box_image(self) -> str:
        """The tag of the box image these settings build (see roke.images)."""
        env = dict(self.env)
        env["HOST_UID"] = env.get("ROKE_HOST_UID") or str(os.getuid())
        env["HOST_GID"] = env.get("ROKE_HOST_GID") or str(os.getgid())
        return box_image(BOX_DIR, env)

    # --- shortcuts ----------------------------------------------------------------------
    def load_all(self, required_agent: bool = False) -> None:
        """Settings, agent, services and network, in that order."""
        self.load_settings()
        self.choose_agent(required=required_agent)
        self.select_services()
        self.select_mcps()
        self.choose_network()


def split_list(text: str) -> list[str]:
    """The names in a comma-separated setting."""
    return [n.strip() for n in text.replace(" ", ",").split(",") if n.strip()]


def network_agents(agent: str, parallel: list[str]) -> list[str]:
    """The agents whose destinations the network allows: the one running and,
    when it is one of them, those allowed to run in parallel."""
    if agent == "none":
        return sorted(parallel)
    if agent in parallel:
        return sorted(parallel)
    return [agent]
