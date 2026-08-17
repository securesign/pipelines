# Red Hat Trusted Artifact Signer's Konflux Build Pipelines

This repository currently holds the Konflux build pipelines for Red Hat Trusted Artifact Signer. To reference these, see the example shown below:

```
pipelineRef:
  resolver: git
  params:
    - name: url
      value: 'https://github.com/securesign/pipelines.git'
    - name: revision
      value: 'sachin/test-pkcs11-e2e'
    - name: pathInRepo
      value: 'pipelines/<pipeline>.yaml'
```

