FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8b314e254e9ab9a7a08b675fcfd3ed66a2943eeda7b26395210d451569976b9b as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8b314e254e9ab9a7a08b675fcfd3ed66a2943eeda7b26395210d451569976b9b as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
