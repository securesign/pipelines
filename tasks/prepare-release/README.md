# prepare-release-branch

Manually triggered Konflux pipeline that prepares a repository for a release. From a Snapshot and a
Release it:

1. creates (or updates) the branch `release-X.Y`,
2. opens a PR into that branch (`chore: initialise <version> release`) that rewires the repository's
   `.tekton` PipelineRuns to the release stream and, for operator projects, bumps their version files.

It can also bump `main` to the next version (see [scenario 2](#2-bump-main-to-the-next-version)).
It never pushes to the target branch directly, and it never creates a branch other than
`release-X.Y` and the side branch `konflux/prepare-<branch>` used for the PR.

| Part | File |
|---|---|
| Pipeline | `pipelines/prepare-release-branch.yaml` |
| Parse task (Release + Snapshot → per-repo inputs) | `tasks/prepare-release/prepare-release-branch-parse.yaml` |
| Per-repo task (`plan`, `operator-files`, `github-token`, `apply`) | `tasks/prepare-release/prepare-release-branch.yaml` |
| GitHub App token | `stepactions/github-app-token.yaml` |
| ReleasePlan | `konflux-configs/base/application/base/prepare-release-branch/releaseplan.yaml` |

## How it works

```
Release (spec.data) + Snapshot
        │
        ▼
   parse ── derives branch, suffix, versions; groups snapshot components per repository
        │
        ▼  one run per repository (matrix)
   plan ───────────── clone, pick the commit, rewire .tekton PipelineRuns          → plan.json
   operator-files ─── operator projects only: bump version files                   → plan.json
   github-token ───── mint a GitHub App installation token
   apply ──────────── create release branch, push a signed commit, open the PR
```

**Which commit is used.** If `release-X.Y` already exists, its tip is used and the Snapshot revisions are
ignored. Otherwise the branch is created from the Snapshot commit. All components of one repository in the
Snapshot must be on the same line of history (the newest revision is used; diverged revisions fail the run).
That is how a code freeze works: build a Snapshot at the commit you want and run the Release.

**`plan` rewires** every PipelineRun in `.tekton/` whose `appstudio.openshift.io/component` label
(without the suffix) is a component of the Snapshot:

- `on-cel-expression`: `target_branch == "main"` → `target_branch == "<branch>"`
- `appstudio.openshift.io/application` and `/component` labels get the suffix (`-v1-7`)
- `serviceAccountName` gets the suffix
- the `release-version` param is set to `releaseVersion`, and the `image-version` param (when present) to `version`
- `manager-pipelinerun-selector` gets the suffix in its `application=` and `component=` values

Edits are targeted in-place text edits, so comments, quoting and line folding survive, and the result is
re-parsed and compared with the expected document. Anything unexpected (for example a CEL expression that
targets neither `main` nor the release branch) fails the run instead of guessing.

**`operator-files`** only acts on operator projects: repositories whose `PROJECT` file has a kubebuilder or
operator-sdk layout/plugin (`kubebuilder.io`, `operatorframework.io`). Every edit is optional (skipped when
the file or pattern does not exist), sets an absolute value (re-runs change nothing) and fails when a pattern
matches more than once. It uses `version`:

| What | Where |
|---|---|
| `VERSION ?= X.Y.Z` | `Makefile` |
| `ARG VERSION="X.Y.Z"` | every `Dockerfile` / `*.Dockerfile` in any directory |
| `stable-vX.Y` in `CHANNELS` | `Makefile`, Dockerfiles, `.github/workflows/*` |
| CSV `metadata.name` (`<name>.vX.Y.Z`) and `spec.version` (a suffix such as `-techpreview` is kept) | `config/manifests/bases/*.clusterserviceversion.yaml` |
| `NEW_OLM_CHANNEL` | `.github/workflows/*` |
| `IMAGE_DIGEST ?= …` → `IMAGE_TAG ?= $(VERSION)` | `Makefile`, only if still on a digest |
| `newTag` follows the version | `config/manager/kustomization.yaml`, only when patch is `0` and it already uses `newTag` (digest-pinned files are left alone) |
| `TEST_UPGRADE_CHANNEL: stable-vX.Y` | workflows that contain `NEW_OLM_CHANNEL`, only when patch is greater than `0` |

**`apply`** creates `release-X.Y` from the chosen commit when it does not exist, moves the side branch
`konflux/prepare-<branch>` to that commit, pushes one commit with the GraphQL `createCommitOnBranch`
mutation (GitHub signs it) and opens the PR into the release branch. It is idempotent: nothing to
change means no PR, and when a PR from the side branch is already open it is updated in place with
the new commit and title instead of being skipped.

## Parameters

Everything is set in the Release's `spec.data`; the Snapshot only supplies the repositories and commits.

| Field | Required | Default | Meaning |
|---|---|---|---|
| `version` | yes | | `X.Y.Z` of the project being released (a leading `v` is accepted). Branch, suffix and operator version are derived from it. |
| `releaseVersion` | no | `version` | Value of the `release-version` param in `.tekton`. Set it only when the project is versioned independently from the RHTAS product (for example policy-controller and policy-controller-operator). |
| `branch` | no | `release-X.Y` | Target branch. Use `main` to bump `main`. |
| `nameSuffix` | no | `-vX-Y` | Suffix for application/component labels and service accounts. Use `""` together with `branch: main`. |

Derived from `version: 1.7.0`:

| Value | Result | Used for |
|---|---|---|
| stream | `1.7` | branch `release-1.7`, suffix `-v1-7`, `stable-v1.7` channel |
| project version | `1.7.0` | `image-version` in `.tekton`; for operators also `Makefile`, Dockerfiles, CSV, `NEW_OLM_CHANNEL`, `newTag` |
| patch | `0` | patch `0` = new stream (`newTag`), greater than `0` = patch release (`TEST_UPGRADE_CHANNEL`) |

The patch number does **not** decide whether a branch is created; only the existence of `release-X.Y` does.
A patch version (`1.7.1`) for a branch that does not exist yet would create it from the Snapshot commit,
which is usually not what you want.

## Prerequisites

- ReleasePlan `prepare-release-branch` bound to the Application `rhtas-release` (manual release, no
  auto-release).
- The Snapshot has `spec.application: rhtas-release`, otherwise the ReleasePlan does not match it.
- Secret `github-app-bot-securesign-pr-manager` in the tenant namespace with the keys `client-id` (the GitHub
  App *Client ID*, not the numeric App ID), `installation-id` and `private-key` (full PEM).
- The GitHub App is installed on every repository involved, with Contents and Pull requests write access,
  and may push to `release-*` and `konflux/prepare-*` branches.
- The Konflux Application/Components of the release stream (`<name>-v1-7`) exist; the pipeline only edits
  labels, it does not create them.

## Triggering

Create the Release in the tenant namespace (`rhtas-tenant`, `rhtas-dev-tenant` for dev):

```bash
kubectl apply -f release.yaml
kubectl get release <name> -n rhtas-tenant -w
```

A failed Release is terminal: fix the cause, delete it and create a new one (the pipeline is idempotent, so
repeating a run is safe).

## Scenarios

### 1. New release stream (code freeze)

secure-sign-operator is aligned with the RHTAS version. Build a Snapshot of the unsuffixed components at the
commit to freeze, then:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Release
metadata:
  name: operator-prepare-release-branch-v1-7
  namespace: rhtas-tenant
spec:
  releasePlan: prepare-release-branch
  snapshot: rhtas-release-main-20261019
  data:
    version: "1.7.0"
```

Result: branch `release-1.7` is created from the Snapshot commit; the PR into it sets `1.7.0` in the version
files and `release-version`, targets `release-1.7` in the PipelineRuns and suffixes labels and service
accounts with `-v1-7`.

### 2. Bump main to the next version

After the freeze, move `main` on. Snapshot of the unsuffixed components, then:

```yaml
  data:
    version: "1.8.0"
    branch: main
    nameSuffix: ""
```

Result: PR into `main` (no branch is created, the current `main` tip is used) that sets `1.8.0` in the version
files and `release-version`; the PipelineRuns keep targeting `main` and keep their names.

### 3. Patch release on an existing stream

The Snapshot lists the components of the release branch (suffixed names, for example
`rhtas-operator-v1-7`); the Snapshot revisions are ignored because the branch tip is used.

```yaml
  data:
    version: "1.7.1"
```

Result: PR into `release-1.7` with `1.7.1` in the version files and `release-version`, plus
`TEST_UPGRADE_CHANNEL: stable-v1.7` in the OLM upgrade workflow. `config/manager/kustomization.yaml` is not
touched.

### 4. Independently versioned operator, new stream

policy-controller-operator has its own version (`main` is 1.2.0) and is released under product 1.6.0:

```yaml
  data:
    version: "1.2.0"
    releaseVersion: "1.6.0"
```

Result: branch `release-1.2` and suffix `-v1-2`; the operator files use `1.2.0`; `.tekton` `release-version` is
`1.6.0` (and `image-version`, where a PipelineRun has it, is `1.2.0`). Files that already hold the value (for example `Makefile` on `main`) are not changed.

### 5. Independently versioned operator, patch release

```yaml
  data:
    version: "1.1.2"
    releaseVersion: "1.5.2"
```

Result: PR into the existing `release-1.1` with `1.1.2` in the operator files and `1.5.2` in `.tekton`.

### 6. Non-operator repositories

Repositories without an operator `PROJECT` file only get the `.tekton` rewiring. Aligned components use the
same data as scenarios 1 to 3. Independently versioned ones (policy-controller has `image-version: 1.2.0`
next to `release-version: 1.6.0`) set both, like scenarios 4 and 5:

```yaml
  data:
    version: "1.2.0"
    releaseVersion: "1.6.0"
```

### 7. Overriding the derived names

```yaml
  data:
    version: "1.7.0"
    branch: release-1.7-hotfix
    nameSuffix: -v1-7-hotfix
```

## Troubleshooting

| Message | Cause |
|---|---|
| `unexpected on-cel-expression` | The PipelineRun targets neither `main` nor the release branch, typically because the Snapshot commit comes from another release branch. Use a Snapshot built from `main` for a new stream. |
| `no PipelineRun matches the snapshot components` | None of the `.tekton` PipelineRuns has a component label matching a Snapshot component (with the suffix removed). |
| `snapshot revisions … have diverged` | The Snapshot has several commits of one repository that are not on one line of history. |
| `cannot patch …` / `matches N times` | A file differs from what the pipeline expects; the run stops instead of guessing. |
| `Release spec.data.version must be X.Y.Z` | `version` is missing or in the old `v1.6` format. |
| Release never starts | The Snapshot is not bound to `rhtas-release` or the ReleasePlan is not applied. |
