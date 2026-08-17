FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:692953368d8e630f40a3c0a6135163f8824fdafc26e0400b9a6c8d7fac850366 as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:692953368d8e630f40a3c0a6135163f8824fdafc26e0400b9a6c8d7fac850366 as test
USER 1001
COPY --from=prod /licenses/LICENSE /licenses/LICENSE

LABEL description="Test"
LABEL io.k8s.description="Test"
LABEL io.k8s.display-name="Test"
LABEL io.openshift.tags="Test"
LABEL summary="Test"
LABEL com.redhat.component="Test"
LABEL name="Test"
