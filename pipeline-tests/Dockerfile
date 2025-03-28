FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:4c8830d349732ed8066544e1cbcf878ad64f39aa4364f13cf4a69954b0ccbda5 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:4c8830d349732ed8066544e1cbcf878ad64f39aa4364f13cf4a69954b0ccbda5 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
