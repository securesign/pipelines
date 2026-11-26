# go-unit-test-oci-ta

Runs Go unit tests on the trusted-artifact source.

Built as a Tekton bundle by Konflux (`pipelines/tekton-bundle-builder-oci-ta.yaml`) and pushed to
`quay.io/redhat-user-workloads/rhtas-tenant/task-go-unit-test-oci-ta`.

## Usage

```yaml
taskRef:
  resolver: bundles
  params:
    - name: name
      value: go-unit-test-oci-ta
    - name: bundle
      value: quay.io/redhat-user-workloads/rhtas-tenant/task-go-unit-test-oci-ta:<revision>@sha256:<digest>
    - name: kind
      value: task
```

## Parameters

| Name | Description | Default |
|------|-------------|---------|
| `SOURCE_ARTIFACT` | The trusted artifact URI containing the application source code. |  |
| `CACHI2_ARTIFACT` | The Trusted Artifact URI pointing to the artifact with the prefetched dependencies. |  |
| `GO_TEST_COMMAND` | The go command used to run the go unit test | go test ./... |
| `GO_BASE_IMAGE` | The Go base image used to run the unit tests | registry.redhat.io/ubi9/go-toolset@sha256:23c7cb17e9c53a65f9ab01f2edf1a4e07c9a9dc2258ed63d69e06925e7cea381 |

## Versioning

Bump `app.kubernetes.io/version` in `go-unit-test-oci-ta.yaml` and add a `CHANGELOG.md` entry for every meaningful change.
