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

1. **Installs OpenShift CLI** - Uses [redhat-actions/openshift-tools-installer](https://github.com/redhat-actions/openshift-tools-installer) to install `oc` with automatic caching
2. **Checks out both branches** - Gets both the PR branch (HEAD) and target branch (BASE)
3. **Builds manifests using Buildah** - Runs `buildah bud` using `konflux-configs/Dockerfile` on both branches, exactly matching the production build process
4. **Extracts manifests** - Uses `oc image extract` to get `/manifests.yaml` from locally built images (same method as production)
5. **Generates diff** - Creates a unified diff showing all changes
6. **Posts PR comment** - Adds a detailed report directly to the pull request
7. **Uploads artifacts** - Saves the generated manifests and diffs for 30 days

> **Important:** This workflow uses **Buildah** (Red Hat's container building tool) and the same `Dockerfile` that Konflux uses in production to build the manifests. The workflow extracts files using **`oc image extract`**, which is the exact same command used in the production `extract-and-apply-manifests` task. The `oc` tool can extract files from images in local containers-storage without needing to push them to a registry. This ensures the diff reflects the actual deployment process, including any post-processing steps or future enhancements to the build process.

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
- Test locally using the same commands as the workflow (see Local Testing section)
- Verify all referenced files exist in `base/` and `overlay/` directories
- Check that the Konflux test image is accessible: `quay.io/konflux-ci/konflux-test:latest`

**Extraction fails:**
- The workflow uses `oc image extract containers-storage:image-name` to access local images
- Verify the image was built successfully: `podman images | grep konflux-config`
- Test extraction manually: `oc image extract containers-storage:image-name --path="/manifests.yaml:."`
- Check that manifests.yaml exists in the image by inspecting the Dockerfile
- Note: Use `containers-storage:` protocol, not `localhost/` (which tries to access a registry)

**Comment not posted:**
- Check workflow logs in GitHub Actions
- Ensure the GITHUB_TOKEN has sufficient permissions
- Verify the repository settings allow workflow comments

**Diff is truncated:**
- For very large diffs (>500 lines), only the first 500 lines are shown in the comment
- Download the full diff from workflow artifacts

### Local Testing

To test changes locally before pushing (using Buildah + oc, same as the workflow):

```bash
# Save current branch
CURRENT_BRANCH=$(git branch --show-current)

# Build from base branch using Buildah
git checkout main
cd konflux-configs
buildah bud --build-arg ENVIRONMENT=prod -t konflux-config-base -f Dockerfile .
oc image extract containers-storage:konflux-config-base --path="/manifests.yaml:/tmp/base.yaml"

# Build from your branch using Buildah
git checkout $CURRENT_BRANCH
buildah bud --build-arg ENVIRONMENT=prod -t konflux-config-head -f Dockerfile .
oc image extract containers-storage:konflux-config-head --path="/manifests.yaml:/tmp/head.yaml"

# Compare
diff -u /tmp/base.yaml /tmp/head.yaml | less

# Or use a visual diff tool
code --diff /tmp/base.yaml /tmp/head.yaml

# Clean up
buildah rmi konflux-config-base konflux-config-head
```

> **Note:** This approach uses `oc image extract`, the exact same command used in your production `extract-and-apply-manifests` task. The `oc` tool can extract files from images stored in local containers-storage (created by buildah/podman) without needing to push them to a registry first. Use the `containers-storage:` protocol prefix to access local images: `containers-storage:image-name:tag`
> 
> **Requirements:** You need the `oc` CLI installed. You can:
> - **Use the Red Hat Action (recommended):** The workflow uses [redhat-actions/openshift-tools-installer](https://github.com/redhat-actions/openshift-tools-installer) which installs and caches `oc` automatically
> - **Manual install:**
>   ```bash
>   # Download from OpenShift mirror
>   curl -sLO https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz
>   tar xzf openshift-client-linux.tar.gz
>   sudo mv oc /usr/local/bin/
>   ```

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

