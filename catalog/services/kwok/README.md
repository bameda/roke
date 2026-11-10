# Kubernetes API (`kwok`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add kwok`.

A Kubernetes API server simulated by [kwok](https://kwok.sigs.k8s.io/)
(*Kubernetes WithOut Kubelet*). The API is real, so `kubectl` and `helm`
work against it and validate what you install, but no container ever runs:
Pods are simulated. It is meant for testing Helm charts and manifests
from inside the box.

Test workloads on a real cluster from your host.

**Inside the box**

| Variable | Value |
|---|---|
| `KUBECONFIG` | `/run/roke/kwok/kubeconfig` (server `http://kwok:8080`, no auth) |

kubectl and helm are not in the image: declare them in the project's
`mise.toml` (see the [`helm-charts`](../../../examples/projects/helm-charts/)
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
| `KWOK_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
