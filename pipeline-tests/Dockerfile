FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8d905a93f1392d4a8f7fb906bd49bf540290674b28d82de3536bb4d0898bf9d7 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8d905a93f1392d4a8f7fb906bd49bf540290674b28d82de3536bb4d0898bf9d7 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
