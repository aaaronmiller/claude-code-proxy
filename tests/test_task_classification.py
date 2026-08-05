"""Classifier output must match the active taxonomy and never select a model."""

import copy
import json

import pytest

from src.services.models.task_classification import (
    ClassificationRejected,
    TAXONOMY_PATH,
    TaskTaxonomy,
    active_taxonomy,
    build_classification,
    build_draft_from_inference,
    from_data,
    load_taxonomy,
    resolve_legacy_tag,
    resolve_task_class,
    validate,
)

TAXONOMY = active_taxonomy()


def _classification(**overrides):
    values = {
        "classified_at": "2026-07-23T13:00:00Z",
        "classifier_version": "adrf:2.0.0",
        "input_ref": "request:sha256:abc",
        "task_class": "single_file_codegen_tests",
        "task_family": "simple_script",
        "required_capabilities": ("tools", "code_edit"),
        "privacy_class": "proprietary",
        "importance": "high",
        "confidence": 0.91,
        "decision_provenance": ("classifier:fixture", "taxonomy:fixture"),
        "taxonomy": TAXONOMY,
    }
    values.update(overrides)
    return build_classification(**values)


def test_build_is_deterministic_and_parses_to_immutable_record():
    first = _classification()
    second = _classification()
    assert first == second
    parsed = from_data(first, TAXONOMY)
    assert parsed.task_class == "single_file_codegen_tests"
    assert parsed.task_family == "simple_script"
    assert parsed.required_capabilities == ("tools", "code_edit")


def test_classification_identity_matches_javascript_publisher_for_unicode_content():
    data = _classification(
        classified_at="2026-07-23T15:00:00Z",
        classifier_version="adrf:unicode",
        input_ref="request:café",
        confidence=0.9,
        decision_provenance=("classifier:café", TAXONOMY.version),
        taxonomy=TAXONOMY,
    )
    assert (
        data["classification_id"]
        == "sha256:5f06b4043728e337d61e5d0f59b1abee8c3810f8eb805fd847a29d505456a328"
    )


def test_active_taxonomy_is_content_addressed_complete_and_immutable():
    loaded = load_taxonomy()
    assert loaded == TAXONOMY
    assert len(loaded.class_to_family) == 19
    assert len(loaded.legacy_tags) == 10
    assert loaded.taxonomy_id == (
        "sha256:ffaa3217691722c7febf79b5317da8788e2e542a9172eaa8f6ed76a3b1a0fd4d"
    )
    with pytest.raises(TypeError):
        loaded.class_to_family["invented"] = "general_answer"


def test_active_taxonomy_covers_every_legacy_tag_with_explicit_disposition():
    assert set(TAXONOMY.legacy_tags) == {
        "general_answer",
        "research_synthesis",
        "simple_script",
        "code_patch",
        "debug_loop",
        "spec_driven_project",
        "data_extraction",
        "benchmark_analysis",
        "artifact_generation",
        "safety_sensitive",
    }
    exact = {
        tag
        for tag, (status, _) in TAXONOMY.legacy_tags.items()
        if status == "exact_default"
    }
    assert exact == {
        "general_answer",
        "research_synthesis",
        "benchmark_analysis",
        "safety_sensitive",
    }


def test_taxonomy_content_mutation_is_rejected(tmp_path):
    source = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    source["classes"][0]["threshold_rank"] = 17
    mutated = tmp_path / "mutated-taxonomy.json"
    mutated.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ClassificationRejected, match="taxonomy_id"):
        load_taxonomy(mutated)


def test_strict_inference_derives_family_and_resolves_known_aliases():
    inference = {
        "classifier_version": "adrf:test",
        "input_ref": "request:sha256:abc",
        "task_class": "single_file_patch",
        "required_capabilities": ["code_generation", "test_execution"],
        "privacy_class": "proprietary",
        "importance": "normal",
        "confidence": 0.9,
        "decision_provenance": ["classifier:test", TAXONOMY.version],
    }
    draft = build_draft_from_inference(inference, TAXONOMY)
    assert draft["task_class"] == "single_file_codegen_tests"
    assert draft["task_family"] == "simple_script"
    assert resolve_task_class("architecture_design", TAXONOMY) == (
        "architecture_schema_design"
    )


def test_legacy_exact_tags_migrate_but_ambiguous_and_unknown_tags_fail_closed():
    assert resolve_legacy_tag("benchmark_analysis", TAXONOMY) == "benchmark_analysis"
    with pytest.raises(ClassificationRejected, match="ambiguous legacy task_tag"):
        resolve_legacy_tag("code_patch", TAXONOMY)
    with pytest.raises(ClassificationRejected, match="unknown legacy task_tag"):
        resolve_legacy_tag("not_a_real_tag", TAXONOMY)


def test_unknown_task_class_is_rejected_instead_of_treated_as_model():
    with pytest.raises(ClassificationRejected, match="unknown task_class"):
        _classification(task_class="qwen3_coder_free")


def test_mismatched_family_is_rejected():
    with pytest.raises(ClassificationRejected, match="does not match"):
        _classification(task_family="research_synthesis")


def test_wrong_taxonomy_version_is_rejected():
    data = _classification()
    wrong = TaskTaxonomy(
        version="taxonomy:next",
        class_to_family=TAXONOMY.class_to_family,
    )
    with pytest.raises(ClassificationRejected, match="not active"):
        validate(data, wrong)


def test_mutation_invalidates_classification_identity():
    data = _classification()
    data["confidence"] = 0.5
    with pytest.raises(ClassificationRejected, match="classification_id"):
        validate(data, TAXONOMY)


@pytest.mark.parametrize("privacy_class", ["public", "proprietary"])
def test_privacy_class_must_be_explicit(privacy_class):
    assert _classification(privacy_class=privacy_class)["privacy_class"] == privacy_class


def test_unlabeled_privacy_has_no_implicit_default():
    with pytest.raises(ClassificationRejected):
        _classification(privacy_class="")


def test_direct_callable_field_is_rejected_even_with_valid_content_id():
    data = copy.deepcopy(_classification())
    data["selected_model_id"] = "openrouter/qwen"
    with pytest.raises(ClassificationRejected):
        validate(data, TAXONOMY)
