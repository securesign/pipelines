FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e7da3c032ae52bd26e597cc616eed644710e32e5d3bc9212c7edde8ab7799b0e as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e7da3c032ae52bd26e597cc616eed644710e32e5d3bc9212c7edde8ab7799b0e as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
