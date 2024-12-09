FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:f598528219a1be07cf520fbe82a2d2434dc9841e1f0a878382c8a13bf42cb486 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:f598528219a1be07cf520fbe82a2d2434dc9841e1f0a878382c8a13bf42cb486 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
