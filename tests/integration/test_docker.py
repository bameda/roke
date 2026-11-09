"""Opt-in tests of real Docker networking and volumes, run by CI."""

import json
import os
import subprocess
import uuid
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

import pytest

REPO = Path(__file__).resolve().parents[2]
COMPOSE = Path(__file__).with_name("compose.yaml")
pytestmark = pytest.mark.skipif(
    os.environ.get("ROKE_DOCKER_TESTS") != "1",
    reason="opt in to real Docker with ROKE_DOCKER_TESTS=1",
)


def run(args, *, env=None, check=True, timeout=120):
    result = subprocess.run(args, env=env, text=True, capture_output=True, timeout=timeout)
    if check:
        assert result.returncode == 0, f"{args}\n{result.stdout}\n{result.stderr}"
    return result


class Stack:
    def __init__(self, mode):
        self.mode = mode
        self.name = f"roke-integration-{uuid.uuid4().hex[:12]}"
        self.env = {**os.environ, "ROKE_TEST_NETWORK": mode}

    def call(self, *args, **kwargs):
        return run(
            ["docker", "compose", "-f", str(COMPOSE), "-p", self.name, *args],
            env=self.env,
            **kwargs,
        )

    def probe(self, script, *args):
        return self.call("run", "--rm", "-T", "--no-deps", "box", "python", "-c", script, *args)

    def address(self, service):
        container = self.call("ps", "--quiet", service).stdout.strip()
        return run(
            [
                "docker",
                "inspect",
                "--format",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                container,
            ]
        ).stdout.strip()


@pytest.fixture(scope="module", params=["restricted", "open"])
def stack(request):
    project = Stack(request.param)
    try:
        project.call(
            "up",
            "-d",
            "--wait",
            "--wait-timeout",
            "60",
            "gateway",
            "internal",
            "allowed",
            "blocked",
        )
        yield project
    finally:
        logs = project.call("logs", "--no-color", check=False)
        print(logs.stdout, logs.stderr)
        project.call("down", "--volumes", "--remove-orphans")


def test_internal_service_is_reachable(stack):
    stack.probe(
        "import urllib.request; "
        "assert urllib.request.urlopen('http://internal:8080', timeout=3).status == 200"
    )


def test_allowed_domain_and_port(stack):
    stack.probe(
        "import urllib.request; "
        "assert urllib.request.urlopen('http://allowed.roke.test:8080', timeout=3).status == 200"
    )


def test_external_dns_policy(stack):
    script = """
import socket, sys
restricted = sys.argv[1] == 'restricted'
try:
    socket.gethostbyname('blocked.roke.test')
except socket.gaierror:
    assert restricted
else:
    assert not restricted, 'blocked domain resolved'
"""
    stack.probe(script, stack.mode)


def test_direct_ip_policy(stack):
    script = """
import socket, sys
restricted = sys.argv[1] == 'restricted'
try:
    connection = socket.create_connection((sys.argv[2], 8080), timeout=3)
except OSError:
    assert restricted
else:
    connection.close()
    assert not restricted, 'blocked IP was reachable'
"""
    stack.probe(script, stack.mode, stack.address("blocked"))


def test_allowed_domain_does_not_allow_other_ports(stack):
    script = """
import socket, sys
try:
    connection = socket.create_connection(('allowed.roke.test', 8081), timeout=3)
except OSError:
    assert sys.argv[1] == 'restricted'
else:
    connection.close()
    assert sys.argv[1] == 'open', 'port restriction was bypassed'
"""
    stack.probe(script, stack.mode)


