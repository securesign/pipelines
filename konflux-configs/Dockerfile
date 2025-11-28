
ARG ENVIRONMENT="prod"

FROM quay.io/konflux-ci/konflux-test:1.4.41@sha256:afea44d83043be7f528ec2cacaeb0c3b69cdafdd86a1b930957def38400f8a6c AS builder

ARG ENVIRONMENT

WORKDIR /tmp

COPY ./base/ ./base/
COPY ./overlay/ ./overlay/

RUN oc kustomize -o /tmp/manifests.yaml ./overlay/$ENVIRONMENT

FROM scratch

LABEL maintainer="Red Hat, Inc."
LABEL vendor="Red Hat, Inc."
LABEL url="https://www.redhat.com"
LABEL distribution-scope="private"

# Copy files to locations specified by labels.
COPY --from=builder /tmp/manifests.yaml /manifests.yaml
