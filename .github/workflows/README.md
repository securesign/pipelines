# GitHub Workflows

This directory contains automated workflows for the pipelines repository.

## Kustomize Diff Review Workflow

### Overview

The `kustomize-diff.yaml` workflow automatically reviews pull requests that modify Konflux configuration files. It compares the generated Kustomize manifests between the PR branch and target branch, helping reviewers understand exactly what changes will be applied to the cluster.

### Triggers

The workflow runs automatically when:
- A pull request is opened, synchronized, or reopened
- The PR includes changes to files under `konflux-configs/**`

### What It Does

1. **Checks out both branches** - Gets both the PR branch (HEAD) and target branch (BASE)
2. **Builds manifests using Buildah** - Runs `buildah bud` using `konflux-configs/Dockerfile` on both branches, exactly matching the production build process
3. **Extracts manifests** - Uses `buildah mount` to directly access `/manifests.yaml` from the built images (works with scratch images)
4. **Generates diff** - Creates a unified diff showing all changes
5. **Posts PR comment** - Adds a detailed report directly to the pull request
6. **Uploads artifacts** - Saves the generated manifests and diffs for 30 days

> **Important:** This workflow uses **Buildah** (Red Hat's container building tool) and the same `Dockerfile` that Konflux uses in production to build the manifests. The workflow uses `buildah mount` to extract files, which works even with minimal scratch images. This ensures the diff reflects the actual deployment process, including any post-processing steps or future enhancements to the build process.

### Comment Features

The workflow posts a comprehensive comment that includes:

- **Build Status** - Shows if Kustomize builds succeeded or failed
- **Changes Summary** - Statistics on additions and deletions
- **Full Diff** - Expandable section with complete diff output
- **Review Checklist** - Helpful items for reviewers to verify
- **Local Testing Instructions** - Commands to reproduce the diff locally

### Example Output

When a PR is opened, you'll see a comment like this:

```markdown
## 🔍 Kustomize Configuration Diff Report

Environment: konflux-configs/overlay/prod
Base Branch: main (abc123...)
PR Branch: feat/update-component (def456...)

---

### 📊 Changes Summary

- Additions: 15 lines
- Deletions: 5 lines

<details>
<summary>View Full Diff</summary>

... diff content ...

</details>

---

### 📝 Review Checklist

- [ ] Verify namespace configurations are correct
- [ ] Check RBAC permissions and service accounts
...
```

### Understanding the Diff

The diff output uses standard unified diff format:
- Lines starting with `+` (in green) are additions in your PR
- Lines starting with `-` (in red) are deletions from the base branch
- Lines with `@@` show the line numbers being changed
- Unchanged lines provide context

### Artifacts

The workflow uploads these artifacts for debugging:
- `base-output.yaml` - Kustomize output from target branch
- `head-output.yaml` - Kustomize output from PR branch
- `diff.txt` - Complete diff file
- Error logs (if builds fail)

Access artifacts from the workflow run page in GitHub Actions.

### Permissions

The workflow requires:
- `contents: read` - To checkout repository code
- `pull-requests: write` - To post comments on PRs

### Troubleshooting

**Workflow doesn't run:**
- Ensure your PR modifies files under `konflux-configs/`
- Check that the workflow file is on the base branch

**Build fails:**
- Review the error log in the PR comment
- Test locally using the Docker build command (see Local Testing section)
- Verify all referenced files exist in `base/` and `overlay/` directories
- Check that the Konflux test image is accessible: `quay.io/konflux-ci/konflux-test:latest`

**Comment not posted:**
- Check workflow logs in GitHub Actions
- Ensure the GITHUB_TOKEN has sufficient permissions
- Verify the repository settings allow workflow comments

**Diff is truncated:**
- For very large diffs (>500 lines), only the first 500 lines are shown in the comment
- Download the full diff from workflow artifacts

### Local Testing

To test changes locally before pushing (using Buildah, same as the workflow):

```bash
# Save current branch
CURRENT_BRANCH=$(git branch --show-current)

# Build from base branch using Buildah
git checkout main
cd konflux-configs
buildah bud --build-arg ENVIRONMENT=prod -t konflux-config-base -f Dockerfile .
CONTAINER_BASE=$(buildah from konflux-config-base)
MOUNT_BASE=$(buildah mount $CONTAINER_BASE)
cp $MOUNT_BASE/manifests.yaml /tmp/base.yaml
buildah umount $CONTAINER_BASE
buildah rm $CONTAINER_BASE

# Build from your branch using Buildah
git checkout $CURRENT_BRANCH
buildah bud --build-arg ENVIRONMENT=prod -t konflux-config-head -f Dockerfile .
CONTAINER_HEAD=$(buildah from konflux-config-head)
MOUNT_HEAD=$(buildah mount $CONTAINER_HEAD)
cp $MOUNT_HEAD/manifests.yaml /tmp/head.yaml
buildah umount $CONTAINER_HEAD
buildah rm $CONTAINER_HEAD

# Compare
diff -u /tmp/base.yaml /tmp/head.yaml | less

# Or use a visual diff tool
code --diff /tmp/base.yaml /tmp/head.yaml

# Clean up
buildah rmi konflux-config-base konflux-config-head
```

> **Note:** The workflow uses `buildah mount` to extract files from scratch images. If you prefer Docker:
> ```bash
> docker build --build-arg ENVIRONMENT=prod -t konflux-config-base -f Dockerfile .
> docker create --name base-c konflux-config-base sh  # Need to specify a command for scratch images
> docker cp base-c:/manifests.yaml /tmp/base.yaml
> docker rm base-c
> ```
> However, Buildah's mount approach is more straightforward for scratch images.

### Integration with PR Workflow

This workflow complements the existing Konflux pipelines:

1. **PR opened** → This workflow generates diff for review
2. **Reviewer examines diff** → Understands cluster impact
3. **PR approved & merged** → Konflux build pipeline runs
4. **Build succeeds** → Konflux release pipeline deploys changes

### Best Practices

**For PR Authors:**
- Review the generated diff before requesting review
- Ensure changes match your expectations
- Add explanations for complex changes in PR description
- Test locally if the build fails

**For Reviewers:**
- Always check the diff comment before approving
- Verify namespace, RBAC, and resource names
- Look for unintended resource deletions
- Confirm changes align with PR description

### Customization

To modify the workflow:

1. **Change target overlay:**
   ```yaml
   # In kustomize-diff.yaml, modify:
   kustomize build overlay/dev  # Instead of overlay/prod
   ```

2. **Add additional checks:**
   ```yaml
   # Add new steps after "Generate Diff Report"
   - name: Custom Validation
     run: |
       # Your validation logic
   ```

3. **Change diff format:**
   ```yaml
   # Modify the diff command in "Generate Diff Report"
   diff -y /tmp/base-output.yaml /tmp/head-output.yaml  # Side-by-side
   ```

4. **Add more overlays:**
   - Duplicate the build and diff steps
   - Run for both `overlay/prod` and `overlay/dev`
   - Combine results in the PR comment

### Related Documentation

- [Konflux Configuration as Code](../konflux-configs/README.md)
- [Kustomize Documentation](https://kustomize.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pull Request Workflow](../konflux-configs/README.md#pull-request-workflow)

