# Konflux Configuration as Code (CAC)

This directory contains declarative configuration for managing Konflux
applications, components, pipelines, and release plans using a
GitOps/Configuration as Code approach.

> **Architecture Decision**: This implementation is based on TAS-ADR-00008,
> which outlines the rationale, goals, and decisions for adopting
> Configuration as Code for Konflux infrastructure management.

## Table of Contents

- [Overview](#overview)
- [First-Time Deployment](#first-time-deployment)
- [Day-to-Day Usage](#day-to-day-usage)
- [Pull Request Workflow](#pull-request-workflow)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Customization](#customization)
- [Scope and Boundaries](#scope-and-boundaries)
- [Contributing](#contributing)

## Overview

This repository implements Configuration as Code (CaC) for managing
all Konflux infrastructure resources in a single Git repository,
replacing fragmented management (manual UI + scattered repos) with
a unified, automated approach.

**Key Benefits**: Full version control and audit trail, mandatory
peer review, automated deployment, eliminated configuration drift,
easy rollback, and reproducible multi-environment deployments.

See the [Architecture](#architecture) section for detailed component
flow and [Scope and Boundaries](#scope-and-boundaries) for a complete
list of managed resources.

## First-Time Deployment

**Prerequisites**: Ensure you have `oc`, `kustomize`, and `git`
installed, and access to the Konflux cluster with admin permissions in
your target namespace.

### Step 1: Verify Access

```bash
# Set your target namespace
export NAMESPACE=rhtas-tenant  # or rhtas-dev-tenant for dev

# Verify cluster access
oc whoami --show-console

# Check namespace permissions
oc auth can-i create application -n $NAMESPACE
oc auth can-i create component -n $NAMESPACE
```

### Step 2: Preview Configuration

Preview what will be deployed to production:

```bash
cd konflux-configs
kustomize build overlay/prod
```

### Step 3: Initial Bootstrap (Manual)

For first-time setup, manually apply the configuration:

```bash
# For production
oc apply -k overlay/prod

# For development
oc apply -k overlay/dev
```

Verify deployment:

```bash
# Check applications
oc get applications -n $NAMESPACE

# Check components
oc get components -n $NAMESPACE

# Check service accounts
oc get sa -n $NAMESPACE konflux-configuration-as-code-deployer
```

### Step 4: Upgrade to Custom Build Pipeline

After the initial bootstrap, Konflux automatically detects the custom
build pipeline definitions in `.tekton/` directory and generates a
pull request to upgrade the `configuration-as-code` component from
the default build pipeline to the custom pipelines.

**What happens**:
- Konflux creates an automated PR titled "Red Hat Konflux update
  configuration-as-code"
- The PR updates the component to use:
  - `.tekton/configuration-as-code-pull-request.yaml` for PR builds
  - `.tekton/configuration-as-code-push.yaml` for main branch builds

**Action required**: Close the automated PR without merging. This
repository already contains the correct custom pipeline definitions in
`.tekton/`. The automated PR is Konflux's way of requesting permission
to upgrade from default to custom build pipelines. Closing the PR
signals approval and allows Konflux to complete the upgrade
automatically.

**Verify the upgrade**:
```bash
# Check that custom pipelines are being used
oc get pipelineruns -n $NAMESPACE \
  -l appstudio.openshift.io/component=configuration-as-code

# You should see PipelineRuns using docker-build-oci-ta pipeline
```

## Day-to-Day Usage

### Making Configuration Changes

**Important**: All changes must go through the Pull Request workflow.
Direct pushes to `main` should be avoided except for emergencies.

1. **Create a Feature Branch**:
   ```bash
   # Create and checkout a new branch
   git checkout -b feat/update-component-config
   ```

2. **Edit Kustomize Files** (see [Directory Structure](#directory-structure)
   for file organization):
   ```bash
   # Edit base configurations
   vim konflux-configs/base/application/konflux/base/component.yaml

   # Or edit environment overlays
   vim konflux-configs/overlay/prod/kustomization.yaml
   ```

3. **Preview Changes Locally**:
   ```bash
   # See what will be deployed
   kustomize build overlay/prod | less

   # Validate YAML syntax
   kustomize build overlay/prod | yq eval '.' -
   ```

4. **Commit and Push**:
   ```bash
   git add konflux-configs/
   git commit -m "feat: update component configuration"
   git push origin feat/update-component-config
   ```

5. **Open Pull Request**:
   - Go to GitHub and create a Pull Request
   - Follow the [Pull Request Workflow](#pull-request-workflow) for
     validation and review process

## Pull Request Workflow

All configuration changes require Pull Request review with automated
validation.

**Automated Validation**: PRs trigger Kustomize build tests, YAML
linting, configuration diff generation, and test image builds (no
deployment). All checks must pass before merge.

**Review Requirements**: At least one approval required. Authors
should provide clear descriptions and test locally. Reviewers should
verify security, RBAC, naming conventions, and deployment impact.

**Post-Merge**: Automated deployment starts immediately—build pipeline
runs, release pipeline deploys to cluster. See
[Architecture](#architecture) for detailed flow and troubleshooting
points.

**Rollback**: If issues occur, use `git revert <commit-hash>` and
push to main for immediate rollback, or create a revert PR for review.
Then investigate root cause.

**Emergencies**: Still create a PR for audit trail, get expedited
review, and never bypass Git workflow—even in emergencies, changes
must go through Git for auditability.

## Architecture

### Design Principles

Git as single source of truth (`main` branch = desired state), no
manual UI changes, all changes via Pull Requests with mandatory
review, automated deployment on merge, Kustomize for
environment-specific overlays (dev/prod).

### Component Flow

**1. Pull Request & Validation**
- **Trigger**: `.tekton/configuration-as-code-pull-request.yaml`  (on pull-request to
  main when `konflux-configs/***` changes)
- **Pipeline**: `docker-build-oci-ta`
- **Action**: Validates Kustomize build, runs YAML linting, builds
  test image

**2. Build on Merge to Main**
- **Trigger**: `.tekton/configuration-as-code-push.yaml` (on push to
  main when `konflux-configs/***` changes)
- **Pipeline**: `docker-build-oci-ta`
- **Component**: `configuration-as-code` in
  `base/application/konflux/base/component.yaml`
- **Build Process**:
  - Runs `oc kustomize overlay/prod` in Dockerfile builder stage
  - Packages output as `/manifests.yaml` in minimal OCI image
  - Pushes to
    `quay.io/redhat-user-workloads/rhtas-tenant/configuration-as-code:<git-sha>`

**3. Automated Release**
- **Trigger**: ReleasePlan with `auto-release: true` in
  `base/release-plan/konflux-manifests/base/releaseplan.yaml`
- **Pipeline**: `pipelines/konflux/deploy-config.yaml`
- **Service Account**: `konflux-configuration-as-code-deployer`
  (defined in `base/release-plan/konflux-manifests/base/rbac.yaml`)
- **Process**:
  - Task `extract-and-apply-manifests` extracts `/manifests.yaml`
    from built image
  - Validates manifests
  - Applies manifests to cluster using `oc apply`
- **Troubleshooting**: Check Release objects (`oc get releases`),
  review deployer service account permissions

**4. Integration Testing**
- **Trigger**: Integration test scenario in
  `base/application/konflux/base/integrationtest.yaml`
- **Pipeline**: `pipelines/konflux/integration-test.yaml`
- **Action**: Validates deployment against cluster api
- **Troubleshooting**: Check IntegrationTestScenario status and test
  pipeline logs

## Directory Structure

```
konflux-configs/
├── base/                       # Base Kustomize configurations
│   ├── application/            # Application definitions
│   │   ├── konflux/base/       # Konflux app (CAC itself)
│   │   └── pipelines/base/     # Pipelines app
│   ├── release-plan/           # Release automation
│   │   └── konflux-manifests/  # CAC deployment release plan
│   └── service-account/        # RBAC for automation
│       ├── promote-to-candidate-sa.yaml
│       └── release-sa.yaml
├── overlay/                    # Environment-specific configs
│   ├── dev/                    # Development environment
│   │   └── kustomization.yaml  # namespace: rhtas-dev-tenant
│   └── prod/                   # Production environment
│       └── kustomization.yaml  # namespace: rhtas-tenant
├── releasePlans/               # Component release plans
│   └── promoteToCandidateRPs/  # Promotion workflows
├── Dockerfile                  # Builds image with manifests
└── README.md                   # This file
```

## Customization

See [Directory Structure](#directory-structure) for file locations
referenced below.

### Using Different Namespace

Edit overlay kustomization:

```yaml
# overlay/dev/kustomization.yaml
namespace: my-custom-namespace

configMapGenerator:
  - name: registry-config
    literals:
      - registry-namespace=my-custom-namespace
      - github-org=my-github-org
```

### Adding New Applications

1. Create new directory: `base/application/myapp/base/`
2. Add standard resources:
   - `application.yaml`
   - `component.yaml`
   - `imagerepository.yaml`
   - `kustomization.yaml`
3. Include in overlay: `- ../../base/application`

### Custom Release Plans

Add custom release plans in:
```
konflux-configs/base/release-plan/my-release-plan/
```

## Scope and Boundaries

### What's Included

This Configuration as Code repository manages:

- **Applications**: Konflux Application resources that group related
  components together
- **Components**: Component definitions with build configurations,
  source repository references, and container image specifications
- **ImageRepositories**: Container registry configurations including
  image names, visibility settings, and credentials
- **EnterpriseContracts**: Policy enforcement rules for security
  compliance, CVE checks, and signature validation
- **IntegrationTestScenarios**: Test automation scenarios that run
  post-build validation
- **ReleasePlans**: Configuration deployment and component promotion
  plans with pipeline references
- **Service Accounts**: RBAC for automation (build-bot, deployers)
  with appropriate roles and permissions
- **Project Resources** (when using Konflux Projects):
  - **Project**: Top-level organizational unit for managing access
    and resources across teams
  - **ProjectDevelopmentStream**: Development stream configurations
    that define build and release workflows
  - **ProjectDevelopmentStreamTemplate**: Reusable templates for
    standardizing development streams across components

**Note**: Project resources (`Project`, `ProjectDevelopmentStream`,
`ProjectDevelopmentStreamTemplate`) are centralized in this repository
to avoid duplication across individual component repositories and
ensure consistent project configuration.

### What's Excluded

The following are explicitly NOT managed in this repository:

1. **Tekton Pipelines Definitions**: Pipeline YAML files defined
   via `pipelinesascode.tekton.dev` annotations remain in their
   respective component source code repositories. This aligns with
   Pipelines-as-Code methodology where pipelines live alongside code.

2. **Secrets**: Sensitive information (credentials, tokens, keys)
   must be managed separately using dedicated secrets management tools.
   **Never commit secrets to Git.**

## Additional Resources

- [Konflux Documentation](https://konflux-ci.dev/docs/)
- [Konflux CaC Documentation](https://konflux.pages.redhat.com/docs/users/building/configuration-as-code.html)
- [Kustomize Documentation](https://kustomize.io/)
- [Pipelines as Code Docs](https://pipelinesascode.com/)

## Contributing

All changes must follow the [Pull Request Workflow](#pull-request-workflow)
outlined above.

### Workflow Requirements

All changes to this configuration repository **must**:

1. **Follow PR Workflow**: Create a feature branch and submit a Pull
   Request. Direct pushes to `main` are discouraged.

2. **Get Peer Review**: At least one team member must review and
   approve changes before merging.

3. **Pass Automated Checks**: All validation (Kustomize build, YAML
   linting) must pass before merging.

4. **Include Context**: Use descriptive commit messages following
   [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features or resources
   - `fix:` for bug fixes or corrections
   - `chore:` for maintenance tasks
   - `docs:` for documentation updates

5. **Test Locally**: Preview changes with `kustomize build` before
   pushing.