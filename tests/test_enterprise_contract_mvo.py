"""Run the deployed MVO cohort selector itself against an isolated Kubernetes mock.

These fixtures reproduce the stale-agent failure shape. Image/UID placeholders
other than the two incident agent digests are synthetic, not production evidence.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


PIPELINE_PATH = Path(__file__).resolve().parents[1] / "pipelines" / "enterprise-contract-mvo.yaml"
NAMESPACE = "rhtas-tenant"
OPERATOR = "model-validation-operator"
AGENT = OPERATOR + "-agent"
BUNDLE = OPERATOR + "-bundle"
REPOSITORY = "https://github.com/securesign/model-validation-operator"
REVISION = "75fcc94922382b33a664fc6115abd562ea60632a"
OLD_REVISION = "aeb7bee70bde69c0044a162fd261818c4456665a"
AGENT_DIGEST = "sha256:72822d45591982e46f888ae06580c5d66c7422e1ab13cdadbe3db42e60b7e270"
OLD_AGENT_DIGEST = "sha256:44811790523d9ca554fcb2b063b35282cda0bcd51dc3086ce7992611f3d062d4"
OPERATOR_DIGEST = "sha256:" + "d" * 64
BUNDLE_DIGEST = "sha256:" + "f" * 64
EC_BUNDLE = "quay.io/conforma/tekton-task:konflux@sha256:e5a704109a8b2cc54ee4785589b95d1a110daf77c561721cec17efa645c8f5d9"


def component(name, digest, revision=REVISION, repository=REPOSITORY):
    return {
        "name": name,
        "containerImage": "quay.io/securesign/" + name + "@" + digest,
        "source": {"git": {"url": repository, "revision": revision}},
    }


def context_metadata(event="pull_request"):
    labels = {"pac.test.appstudio.openshift.io/event-type": event}
    annotations = {
        "pac.test.appstudio.openshift.io/event-type": event,
        "pac.test.appstudio.openshift.io/sha": REVISION,
        "pac.test.appstudio.openshift.io/source-repo-url": REPOSITORY,
        "pac.test.appstudio.openshift.io/repo-url": REPOSITORY,
        "pac.test.appstudio.openshift.io/source-branch": "SECURESIGN-4194-cleanup" if event == "pull_request" else "main",
        "pac.test.appstudio.openshift.io/target-branch": "main",
    }
    if event == "pull_request":
        labels.update({
            "pac.test.appstudio.openshift.io/pull-request": "132",
            "test.appstudio.openshift.io/pr-group-sha": "a" * 64,
        })
        annotations.update({
            "pac.test.appstudio.openshift.io/pull-request": "132",
            "test.appstudio.openshift.io/pr-group": "SECURESIGN-4194-cleanup",
        })
    return labels, annotations


def fixture(event="pull_request"):
    labels, annotations = context_metadata(event)
    original = {
        "apiVersion": "appstudio.redhat.com/v1alpha1",
        "kind": "Snapshot",
        "metadata": {
            "name": "original-snapshot",
            "namespace": NAMESPACE,
            "uid": "original-snapshot-uid",
            "labels": {
                **labels,
                "appstudio.openshift.io/application": OPERATOR,
                "appstudio.openshift.io/component": OPERATOR,
                "appstudio.openshift.io/build-pipelinerun": "operator-build",
                "test.appstudio.openshift.io/type": "component",
            },
            "annotations": annotations,
        },
        "spec": {
            "application": OPERATOR,
            "components": [
                component(OPERATOR, OPERATOR_DIGEST),
                component(AGENT, OLD_AGENT_DIGEST, OLD_REVISION),
                component(BUNDLE, "sha256:" + "e" * 64, OLD_REVISION),
            ],
        },
    }
    integration = {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "name": "integration-run",
            "namespace": NAMESPACE,
            "labels": {
                **labels,
                "appstudio.openshift.io/snapshot": "original-snapshot",
                "appstudio.openshift.io/application": OPERATOR,
                "appstudio.openshift.io/component": OPERATOR,
            },
            "annotations": deepcopy(annotations),
        },
        "spec": {"params": [{"name": "SNAPSHOT", "value": json.dumps(original["spec"])}]},
    }
    build = {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "name": "operator-build",
            "namespace": NAMESPACE,
            "uid": "operator-build-uid",
            "labels": {**labels, "appstudio.openshift.io/component": OPERATOR},
            "annotations": deepcopy(annotations),
        },
        "status": {
            "conditions": [{"type": "Succeeded", "status": "True"}],
            "results": [{"name": "IMAGE_URL", "value": "quay.io/securesign/" + OPERATOR}, {"name": "IMAGE_DIGEST", "value": OPERATOR_DIGEST}],
            "childReferences": [{
                "apiVersion": "tekton.dev/v1", "kind": "TaskRun",
                "name": "operator-build-images", "pipelineTaskName": "build-images",
            }],
        },
    }
    task = {
        "apiVersion": "tekton.dev/v1",
        "kind": "TaskRun",
        "metadata": {
            "name": "operator-build-images", "namespace": NAMESPACE,
            "labels": {"tekton.dev/pipelineRun": "operator-build", "tekton.dev/pipelineTask": "build-images"},
            "ownerReferences": [{
                "apiVersion": "tekton.dev/v1", "kind": "PipelineRun",
                "name": "operator-build", "uid": "operator-build-uid", "controller": True,
            }],
        },
        "spec": {"params": [{"name": "BUILD_ARGS", "value": [
            "AGENT_IMG=registry.redhat.io/rhtas/model-validation-agent-rhel9@" + AGENT_DIGEST,
        ]}]},
        "status": {"conditions": [{"type": "Succeeded", "status": "True"}]},
    }
    entries = []
    for name, snapshot, build_name in [
        (OPERATOR, "original-snapshot", "operator-build"),
        (AGENT, "agent-snapshot", "agent-build"),
        (BUNDLE, "bundle-snapshot", "bundle-build"),
    ]:
        entries.append({
            "namespace": NAMESPACE, "component": name,
            "buildPipelineRun": build_name, "snapshot": snapshot,
            "repoUrl": REPOSITORY, "pullRequestNumber": "132" if event == "pull_request" else "", "version": "",
        })
    candidate = {
        "apiVersion": "appstudio.redhat.com/v1alpha1",
        "kind": "Snapshot",
        "metadata": {
            "name": "coherent-group" if event == "pull_request" else "coherent-push",
            "namespace": NAMESPACE, "uid": "coherent-snapshot-uid",
            "creationTimestamp": "2026-11-24T12:42:32Z",
            "labels": {
                **labels,
                "appstudio.openshift.io/application": OPERATOR,
                "test.appstudio.openshift.io/type": "group" if event == "pull_request" else "component",
                "appstudio.openshift.io/component": BUNDLE,
                "appstudio.openshift.io/build-pipelinerun": "bundle-build",
            },
            "annotations": deepcopy(annotations),
        },
        "spec": {
            "application": OPERATOR,
            "components": [component(OPERATOR, OPERATOR_DIGEST), component(AGENT, AGENT_DIGEST), component(BUNDLE, BUNDLE_DIGEST)],
        },
    }
    if event == "pull_request":
        candidate["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"] = json.dumps(entries)
    return {
        "resources": {
            "pipelineruns/integration-run": integration,
            "snapshots/original-snapshot": original,
            "pipelineruns/operator-build": build,
            "taskruns/operator-build-images": task,
        },
        "groups": [candidate],
    }


def fork_fixture():
    """A fork PR is still built by the target namespace's trusted Konflux build."""
    state = fixture()
    fork_url = "https://github.com/contributor/model-validation-operator"
    for obj in list(state["resources"].values()) + state["groups"]:
        annotations = obj["metadata"].get("annotations", {})
        if "pac.test.appstudio.openshift.io/source-repo-url" in annotations:
            annotations["pac.test.appstudio.openshift.io/source-repo-url"] = fork_url
            annotations["pac.test.appstudio.openshift.io/repo-url"] = REPOSITORY
    original = state["resources"]["snapshots/original-snapshot"]
    original["spec"]["components"][0]["source"]["git"]["url"] = fork_url
    for entry in state["groups"][0]["spec"]["components"]:
        entry["source"]["git"]["url"] = fork_url
    state["resources"]["pipelineruns/operator-build"]["spec"] = {"params": [{"name": "git-url", "value": fork_url}, {"name": "revision", "value": REVISION}]}
    state["resources"]["pipelineruns/integration-run"]["spec"]["params"][0]["value"] = json.dumps(original["spec"])
    return state


