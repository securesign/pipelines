FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:83006d535923fcf1345067873524a3980316f51794f01d8655be55d6e9387183 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:83006d535923fcf1345067873524a3980316f51794f01d8655be55d6e9387183 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
