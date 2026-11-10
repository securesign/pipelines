# prepare-release-stream

A manually triggered Konflux pipeline that prepares release branches and opens PRs for
component changes and central version mappings.

## Inputs

The Release supplies `spec.data`; the Snapshot supplies repositories, components and commits.
Every Snapshot repository is consumed, including `securesign/pipelines`.

| Release field | Required | Default | Use |
|---|---|---|---|
| `version` | yes | | Project version `X.Y.Z` (leading `v` accepted); derives branch, suffix and operator version. Updates central image mappings. |
| `releaseVersion` | no | `version` for derived inputs | Product version. Central release mappings change only when this field is explicitly supplied. |
| `branch` | no | `release-X.Y` | Component target branch. |
| `nameSuffix` | no | `-vX-Y` | Application/component label and service-account suffix. Use `""` with `branch: main`. |

## Steps and storage

```text
parse Release + Snapshot
  └─ prepare-release-components (matrix: every Snapshot repository)
       checkout → rewire-pipelineruns → operator-files → github-token
       → prepare-commit → signed-commit → pull-request
       └─ prepare-release-versions (once, after the matrix succeeds)
            checkout → plan-versions → github-token
            → prepare-commit → signed-commit → pull-request
```

| File | Purpose |
|---|---|
| `pipelines/prepare-release-stream.yaml` | Task ordering and repository matrix |
| `tasks/prepare-release/prepare-release-stream-parse.yaml` | Existing Release defaults and Snapshot grouping |
| `tasks/prepare-release/prepare-release-components.yaml` | Component branch and file preparation |
| `tasks/prepare-release/prepare-release-versions.yaml` | Central versions in `pipelines/main` |
| `stepactions/github-app-token.yaml` | GitHub App authentication |
| `stepactions/signed-commit.yaml` | Generic API commit creation; returns a SHA |

Each Task has its own `/var/work` `emptyDir`, containing its clone under `repos/`,
`plan.json` and `.gh-token`. The signed-commit step uses temporary API payload files. The central Task also saves the original
Release's `spec.data` as `release-data.json`. Tasks exchange parse results, not files.

Both Tasks record their planned file changes in the same format:

```json
{
  "repo": "securesign/pipelines",
  "sha": "<origin/main SHA>",
  "create": false,
  "files": [{"path": "konflux-configs/base/config/rhtas-versions.1.7.properties", "content": "<complete file>"}]
}
```

`create` requests creation of the component target branch. It is always false for central
configuration. `files: []` skips publication.

## Component changes

Checkout uses the existing target branch's tip. If the branch is missing, it uses the newest
Snapshot revision in that repository. All selected revisions must be on one line of history;
`git merge-base --is-ancestor` fails for diverged revisions.

Matching `.tekton` PipelineRuns get the target branch in their CEL expression and the suffix
in application/component labels, service accounts and manager selectors. Local `release-version`
and `image-version` parameters are neither required nor modified. Text edits preserve comments,
quoting and folding; a YAML comparison checks that only the intended fields changed.

Operator projects are identified by their kubebuilder/operator-sdk `PROJECT` file. Existing
patterns are updated; absent patterns are skipped and ambiguous matches fail.

| Operator file | Changes |
|---|---|
| `Makefile`, Dockerfiles | Project version and `stable-vX.Y` channels |
| `config/manifests/bases/*.clusterserviceversion.yaml` | CSV name/version; preserve prerelease suffix |
| `.github/workflows/*` | `NEW_OLM_CHANNEL`, channels; patch releases set `TEST_UPGRADE_CHANNEL` |
| `Makefile` | New streams (patch `0`) convert `IMAGE_DIGEST` to `IMAGE_TAG`; patches keep digest pins |
| `config/manager/kustomization.yaml` | New streams update an existing `newTag`; digest pins remain unchanged |

## Central versions

The central Task reads the properties files registered under the `rhtas-repo-branch-versions`
ConfigMap generator. For each Snapshot repository and the exact component target branch:

- Explicit `version` updates its image mapping and existing component image overrides.
- Explicit `releaseVersion` updates its release mapping and existing component release overrides.
- Absent fields leave their dimension unchanged, regardless of parsed defaults.

Existing keys stay in their current file. New keys go into `rhtas-versions.main.properties` for
`main`, otherwise `rhtas-versions.<product-X.Y>.properties` using parsed `release-version`.
A new stream file is registered once. Other repositories, branches, repo-only fallbacks and
comments are preserved.

For `policy-controller-operator`, branch `release-1.3`, `version: "1.3.0"` and
`releaseVersion: "1.7.0"`, new mappings go into `rhtas-versions.1.7.properties`:

```properties
policy-controller-operator__release-1.3=1.7.0
policy-controller-operator__release-1.3__image=1.3.0
```

## Publication

`prepare-commit` writes the planned files into the checkout, stages them and reads the current
PR branch head. `signed-commit` creates a verified commit through GitHub's REST blob/tree/commit
APIs and returns its SHA. `pull-request` then creates or updates the bot branch and opens or updates its PR.

The generic StepAction follows [securesign/actions/signed-commit](https://github.com/securesign/actions/tree/main/signed-commit).
It knows nothing about Releases, version mappings, branch creation or PRs:

| Input | Meaning |
|---|---|
| `working-directory` | Existing checkout with files staged using `git add` |
| `message` | Commit message |
| `base-ref` | Diff base and first parent; defaults to `HEAD` |
| `extra-parent` | Optional second parent SHA |
| `token-file` | GitHub App token file |

Its `commit-sha` result is empty for no changes. It preserves file modes and binary contents,
handles additions and deletions, and refuses an unverified API commit. Native tool failures stop the step.

Component PR branches are `konflux/prepare-<target-branch>`. Central PR branches are
`konflux/prepare-versions-<namespace>/<Release-name>`. On rerun, the previous PR head becomes a
second commit parent so the bot branch can advance with a normal fast-forward update. GitHub
rejects a concurrent non-fast-forward change. There are no temporary remote branches or force updates.

## Prerequisites and triggering

- Apply ReleasePlan `prepare-release-stream`, bound to Application `rhtas-release` with manual release enabled.
- The Snapshot must have `spec.application: rhtas-release`.
- Install secret `github-app-bot-securesign-pr-manager` in the tenant namespace with
  `client-id`, `installation-id` and `private-key`. The GitHub App needs Contents and Pull requests
  write access on the selected repositories and pipelines, including bot branch creation and updates.
- Create the release-stream Konflux Applications/Components first; this pipeline only rewires their labels.
- Merge PR #530's central ConfigMap generator into `pipelines/main` before running this pipeline.

**Merge and deploy the central-config PR before merging component PRs that trigger release builds.**

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Release
metadata:
  name: operator-prepare-release-1-7
  namespace: rhtas-tenant
spec:
  releasePlan: prepare-release-stream
  snapshot: <snapshot-name>
  data:
    version: "1.7.0"
    releaseVersion: "1.7.0"
```

Apply with `kubectl apply -f release.yaml`. For a patch release, use e.g. `1.7.1`; for a main
bump, add `branch: main` and `nameSuffix: ""`. Independently versioned projects set their own
`version` and the product's `releaseVersion`. A failed Release is terminal: fix the cause and
create a new Release.
