"""The commands, grouped like `roke help`: one module per group."""

from roke.commands import agent, box, network, service, setup

HANDLERS = {
    ("run", ""): box.run,
    ("continue", ""): box.run,
    ("shell", ""): box.run,
    ("exec", ""): box.run,
    ("urls", ""): box.urls,
    ("settings", ""): box.settings,
    ("build", ""): box.build,
    ("down", ""): box.down,
    ("purge", ""): box.purge,
    ("agent", "list"): agent.show,
    ("agent", "use"): agent.use,
    ("agent", "reset"): agent.reset,
    ("service", "list"): service.show,
    ("service", "add"): service.change,
    ("service", "rm"): service.change,
    ("network", "list"): network.show,
    ("network", "add"): network.change,
    ("network", "rm"): network.change,
    ("network", "blocked"): network.blocked,
    ("init", ""): setup.init,
    ("update", ""): setup.update,
}


def run(req) -> int:
    return HANDLERS[(req.command, req.sub)](req) or 0