MOCK_OC = r'''#!/usr/bin/env python3
import json, os, pathlib, re, sys
args = sys.argv[1:]
state = json.loads(pathlib.Path(os.environ["MOCK_STATE"]).read_text())
calls_path = pathlib.Path(os.environ["MOCK_CALLS"])
namespace = None
timeout = None
clean = []
i = 0
while i < len(args):
    arg = args[i]
    if arg in ("-n", "--namespace", "--request-timeout", "-o", "--output", "-l", "--selector", "--field-selector"):
        if i + 1 >= len(args):
            raise SystemExit("missing flag value")
        value = args[i + 1]
        if arg in ("-n", "--namespace"):
            namespace = value
        elif arg == "--request-timeout":
            timeout = value
        i += 2
        continue
    if arg.startswith("--namespace="):
        namespace = arg.split("=", 1)[1]
    elif arg.startswith("--request-timeout="):
        timeout = arg.split("=", 1)[1]
    elif arg.startswith(("--output=", "--selector=", "--field-selector=", "-o=", "-l=")):
        pass
    else:
        clean.append(arg)
    i += 1
if not clean or clean[0] != "get":
    raise SystemExit("mock refuses non-get API access")
if namespace != "rhtas-tenant":
    raise SystemExit("namespace was not explicitly bounded")
if not timeout or not re.fullmatch(r"[1-9][0-9]*s", timeout) or int(timeout[:-1]) > 60:
    raise SystemExit("request timeout was not explicitly bounded")
resource = clean[1]
name = clean[2] if len(clean) > 2 else None
if "/" in resource:
    resource, name = resource.split("/", 1)
resource = resource.split(".", 1)[0].lower()
resource = {"snapshot": "snapshots", "pr": "pipelineruns", "pipelinerun": "pipelineruns", "taskrun": "taskruns", "tr": "taskruns"}.get(resource, resource)
key = resource + ("/" + name if name else "")
previous = [json.loads(x) for x in calls_path.read_text().splitlines()] if calls_path.exists() else []
with calls_path.open("a") as out:
    out.write(json.dumps({"key": key, "namespace": namespace, "timeout": timeout, "args": args}) + "\n")
if key in state.get("errors", {}):
    print(state["errors"][key], file=sys.stderr)
    raise SystemExit(1)
if resource == "snapshots" and not name:
    responses = state.get("list_responses")
    if responses:
        index = min(sum(c["key"] == "snapshots" for c in previous), len(responses) - 1)
        groups = responses[index]
    else:
        groups = state.get("groups", [])
    print(json.dumps({"apiVersion": "appstudio.redhat.com/v1alpha1", "kind": "SnapshotList", "items": groups}))
elif key in state["resources"]:
    print(json.dumps(state["resources"][key]))
else:
    print("Error from server (NotFound): " + key, file=sys.stderr)
    raise SystemExit(1)
'''


class SelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = yaml.safe_load(PIPELINE_PATH.read_text())
        cls.selector = next(task for task in cls.pipeline["spec"]["tasks"] if task["name"] == "resolve-mvo-snapshot")
        cls.step = next(step for step in cls.selector["taskSpec"]["steps"] if step["name"] == "resolve")
        cls.script = cls.step["script"]

    def run_selector(self, state, env_changes=None, success=True):
        with tempfile.TemporaryDirectory(prefix="mvo-cohort-test-") as tmp:
            root = Path(tmp)
            state_path = root / "state.json"
            state_path.write_text(json.dumps(state))
            oc = root / "oc"
            oc.write_text(MOCK_OC)
            oc.chmod(0o755)
            script_path = root / "resolve.sh"
            script_path.write_text(self.script)
            result_path, name_path = root / "snapshot-result", root / "name-result"
            env = os.environ.copy()
            env.pop("BASH_ENV", None)
            env.pop("ENV", None)
            env.update({
                "PATH": str(root) + os.pathsep + env["PATH"],
                "MOCK_STATE": str(state_path), "MOCK_CALLS": str(root / "calls.jsonl"),
                "SNAPSHOT_INPUT": json.dumps(state["resources"]["snapshots/original-snapshot"]["spec"]),
                "INTEGRATION_PIPELINERUN": "integration-run", "NAMESPACE": NAMESPACE, "APPLICATION": OPERATOR,
                "OPERATOR_COMPONENT": OPERATOR, "AGENT_COMPONENT": AGENT, "BUNDLE_COMPONENT": BUNDLE,
                "WAIT_TIMEOUT_SECONDS": "1", "POLL_INTERVAL_SECONDS": "1", "REQUEST_TIMEOUT_SECONDS": "1",
                "STRICT": "true", "SINGLE_COMPONENT": "false",
                "RESULT_SNAPSHOT_PATH": str(result_path), "RESULT_NAME_PATH": str(name_path),
            })
            env.update(env_changes or {})
            result = subprocess.run(["bash", str(script_path)], env=env, text=True, capture_output=True, timeout=12)
            diagnostic = result.stdout + "\n" + result.stderr
            calls = [json.loads(x) for x in (root / "calls.jsonl").read_text().splitlines()] if (root / "calls.jsonl").exists() else []
            if success:
                self.assertEqual(result.returncode, 0, diagnostic)
                self.assertTrue(result_path.exists(), diagnostic)
                selected = json.loads(result_path.read_text())
                name = name_path.read_text().strip()
                self.assertTrue(calls, "selector did not read live identity evidence")
                return selected, name, calls, diagnostic
            self.assertNotEqual(result.returncode, 0, diagnostic)
            self.assertFalse(result_path.exists() and result_path.read_text().strip(), "a failed selector emitted a snapshot")
            return None, None, calls, diagnostic

    def reject_group(self, change):
        state = fixture()
        change(state["groups"][0])
        self.run_selector(state, success=False)

    def test_stale_original_agent_is_replaced_by_exact_consumed_group_agent(self):
        state = fixture()
        selected, name, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])
        self.assertEqual(name, "coherent-group")
        self.assertNotEqual(selected, state["resources"]["snapshots/original-snapshot"]["spec"])

    def test_push_uses_final_coherent_component_snapshot_without_pr_group(self):
        state = fixture("push")
        selected, name, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])
        self.assertEqual(name, "coherent-push")

    def test_legacy_push_without_event_type_or_pr_number(self):
        state = fixture("push")
        for obj in list(state["resources"].values()) + state["groups"]:
            for field in ("labels", "annotations"):
                obj["metadata"].get(field, {}).pop("pac.test.appstudio.openshift.io/event-type", None)
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_same_revision_does_not_authorize_different_agent_digest(self):
        self.reject_group(lambda group: group["spec"]["components"][1].update(containerImage="quay.io/securesign/agent@sha256:" + "b" * 64))

    def test_wrong_operator_image(self):
        self.reject_group(lambda group: group["spec"]["components"][0].update(containerImage="quay.io/securesign/operator@sha256:" + "b" * 64))

    def test_wrong_source_revision(self):
        self.reject_group(lambda group: group["spec"]["components"][2]["source"]["git"].update(revision=OLD_REVISION))

    def test_wrong_source_repository(self):
        self.reject_group(lambda group: group["spec"]["components"][1]["source"]["git"].update(url="https://github.com/unrelated/agent"))

    def test_missing_required_component(self):
        self.reject_group(lambda group: group["spec"]["components"].pop())

    def test_duplicate_required_component(self):
        self.reject_group(lambda group: group["spec"]["components"].append(deepcopy(group["spec"]["components"][1])))

    def test_wrong_application(self):
        self.reject_group(lambda group: group["spec"].update(application="unrelated-app"))

    def test_wrong_namespace(self):
        self.reject_group(lambda group: group["metadata"].update(namespace="other-tenant"))

    def test_wrong_pr_context(self):
        def change(group):
            info = json.loads(group["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"])
            info[0]["pullRequestNumber"] = "999"
            group["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"] = json.dumps(info)
        self.reject_group(change)

    def test_wrong_operator_build_identity_in_group_info(self):
        def change(group):
            info = json.loads(group["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"])
            info[0]["buildPipelineRun"] = "different-operator-build"
            group["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"] = json.dumps(info)
        self.reject_group(change)

    def test_group_without_controller_group_info(self):
        self.reject_group(lambda group: group["metadata"]["annotations"].pop("test.appstudio.openshift.io/group-test-info"))

    def test_keep_additional_snapshot_components(self):
        state = fixture()
        state["groups"][0]["spec"]["components"].append(component("external", "sha256:" + "c" * 64, OLD_REVISION, "https://github.com/example/external"))
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])
        self.assertEqual(len(selected["components"]), 4)

    def test_ambiguous_different_image_vectors_fail_closed(self):
        state = fixture()
        second = deepcopy(state["groups"][0])
        second["metadata"]["name"] = "second-coherent-group"
        second["spec"]["components"][2]["containerImage"] = "quay.io/securesign/bundle@sha256:" + "c" * 64
        state["groups"].append(second)
        self.run_selector(state, success=False)

    def test_identical_duplicate_groups_choose_deterministically(self):
        state = fixture()
        second = deepcopy(state["groups"][0])
        second["metadata"].update(name="another-coherent-group", creationTimestamp="2026-11-24T12:43:00Z")
        state["groups"].append(second)
        selected, first_name, _, _ = self.run_selector(state)
        state["groups"].reverse()
        reverse_selected, reverse_name, _, _ = self.run_selector(state)
        self.assertEqual(selected, reverse_selected)
        self.assertEqual(first_name, reverse_name)

    def test_waits_for_group_creation(self):
        state = fixture()
        state["list_responses"] = [[], state["groups"]]
        selected, _, calls, _ = self.run_selector(state, {"WAIT_TIMEOUT_SECONDS": "5"})
        self.assertEqual(selected, state["groups"][0]["spec"])
        self.assertGreaterEqual(sum(call["key"] == "snapshots" for call in calls), 2)

    def test_missing_group_times_out_without_fallback(self):
        state = fixture()
        state["groups"] = []
        _, _, _, diagnostic = self.run_selector(state, success=False)
        self.assertIn("timed out", diagnostic)

    def test_api_denial_is_not_an_empty_group_list(self):
        state = fixture()
        state["errors"] = {"snapshots": "Error from server (Forbidden): snapshots is forbidden"}
        _, _, calls, diagnostic = self.run_selector(state, success=False)
        self.assertIn("Forbidden", diagnostic)
        self.assertEqual(sum(call["key"] == "snapshots" for call in calls), 1)

    def test_api_request_timeout_fails_closed(self):
        state = fixture()
        state["errors"] = {"pipelineruns/operator-build": "request timed out: context deadline exceeded"}
        _, _, _, diagnostic = self.run_selector(state, success=False)
        self.assertIn("deadline", diagnostic)

    def test_missing_build_evidence(self):
        state = fixture()
        state["resources"].pop("taskruns/operator-build-images")
        self.run_selector(state, success=False)

    def test_taskrun_must_be_owned_by_expected_build(self):
        state = fixture()
        state["resources"]["taskruns/operator-build-images"]["metadata"]["ownerReferences"][0]["uid"] = "different-build-uid"
        self.run_selector(state, success=False)

    def test_conflicting_agent_arguments_are_not_guessed(self):
        state = fixture()
        state["resources"]["taskruns/operator-build-images"]["spec"]["params"][0]["value"].append("AGENT_IMG=quay.io/agent@sha256:" + "c" * 64)
        self.run_selector(state, success=False)

    def test_malformed_original_does_not_get_repaired_silently(self):
        state = fixture()
        state["resources"]["snapshots/original-snapshot"]["spec"]["components"][0]["containerImage"] = "quay.io/operator:latest"
        self.run_selector(state, success=False)

    def test_strict_false_is_rejected(self):
        self.run_selector(fixture(), {"STRICT": "false"}, success=False)

    def test_single_component_true_is_rejected(self):
        self.run_selector(fixture(), {"SINGLE_COMPONENT": "true"}, success=False)

    def test_unbounded_request_timeout_is_rejected(self):
        self.run_selector(fixture(), {"REQUEST_TIMEOUT_SECONDS": "0"}, success=False)

    def test_input_snapshot_cannot_replace_live_operator_identity(self):
        state = fixture()
        supplied = deepcopy(state["resources"]["snapshots/original-snapshot"]["spec"])
        supplied["components"][0]["containerImage"] = "quay.io/operator@sha256:" + "a" * 64
        self.run_selector(state, {"SNAPSHOT_INPUT": json.dumps(supplied)}, success=False)

    def test_managed_application_cannot_be_substituted(self):
        self.run_selector(fixture(), {"APPLICATION": "different-app"}, success=False)

    def test_pull_request_cannot_claim_push_event(self):
        state = fixture()
        original = state["resources"]["snapshots/original-snapshot"]
        original["metadata"]["labels"]["pac.test.appstudio.openshift.io/event-type"] = "push"
        original["metadata"]["annotations"]["pac.test.appstudio.openshift.io/event-type"] = "push"
        self.run_selector(state, success=False)

    def test_pull_request_number_must_be_numeric(self):
        state = fixture()
        original = state["resources"]["snapshots/original-snapshot"]
        original["metadata"]["labels"]["pac.test.appstudio.openshift.io/pull-request"] = "not-a-number"
        original["metadata"]["annotations"]["pac.test.appstudio.openshift.io/pull-request"] = "not-a-number"
        self.run_selector(state, success=False)

    def test_controller_owner_is_preserved_when_available(self):
        state = fixture()
        owner = {"apiVersion": "appstudio.redhat.com/v1alpha1", "kind": "Application", "name": OPERATOR, "uid": "app-uid", "controller": True}
        state["resources"]["snapshots/original-snapshot"]["metadata"]["ownerReferences"] = [owner]
        state["groups"][0]["metadata"]["ownerReferences"] = [deepcopy(owner)]
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_other_controller_owner_is_rejected_when_original_has_one(self):
        state = fixture()
        owner = {"apiVersion": "appstudio.redhat.com/v1alpha1", "kind": "Application", "name": OPERATOR, "uid": "app-uid", "controller": True}
        state["resources"]["snapshots/original-snapshot"]["metadata"]["ownerReferences"] = [owner]
        state["groups"][0]["metadata"]["ownerReferences"] = [{**owner, "uid": "other-app-uid"}]
        self.run_selector(state, success=False)

    def test_new_pac_aliases_are_accepted(self):
        state = fixture()
        for obj in list(state["resources"].values()) + state["groups"]:
            for field in ("labels", "annotations"):
                metadata = obj["metadata"].get(field, {})
                for key in list(metadata):
                    if key.startswith("pac.test.appstudio.openshift.io/"):
                        metadata[key.replace("pac.test.appstudio.openshift.io/", "pac.integration.konflux-ci.dev/")] = metadata.pop(key)
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_conflicting_metadata_aliases_fail_closed(self):
        state = fixture()
        state["resources"]["snapshots/original-snapshot"]["metadata"]["labels"]["pac.integration.konflux-ci.dev/pull-request"] = "999"
        self.run_selector(state, success=False)

    def test_conflicting_label_and_annotation_fail_closed(self):
        state = fixture()
        state["resources"]["snapshots/original-snapshot"]["metadata"]["annotations"]["pac.test.appstudio.openshift.io/pull-request"] = "999"
        self.run_selector(state, success=False)

    def test_wrong_group_hash(self):
        self.reject_group(lambda group: group["metadata"]["labels"].update({"test.appstudio.openshift.io/pr-group-sha": "b" * 64}))

    def test_wrong_group_name(self):
        self.reject_group(lambda group: group["metadata"]["annotations"].update({"test.appstudio.openshift.io/pr-group": "different-stack"}))

    def test_group_info_must_refer_to_original_snapshot(self):
        def change(group):
            info = json.loads(group["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"])
            info[0]["snapshot"] = "different-original-snapshot"
            group["metadata"]["annotations"]["test.appstudio.openshift.io/group-test-info"] = json.dumps(info)
        self.reject_group(change)

    def test_conflicting_platform_dependency_digests_fail_closed(self):
        state = fixture()
        build = state["resources"]["pipelineruns/operator-build"]
        build["status"]["childReferences"].append({"apiVersion": "tekton.dev/v1", "kind": "TaskRun", "name": "other-platform", "pipelineTaskName": "build-images"})
        task = deepcopy(state["resources"]["taskruns/operator-build-images"])
        task["metadata"]["name"] = "other-platform"
        task["spec"]["params"][0]["value"] = ["AGENT_IMG=registry.redhat.io/rhtas/agent@sha256:" + "c" * 64]
        state["resources"]["taskruns/other-platform"] = task
        self.run_selector(state, success=False)

    def test_matching_platform_dependency_digests_are_allowed(self):
        state = fixture()
        build = state["resources"]["pipelineruns/operator-build"]
        build["status"]["childReferences"].append({"apiVersion": "tekton.dev/v1", "kind": "TaskRun", "name": "other-platform", "pipelineTaskName": "build-images"})
        task = deepcopy(state["resources"]["taskruns/operator-build-images"])
        task["metadata"]["name"] = "other-platform"
        state["resources"]["taskruns/other-platform"] = task
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_group_snapshot_without_pac_pr_number_uses_controller_group_info(self):
        state = fixture()
        candidate = state["groups"][0]
        for field in ("labels", "annotations"):
            candidate["metadata"][field].pop("pac.test.appstudio.openshift.io/pull-request", None)
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, candidate["spec"])

    def test_pr_group_cannot_claim_push_event(self):
        def change(group):
            for field in ("labels", "annotations"):
                group["metadata"][field]["pac.test.appstudio.openshift.io/event-type"] = "push"
        self.reject_group(change)

    def test_pr_group_cannot_claim_different_nonempty_pr_number(self):
        def change(group):
            for field in ("labels", "annotations"):
                group["metadata"][field]["pac.test.appstudio.openshift.io/pull-request"] = "999"
        self.reject_group(change)

    def test_push_cannot_select_pr_component_snapshot(self):
        state = fixture("push")
        candidate = state["groups"][0]
        for field in ("labels", "annotations"):
            candidate["metadata"][field]["pac.test.appstudio.openshift.io/pull-request"] = "132"
            candidate["metadata"][field]["pac.test.appstudio.openshift.io/event-type"] = "pull_request"
        self.run_selector(state, success=False)

    def test_source_build_identity_is_anchored_to_original_operator(self):
        cases = [
            ("digest", lambda build: next(result for result in build["status"]["results"] if result["name"] == "IMAGE_DIGEST").update(value="sha256:" + "a" * 64)),
            ("repository", lambda build: next(result for result in build["status"]["results"] if result["name"] == "IMAGE_URL").update(value="quay.io/unrelated/operator")),
            ("missing-image-results", lambda build: build["status"].update(results=[])),
            ("component", lambda build: build["metadata"]["labels"].update({"appstudio.openshift.io/component": AGENT})),
            ("sha", lambda build: build["metadata"]["annotations"].update({"pac.test.appstudio.openshift.io/sha": OLD_REVISION})),
        ]
        for reason, change in cases:
            with self.subTest(reason=reason):
                state = fixture()
                change(state["resources"]["pipelineruns/operator-build"])
                self.run_selector(state, success=False)

    def test_source_build_pr_cannot_differ_from_original_snapshot(self):
        state = fixture()
        for field in ("labels", "annotations"):
            state["resources"]["pipelineruns/operator-build"]["metadata"][field]["pac.test.appstudio.openshift.io/pull-request"] = "999"
        self.run_selector(state, success=False)

    def test_integration_pr_cannot_differ_from_original_snapshot(self):
        state = fixture()
        for field in ("labels", "annotations"):
            state["resources"]["pipelineruns/integration-run"]["metadata"][field]["pac.test.appstudio.openshift.io/pull-request"] = "999"
        self.run_selector(state, success=False)

    def test_source_build_git_parameters_are_validated_when_present(self):
        for field, invalid in [("git-url", "https://github.com/unrelated/operator"), ("revision", OLD_REVISION)]:
            with self.subTest(field=field):
                state = fixture()
                params = {"git-url": REPOSITORY, "revision": REVISION}
                params[field] = invalid
                state["resources"]["pipelineruns/operator-build"]["spec"] = {"params": [{"name": name, "value": value} for name, value in params.items()]}
                self.run_selector(state, success=False)
        state = fixture()
        state["resources"]["pipelineruns/operator-build"]["spec"] = {"params": [{"name": "git-url", "value": REPOSITORY}, {"name": "revision", "value": REVISION}]}
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_taskrun_identity_labels_cannot_contradict_ownership(self):
        for label, invalid in [("tekton.dev/pipelineRun", "different-build"), ("tekton.dev/pipelineTask", "different-task")]:
            with self.subTest(label=label):
                state = fixture()
                state["resources"]["taskruns/operator-build-images"]["metadata"]["labels"][label] = invalid
                self.run_selector(state, success=False)

    def test_push_candidate_pac_identity_cannot_contradict_component_sources(self):
        for field, invalid in [("sha", OLD_REVISION), ("source-repo-url", "https://github.com/unrelated/operator")]:
            with self.subTest(field=field):
                state = fixture("push")
                state["groups"][0]["metadata"]["annotations"]["pac.test.appstudio.openshift.io/" + field] = invalid
                self.run_selector(state, success=False)

    def test_escaped_quotes_cannot_overflow_tekton_results(self):
        state = fixture()
        state["groups"][0]["spec"]["components"][0]["description"] = '"' * 800
        _, _, _, diagnostic = self.run_selector(state, success=False)
        self.assertIn("result", diagnostic.lower())

    def test_html_escaping_cannot_overflow_tekton_results(self):
        state = fixture()
        state["groups"][0]["spec"]["components"][0]["description"] = "<" * 700
        _, _, _, diagnostic = self.run_selector(state, success=False)
        self.assertIn("result", diagnostic.lower())

    def test_small_escaped_metadata_is_preserved_within_result_budget(self):
        state = fixture()
        state["groups"][0]["spec"]["components"][0]["description"] = '"<&>"' * 20
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_trusted_build_of_fork_pr_preserves_source_and_target_identity(self):
        state = fork_fixture()
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])
        self.assertEqual(selected["components"][0]["source"]["git"]["url"], "https://github.com/contributor/model-validation-operator")

    def test_fork_pr_cannot_target_unrelated_repository(self):
        state = fork_fixture()
        state["resources"]["snapshots/original-snapshot"]["metadata"]["annotations"]["pac.test.appstudio.openshift.io/repo-url"] = "https://github.com/unrelated/model-validation-operator"
        self.run_selector(state, success=False)

    def test_fork_pr_requires_explicit_target_evidence(self):
        state = fork_fixture()
        state["resources"]["snapshots/original-snapshot"]["metadata"]["annotations"].pop("pac.test.appstudio.openshift.io/repo-url")
        self.run_selector(state, success=False)

    def test_fork_build_requires_matching_target_evidence(self):
        state = fork_fixture()
        state["resources"]["pipelineruns/operator-build"]["metadata"]["annotations"].pop("pac.test.appstudio.openshift.io/repo-url")
        self.run_selector(state, success=False)

    def test_fork_build_cannot_change_source_or_target(self):
        for field, invalid in [("source-repo-url", "https://github.com/unrelated/model-validation-operator"), ("repo-url", "https://github.com/unrelated/target")]:
            with self.subTest(field=field):
                state = fork_fixture()
                state["resources"]["pipelineruns/operator-build"]["metadata"]["annotations"]["pac.test.appstudio.openshift.io/" + field] = invalid
                self.run_selector(state, success=False)

    def test_fork_build_git_url_must_match_fork_source(self):
        state = fork_fixture()
        state["resources"]["pipelineruns/operator-build"]["spec"]["params"][0]["value"] = REPOSITORY
        self.run_selector(state, success=False)

    def test_same_repository_legacy_without_target_metadata_remains_valid(self):
        state = fixture()
        for obj in list(state["resources"].values()) + state["groups"]:
            obj["metadata"].get("annotations", {}).pop("pac.test.appstudio.openshift.io/repo-url", None)
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_fork_target_can_use_pac_organization_repository_labels(self):
        state = fork_fixture()
        for obj in list(state["resources"].values()) + state["groups"]:
            obj["metadata"].get("annotations", {}).pop("pac.test.appstudio.openshift.io/repo-url", None)
            obj["metadata"].setdefault("labels", {}).update({"pipelinesascode.tekton.dev/url-org": "securesign", "pipelinesascode.tekton.dev/url-repository": "model-validation-operator"})
        selected, _, _, _ = self.run_selector(state)
        self.assertEqual(selected, state["groups"][0]["spec"])

    def test_conflicting_full_target_and_organization_labels_fail_closed(self):
        state = fork_fixture()
        state["resources"]["snapshots/original-snapshot"]["metadata"]["labels"].update({"pipelinesascode.tekton.dev/url-org": "unrelated", "pipelinesascode.tekton.dev/url-repository": "model-validation-operator"})
        self.run_selector(state, success=False)

    def test_standard_strict_verification_and_identity_wiring_is_preserved(self):
        tasks = {task["name"]: task for task in self.pipeline["spec"]["tasks"]}
        verify = tasks["verify"]
        values = {param["name"]: param["value"] for param in verify["params"]}
        defaults = {param["name"]: param.get("default") for param in self.pipeline["spec"]["params"]}
        self.assertEqual(defaults["STRICT"], "true")
        self.assertEqual(defaults["SINGLE_COMPONENT"], "false")
        self.assertEqual(values["IMAGES"], "$(tasks.resolve-mvo-snapshot.results.SNAPSHOT)")
        self.assertIn(values["STRICT"], ("true", "$(params.STRICT)"))
        self.assertIn(values["SINGLE_COMPONENT"], ("false", "$(params.SINGLE_COMPONENT)"))
        self.assertEqual(values["POLICY_CONFIGURATION"], "$(params.POLICY_CONFIGURATION)")
        self.assertEqual(values["PUBLIC_KEY"], "$(params.PUBLIC_KEY)")
        self.assertEqual(values["CERTIFICATE_OIDC_ISSUER"], "$(tasks.collect-keyless-params.results.defaultOIDCIssuer)")
        self.assertEqual(values["CERTIFICATE_IDENTITY"], "$(tasks.collect-keyless-params.results.tektonChainsIdentity)")
        self.assertEqual(values["TUF_MIRROR"], "$(tasks.collect-keyless-params.results.tufUrl)")
        self.assertEqual(values["REKOR_HOST"], "$(tasks.collect-keyless-params.results.rekorUrl)")
        self.assertEqual(values["IGNORE_REKOR"], "true")
        self.assertEqual(values["EXTRA_RULE_DATA"], "$(params.EXTRA_RULE_DATA)")
        self.assertTrue({"resolve-mvo-snapshot", "collect-keyless-params"}.issubset(set(verify.get("runAfter", []))))
        for name, task_name in [("verify", "verify-enterprise-contract"), ("collect-keyless-params", "collect-keyless-params")]:
            ref = tasks[name]["taskRef"]
            self.assertEqual(ref["resolver"], "bundles")
            params = {param["name"]: param["value"] for param in ref["params"]}
            self.assertEqual(params, {"bundle": EC_BUNDLE, "name": task_name, "kind": "task"})
        self.assertEqual(next(result["value"] for result in self.pipeline["spec"]["results"] if result["name"] == "TEST_OUTPUT"), "$(tasks.verify.results.TEST_OUTPUT)")
        self.assertRegex(self.step["image"], r"^quay\.io/konflux-ci/konflux-test:[^@]+@sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
