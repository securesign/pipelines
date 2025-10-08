# Kustomizeconfig for Project Name Alignment

## Problem
When using `nameSuffix` in kustomize overlays, resource names get transformed (e.g., `rhtas-fbc` → `rhtas-fbc-main`), but custom resource field references don't automatically update. This causes misalignment between:

- `Project` name: `rhtas-fbc-main` (transformed)
- `ProjectDevelopmentStreamTemplate` spec.project: `rhtas-fbc` (not transformed) ❌
- `ProjectDevelopmentStreamTemplate` name: `rhtas-fbc-project-template-main` (transformed)  
- `ProjectDevelopmentStream` spec.template.name: `rhtas-fbc-project-template` (not transformed) ❌

## Solution
Use `kustomizeconfig.yaml` to tell kustomize about name reference relationships:

```yaml
nameReference:
# Project name references
- kind: Project
  version: v1beta1
  group: projctl.konflux.dev
  fieldSpecs:
  - path: spec/project
    kind: ProjectDevelopmentStreamTemplate
    group: projctl.konflux.dev
    version: v1beta1
  - path: spec/project
    kind: ProjectDevelopmentStream
    group: projctl.konflux.dev
    version: v1beta1
# ProjectDevelopmentStreamTemplate name references  
- kind: ProjectDevelopmentStreamTemplate
  version: v1beta1
  group: projctl.konflux.dev
  fieldSpecs:
  - path: spec/template/name
    kind: ProjectDevelopmentStream
    group: projctl.konflux.dev
    version: v1beta1
```

## Result
After applying kustomizeconfig:
- `Project` name: `rhtas-fbc-main` (transformed)
- `ProjectDevelopmentStreamTemplate` spec.project: `rhtas-fbc-main` (aligned) ✅
- `ProjectDevelopmentStreamTemplate` name: `rhtas-fbc-project-template-main` (transformed)
- `ProjectDevelopmentStream` spec.template.name: `rhtas-fbc-project-template-main` (aligned) ✅

## Implementation
Each overlay needs its own `kustomizeconfig.yaml` due to kustomize security restrictions:

```
overlay/
├── main/
│   ├── kustomization.yaml
│   └── kustomizeconfig.yaml
└── v1-2/
    ├── kustomization.yaml
    └── kustomizeconfig.yaml
```

Reference it in your `kustomization.yaml`:
```yaml
configurations:
  - kustomizeconfig.yaml
```

## Verified Overlays
- ✅ `main`: All names aligned with `-main` suffix
  - Project: `rhtas-fbc-main`
  - Template: `rhtas-fbc-project-template-main`
  - All references properly aligned
- ✅ `v1-2`: All names aligned with `-v1-2` suffix  
  - Project: `rhtas-fbc-v1-2`
  - Template: `rhtas-fbc-project-template-v1-2`
  - All references properly aligned
