FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:dd334afa72444fa46238fcf9e6bd399245adf746378735348cf84b9dfdca38f1 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:dd334afa72444fa46238fcf9e6bd399245adf746378735348cf84b9dfdca38f1 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
