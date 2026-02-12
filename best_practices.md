
<b>Pattern 1: Avoid hardcoding temporary development branches or personal refs in Tekton `taskRef`/`ref` revisions; use stable branches/tags (e.g., `main`) or a pipeline parameter propagated consistently, and ensure any temporary override is reverted before merge.
</b>

Example code before:
```
taskRef:
  resolver: git
  params:
    - name: url
      value: https://github.com/org/pipelines.git
    - name: revision
      value: myuser/feature-branch   # temporary override
    - name: pathInRepo
      value: tasks/foo.yaml
```

Example code after:
```
params:
  - name: pipelinesRevision
    default: "main"
taskRef:
  resolver: git
  params:
    - name: url
      value: https://github.com/org/pipelines.git
    - name: revision
      value: $(params.pipelinesRevision)
    - name: pathInRepo
      value: tasks/foo.yaml
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/securesign/pipelines/pull/304#discussion_r2528398170
- https://github.com/securesign/pipelines/pull/84#discussion_r1998200267
- https://github.com/securesign/pipelines/pull/84#discussion_r1998207012
</details>


___

<b>Pattern 2: Model task execution explicitly: add `runAfter`/dependencies when a task consumes results/workspace output from another task, and avoid relying on implicit ordering (especially for clone steps and metadata parsing).
</b>

Example code before:
```
tasks:
  - name: parse-metadata
    taskRef: { name: parse }
  - name: clone-e2e
    taskRef: { name: git-clone }
    params:
      - name: revision
        value: $(tasks.parse-metadata.results.e2e-revision) # consumes result but no dependency
```

Example code after:
```
tasks:
  - name: parse-metadata
    taskRef: { name: parse }
  - name: clone-e2e
    runAfter:
      - parse-metadata
    taskRef: { name: git-clone }
    params:
      - name: revision
        value: $(tasks.parse-metadata.results.e2e-revision)
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/securesign/pipelines/pull/304#discussion_r2528398170
</details>


___

<b>Pattern 3: Do not mask failures in CI pipelines: avoid `onError: continue` for critical install/clone/test steps, and remove ad-hoc debugging output once the pipeline is stable so failures are surfaced and logs stay signal-rich.
</b>

Example code before:
```
- name: install-component
  onError: continue
  script: |
    oc version
    oc get pods -A   # debug noise
    ./run-tests.sh
```

Example code after:
```
- name: install-component
  script: |
    ./run-tests.sh
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/securesign/pipelines/pull/84#discussion_r1998208884
- https://github.com/securesign/pipelines/pull/84#discussion_r1998209372
- https://github.com/securesign/pipelines/pull/84#discussion_r1998211017
</details>


___

<b>Pattern 4: Keep configuration minimal and product-correct: remove duplicated/incorrect metadata (e.g., duplicate labels), avoid applying operator-only conventions (like `monorepo`) to non-operator components, and use the intended canonical values (e.g. release derived from `SOURCE_DATE_EPOCH` when required).
</b>

Example code before:
```
labels:
  - "release=$SOURCE_DATE_EPOCH"
  - "release=1.3.0"         # duplicate/conflicting
monorepo: true              # applied to all components by default
```

Example code after:
```
labels:
  - "release=$SOURCE_DATE_EPOCH"
  - "version=1.3.0"
# monorepo removed for non-operator components
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/securesign/pipelines/pull/231#discussion_r2382194447
- https://github.com/securesign/pipelines/pull/286#discussion_r2493891799
</details>


___
