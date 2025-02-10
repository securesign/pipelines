FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e014f6a342c3790a07b771209b35713e3e4095ff631e4d8bb84966fab3d099e6 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e014f6a342c3790a07b771209b35713e3e4095ff631e4d8bb84966fab3d099e6 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
