FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:186a94b76e386782f576c9c49813b16dceb2ba63102af5a28405dcefec2806d0 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:186a94b76e386782f576c9c49813b16dceb2ba63102af5a28405dcefec2806d0 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
