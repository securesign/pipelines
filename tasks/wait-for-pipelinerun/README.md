# wait-for-pipelinerun

Waits for a Tekton PipelineRun matching the specified selector to complete, then extracts the produced artifact reference and digest from its results.

Built as a Tekton bundle by Konflux (`pipelines/tekton-bundle-builder-oci-ta.yaml`) and pushed to
`quay.io/redhat-user-workloads/rhtas-tenant/task-wait-for-pipelinerun`.

## Usage

```yaml
taskRef:
  resolver: bundles
  params:
    - name: name
      value: wait-for-pipelinerun
    - name: bundle
      value: quay.io/redhat-user-workloads/rhtas-tenant/task-wait-for-pipelinerun:<revision>@sha256:<digest>
    - name: kind
      value: task
```

## Parameters

| Name | Description | Default |
|------|-------------|---------|
| `selector` | Label selector used to find the target PipelineRuns (e.g., "mylabel=myvalue"). | required |

## Versioning

Bump `app.kubernetes.io/version` in `wait-for-pipelinerun.yaml` and add a `CHANGELOG.md` entry for every meaningful change.
