FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8b6978d555746877c73f52375f60fd7b6fd27d6aca000eaed27d0995303c13de as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8b6978d555746877c73f52375f60fd7b6fd27d6aca000eaed27d0995303c13de as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