def test_alternative_dns_server_cannot_bypass_policy(stack):
    # Send a DNS request explicitly to Docker's resolver. The gateway must
    # redirect it to dnsmasq, rather than let the box bypass its filter.
    script = """
import socket, struct, sys
name = b''.join(bytes([len(part)]) + part.encode() for part in 'blocked.roke.test'.split('.'))
packet = struct.pack('!6H', 42, 0x100, 1, 0, 0, 0) + name + b'\\0' + struct.pack('!2H', 1, 1)
for resolver in ('127.0.0.11', sys.argv[2]):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)
        sock.sendto(packet, (resolver, 53))
        response = sock.recv(4096)
    assert struct.unpack('!H', response[:2])[0] == 42
    assert response[3] & 15 == (3 if sys.argv[1] == 'restricted' else 0)
"""
    stack.probe(script, stack.mode, stack.address("blocked"))


def test_services_have_no_external_route_in_either_mode(stack):
    script = """
import socket, sys
try:
    connection = socket.create_connection((sys.argv[1], 8080), timeout=3)
except OSError:
    pass
else:
    connection.close()
    raise AssertionError('internal service reached the external network')
"""
    stack.call("exec", "-T", "internal", "python", "-c", script, stack.address("allowed"))


def test_service_ui_is_forwarded_on_host_loopback(stack):
    address = stack.call("port", "gateway", "18080").stdout.strip()
    assert address.startswith("127.0.0.1:")
    with build_opener(ProxyHandler({})).open(f"http://{address}", timeout=3) as response:
        assert response.status == 200


def test_box_has_no_capabilities(stack):
    stack.probe(
        "from pathlib import Path; "
        "status = Path('/proc/self/status').read_text(); "
        "assert int(status.split('CapEff:')[1].split()[0], 16) == 0"
    )


def test_moving_project_preserves_home_volume(tmp_path):
    # Use the real launcher and base Compose, replacing only the agent image
    # and entrypoint with a tiny Python client. No provider login is required.
    images = json.loads(Stack("restricted").call("config", "--format", "json").stdout)["services"]
    config, code = tmp_path / "config", tmp_path / "shop"
    code.mkdir()
    own = config / "projects" / "shop"
    own.mkdir(parents=True)
    (config / "roke.env").write_text("ROKE_AGENT=claude\n")
    override = own / "compose.yaml"
    override.write_text(
        json.dumps(
            {
                "services": {
                    "box": {"image": images["box"]["image"], "entrypoint": []},
                    "gateway": {"image": images["gateway"]["image"]},
                }
            }
        )
    )
    env = {key: value for key, value in os.environ.items() if not key.startswith("ROKE_")}
    env["ROKE_CONFIG_DIR"] = str(config)
    launcher = [str(REPO / "bin" / "roke")]
    try:
        run(
            [
                *launcher,
                "exec",
                "-C",
                str(code),
                "python",
                "-c",
                "from pathlib import Path; Path('/home/dev/proof').write_text('saved')",
            ],
            env=env,
        )
        registry = config / ".local" / "projects.json"
        before = json.loads(registry.read_text())["shop"]["compose_name"]
        run([*launcher, "down", "-C", str(code)], env=env)
        moved = tmp_path / "renamed"
        code.rename(moved)
        code = moved
        run(
            [
                *launcher,
                "exec",
                "--id",
                "shop",
                "-C",
                str(code),
                "python",
                "-c",
                "from pathlib import Path; assert Path('/home/dev/proof').read_text() == 'saved'",
            ],
            env=env,
        )
        assert json.loads(registry.read_text())["shop"]["compose_name"] == before
    finally:
        registry = config / ".local" / "projects.json"
        if registry.exists():
            name = json.loads(registry.read_text())["shop"]["compose_name"]
            cleanup_env = {
                **env,
                "PROJECT_DIR": str(code),
                "ROKE_PROJECT_CONFIG": str(own),
                "ROKE_AGENT": "claude",
            }
            command = [
                "docker",
                "compose",
                "-p",
                name,
                "-f",
                str(REPO / "compose.yaml"),
                "-f",
                str(override),
            ]
            logs = run([*command, "logs", "--no-color"], env=cleanup_env, check=False)
            print(logs.stdout, logs.stderr)
            run([*command, "down", "--volumes", "--remove-orphans"], env=cleanup_env)
