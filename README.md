# Red Hat Trusted Artifact Signer's Konflux Build Pipelines

This repository currently holds the Konflux build pipelines for Red Hat Trusted Artifact Signer. To reference these, see the example shown below:

```
pipelineRef:
  resolver: git
  params:
    - name: url
      value: 'https://github.com/securesign/pipelines.git'
    - name: revision
      value: 'main'
    - name: pathInRepo
      value: 'pipelines/<pipeline>.yaml'
```


## Task bundles

Tasks under `tasks/<name>/<name>.yaml` are built by Konflux as Tekton bundles with
`pipelines/tekton-bundle-builder-oci-ta.yaml` (one component per task) and published to
`quay.io/redhat-user-workloads/rhtas-tenant/task-<name>`. Reference them with the `bundles` resolver.
Every meaningful change requires an `app.kubernetes.io/version` label bump and a `CHANGELOG.md` entry.
