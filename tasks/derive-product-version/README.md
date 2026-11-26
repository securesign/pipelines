# derive-product-version

Derives product and image metadata versions from release/image inputs.

Built as a Tekton bundle by Konflux (`pipelines/tekton-bundle-builder-oci-ta.yaml`) and pushed to
`quay.io/redhat-user-workloads/rhtas-tenant/task-derive-product-version`.

## Usage

```yaml
taskRef:
  resolver: bundles
  params:
    - name: name
      value: derive-product-version
    - name: bundle
      value: quay.io/redhat-user-workloads/rhtas-tenant/task-derive-product-version:<revision>@sha256:<digest>
    - name: kind
      value: task
```

## Parameters

| Name | Description | Default |
|------|-------------|---------|
| `release-version` | Full release version (including Patch) | required |
| `image-version` | Optional image metadata version label. Falls back to release-version when empty. |  |

## Versioning

Bump `app.kubernetes.io/version` in `derive-product-version.yaml` and add a `CHANGELOG.md` entry for every meaningful change.
