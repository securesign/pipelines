FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:1bc3c5c15720506a0cf48adfdf8b623dfe704377e007d7bbae8d14876392ca6a as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:1bc3c5c15720506a0cf48adfdf8b623dfe704377e007d7bbae8d14876392ca6a as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
