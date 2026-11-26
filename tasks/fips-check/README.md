# fips-check

The fips-check task uses the check-payload tool to verify if an image is FIPS compliant.

Built as a Tekton bundle by Konflux (`pipelines/tekton-bundle-builder-oci-ta.yaml`) and pushed to
`quay.io/redhat-user-workloads/rhtas-tenant/task-fips-check`.

## Usage

```yaml
taskRef:
  resolver: bundles
  params:
    - name: name
      value: fips-check
    - name: bundle
      value: quay.io/redhat-user-workloads/rhtas-tenant/task-fips-check:<revision>@sha256:<digest>
    - name: kind
      value: task
```

## Parameters

| Name | Description | Default |
|------|-------------|---------|
| `image-digest` | Image digest to scan. | required |
| `image-url` | Image URL. | required |

## Versioning

Bump `app.kubernetes.io/version` in `fips-check.yaml` and add a `CHANGELOG.md` entry for every meaningful change.
