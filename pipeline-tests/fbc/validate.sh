#!/usr/bin/env bash
set -euo pipefail

path_context="${1:?path context is required}"

test -f "${path_context}/graph.yaml"
command -v opm >/dev/null
command -v jq >/dev/null
