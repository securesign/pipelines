FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:94b434a29a894129301f6ff52dbddb19422fc800a109170c634b056da8cd704f as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:94b434a29a894129301f6ff52dbddb19422fc800a109170c634b056da8cd704f as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
