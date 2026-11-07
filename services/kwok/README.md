# Kubernetes API (`kwok`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=kwok` in `~/.config/roke/projects/<name>/project.env`, or `roke -s kwok`.

A Kubernetes API server simulated by [kwok](https://kwok.sigs.k8s.io/)
(*Kubernetes WithOut Kubelet*). The API is real, so `kubectl` and `helm`
work against it and validate what you install, but no container ever runs:
Pods are simulated. It is meant for testing Helm charts and manifests
from inside the box.

Why not a real cluster? kind and k3d need the Docker socket, and k3s needs
a privileged container. An agent with admin rights on such a cluster could
start a Pod that mounts the host's disks and escape the box. kwok needs no
privileges. Test on a real cluster from your host, with kind or k3d.

**Inside the box**

| Variable | Value |
|---|---|
| `KUBECONFIG` | `/run/roke/kwok/kubeconfig` (server `http://kwok:8080`, no auth) |

kubectl and helm are not in the image: declare them in the project's
`mise.toml` (see the [`helm-charts`](../../examples/projects/helm-charts/)
example).

**Explore it**

```bash
kubectl get namespaces
helm install demo ./chart --namespace demo --create-namespace
kubectl get all -n demo
```

Without nodes, Pods stay `Pending`. To have them reported as `Running`,
add a simulated node first:

```bash
kubectl apply -f /run/roke/kwok/fake-node.yaml
```

Do not use `helm install --wait` before adding a node: it would wait
forever. `helm test` is not meaningful either, since test Pods never run.

**Data**: not persisted. The cluster starts empty after `roke down`.

**Settings**

| Variable | Default |
|---|---|
| `KWOK_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |

Other Kubernetes versions use the same kwok version with another suffix,
for example `v0.8.0-k8s.v1.34.8`.
