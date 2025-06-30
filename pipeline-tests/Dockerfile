FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e12131db2e2b6572613589a94b7f615d4ac89d94f859dad05908aeb478fb090f as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e12131db2e2b6572613589a94b7f615d4ac89d94f859dad05908aeb478fb090f as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
