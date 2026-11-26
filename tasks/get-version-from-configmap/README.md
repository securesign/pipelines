# get-version-from-configmap

Looks up release and image versions by repository, target branch, and optional component. An image version defaults to the resolved release version.

Built as a Tekton bundle by Konflux (`pipelines/tekton-bundle-builder-oci-ta.yaml`) and pushed to
`quay.io/redhat-user-workloads/rhtas-tenant/task-get-version-from-configmap`.

## Usage

```yaml
taskRef:
  resolver: bundles
  params:
    - name: name
      value: get-version-from-configmap
    - name: bundle
      value: quay.io/redhat-user-workloads/rhtas-tenant/task-get-version-from-configmap:<revision>@sha256:<digest>
    - name: kind
      value: task
```

## Parameters

| Name | Description | Default |
|------|-------------|---------|
| `git-url` | Source repository URL | required |
| `target-branch` | Target branch for the version lookup; an empty value uses the PipelineRun annotation |  |
| `component-name` | Stable component identifier; an empty value uses the output image name |  |
| `output-image` | Output image used to derive the component name when none is supplied |  |
| `configmap-name` | ConfigMap containing the version mappings | rhtas-repo-branch-versions |
| `default-version` | Version to use when no mapping exists | 0.0.0-dev |
| `default-image-version` | Existing per-component image version used when no ConfigMap image mapping exists |  |
| `allow-missing-configmap` | Use the default version when the ConfigMap has not been deployed yet | false |

## Versioning

Bump `app.kubernetes.io/version` in `get-version-from-configmap.yaml` and add a `CHANGELOG.md` entry for every meaningful change.
