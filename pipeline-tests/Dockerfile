FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:fb77e447ab97f3fecd15d2fa5361a99fe2f34b41422e8ebb3612eecd33922fa0 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:fb77e447ab97f3fecd15d2fa5361a99fe2f34b41422e8ebb3612eecd33922fa0 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
