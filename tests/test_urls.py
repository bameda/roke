"""Port discovery compares actual Docker bindings with the next start's settings."""

import json

import pytest


def config(port="18025", target="mailpit:8025"):
    return {
        "services": {
            "gateway": {
                "environment": {"ROKE_FORWARD_MAILPIT": f"48025 {target}"},
                "ports": [
                    {"host_ip": "127.0.0.1", "published": "3000", "target": 3000},
                    {"host_ip": "127.0.0.1", "published": port, "target": 48025},
                ],
            }
        }
    }


def running(port="18025", target="mailpit:8025"):
    return {
        "FAKE_RUNNING_HASHES": "gateway=h1",
        "FAKE_CONTAINER_ENVS": json.dumps(
            {"id-gateway": [f"ROKE_FORWARD_MAILPIT=48025 {target}", "SECRET=never-print-this"]}
        ),
        "FAKE_PORT_BINDINGS": json.dumps(
            {
                "id-gateway": {
                    "3000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "3000"}],
                    "48025/tcp": [{"HostIp": "127.0.0.1", "HostPort": port}],
                    "9999/tcp": None,
                }
            }
        ),
    }


def test_stopped_project_shows_configured_ports_without_inspection(env):
    result = env.roke("urls", cwd=env.project(), env={"FAKE_CONFIG_JSON": json.dumps(config())})
    assert result.code == 0, result.text
    assert "Configured ports (project stopped)" in result.out
    assert "http://127.0.0.1:3000 → box:3000 (tcp, local only)" in result.out
    assert "http://127.0.0.1:18025 → mailpit:8025 (tcp, local only)" in result.out
    assert "Published ports (running containers)" not in result.out
    assert not any(call["args"][0] == "inspect" for call in result.calls)


def test_running_project_shows_actual_ports_without_repeating_matching_settings(env):
    result = env.roke(
        "urls", cwd=env.project(), env={"FAKE_CONFIG_JSON": json.dumps(config()), **running()}
    )
    assert result.code == 0, result.text
    assert "Published ports (running containers)" in result.out
    assert "http://127.0.0.1:18025 → mailpit:8025 (tcp, local only)" in result.out
    assert "Configured ports" not in result.out
    assert "9999" not in result.out
    assert "never-print-this" not in result.text


def test_running_project_keeps_actual_ports_and_forward_targets_when_settings_change(env):
    result = env.roke(
        "urls",
        cwd=env.project(),
        env={"FAKE_CONFIG_JSON": json.dumps(config()), **running("8025", "mailpit:8026")},
    )
    assert result.code == 0, result.text
    actual, configured = result.out.split("Configured ports (next start)")
    assert "http://127.0.0.1:8025 → mailpit:8026" in actual
    assert "18025" not in actual
    assert "http://127.0.0.1:18025 → mailpit:8025" in configured
    assert "Settings differ" in configured


def test_urls_includes_custom_containers_protocols_and_binding_addresses(env):
    result = env.roke(
        "urls",
        cwd=env.project(),
        env={
            "FAKE_RUNNING_HASHES": "custom=h1",
            "FAKE_PORT_BINDINGS": json.dumps(
                {
                    "id-custom": {
                        "53/udp": [{"HostIp": "0.0.0.0", "HostPort": "1053"}],
                        "8000/tcp": [
                            {"HostIp": "::1", "HostPort": "8001"},
                            {"HostIp": "192.168.1.2", "HostPort": "8002"},
                            {"HostIp": "::", "HostPort": "8003"},
                        ],
                    }
                }
            ),
        },
    )
    assert result.code == 0, result.text
    assert "udp://127.0.0.1:1053 → custom:53 (udp, network access, bind 0.0.0.0)" in result.out
    assert "tcp://[::1]:8001 → custom:8000 (tcp, local only)" in result.out
    assert "tcp://192.168.1.2:8002 → custom:8000 (tcp, network access)" in result.out
    assert "tcp://[::1]:8003 → custom:8000 (tcp, network access, bind ::)" in result.out


def test_running_project_with_no_bindings_does_not_claim_configured_ports_are_published(env):
    result = env.roke(
        "urls",
        cwd=env.project(),
        env={
            **running(),
            "FAKE_CONFIG_JSON": json.dumps(config()),
            "FAKE_PORT_BINDINGS": "{}",
        },
    )
    assert result.code == 0, result.text
    actual, configured = result.out.split("Configured ports (next start)")
    assert "Published ports (running containers)\n  none" in actual
    assert "http://" not in actual
    assert "http://127.0.0.1:18025" in configured


@pytest.mark.parametrize(
    "failure",
    [
        {"FAKE_DOCKER_FAIL": "ps"},
        {"FAKE_DOCKER_FAIL": "inspect"},
        {"FAKE_BAD_INSPECT": "1"},
        {"FAKE_PORT_BINDINGS": '{"id-gateway": []}'},
        {"FAKE_PORT_BINDINGS": '{"id-gateway": {"80/tcp": [{"HostIp": 1, "HostPort": "80"}]}}'},
    ],
)
def test_urls_does_not_report_failed_inspection_as_no_published_ports(env, failure):
    result = env.roke("urls", cwd=env.project(), env={**running(), **failure})
    assert result.code != 0
    assert "container" in result.err
    assert "Traceback" not in result.err
    assert "Published ports" not in result.out
