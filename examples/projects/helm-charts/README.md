# Example: Helm charts

For a repository of Helm charts. The agent writes and refactors the charts,
validates them statically, **installs them against a real Kubernetes API**
(simulated by `kwok`) and pushes them to a local OCI registry. Testing on a
real cluster stays on your host, with kind or k3d.

## What it sets up

- **`project.env`**: the `kwok` and `registry` services.
- **`AGENTS.md`**: the validation steps the agent must follow, and what not
  to expect from a simulated cluster.

## In the project

Add a `mise.toml` with the tools, so they are installed in the box:

```toml
[tools]
helm = "latest"
kubectl = "latest"
kubeconform = "latest"
helm-docs = "latest"
"aqua:helm/chart-testing" = "latest"
yamllint = "latest"
"pipx:yamale" = "latest"
```

`chart-testing` (`ct lint`) needs `yamllint` and `yamale`, hence the last
two. For unit tests, install the
[helm-unittest](https://github.com/helm-unittest/helm-unittest) plugin as
its README explains; plugins are kept in the project's home volume.

## Check it

From `roke shell`, for a chart in `charts/mychart`:

```bash
helm lint charts/mychart
helm template demo charts/mychart | kubeconform -strict -summary
ct lint --charts charts/mychart
helm install demo charts/mychart -n demo --create-namespace
kubectl get all -n demo
helm package charts/mychart && helm push mychart-*.tgz "oci://$OCI_REGISTRY/charts" --plain-http
```

See [kwok](../../../catalog/services/kwok/README.md) for what a simulated cluster
can and cannot do.
