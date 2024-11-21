FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8b6978d555746877c73f52375f60fd7b6fd27d6aca000eaed27d0995303c13de as prod
COPY LICENSE /licenses/LICENSE
USER 1001

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:8b6978d555746877c73f52375f60fd7b6fd27d6aca000eaed27d0995303c13de as test

COPY --from=prod /licenses/LICENSE /licenses/LICENSE
