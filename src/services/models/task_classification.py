"""Strict task classification boundary that cannot select a callable."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

SUPPORTED_SCHEMA_MAJOR = 1
SCHEMA_VERSION = "1.0.0"
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "task_classification.schema.json"
)
TAXONOMY_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "003-model-scan-integration"
    / "registry"
    / "task-taxonomy.v1.json"
)

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_CAPABILITY = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_TAXONOMY_FIELDS = {
    "schema_version",
    "version",
    "taxonomy_id",
    "families",
    "classes",
    "legacy_tag_dispositions",
    "class_aliases",
    "source_provenance",
}
_CLASS_FIELDS = {
    "task_class",
    "label",
    "task_family",
    "threshold_rank",
    "validation_gates",
    "required_capabilities",
    "source_provenance",
    "mapping_rationale",
}
_LEGACY_TAG_FIELDS = {
    "task_tag",
    "task_family",
    "disposition",
    "default_task_class",
    "rationale",
}
_INFERENCE_COMMON_FIELDS = {
    "classifier_version",
    "input_ref",
    "required_capabilities",
    "privacy_class",
    "importance",
    "confidence",
    "decision_provenance",
}


class ClassificationRejected(ValueError):
    """Raised when a classification cannot safely enter routing policy."""


@dataclass(frozen=True)
class TaskTaxonomy:
    version: str
    class_to_family: Mapping[str, str]
    taxonomy_id: str = ""
    legacy_tags: Mapping[str, tuple[str, str | None]] = field(
        default_factory=lambda: MappingProxyType({})
    )
    class_aliases: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    source_provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskClassification:
    schema_version: str
    classification_id: str
    classified_at: str
    classifier_version: str
    taxonomy_version: str
    input_ref: str
    task_class: str
    task_family: str
    required_capabilities: tuple[str, ...]
    privacy_class: str
    importance: str
    confidence: float
    decision_provenance: tuple[str, ...]


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _major(version: str) -> int | None:
    try:
        return int(version.split(".", 1)[0])
    except (AttributeError, ValueError):
        return None


def _canonical_payload(classification: dict[str, Any]) -> bytes:
    payload = dict(classification)
    payload.pop("classification_id", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _classification_id(classification: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_payload(classification)).hexdigest()


def _exact_fields(value: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ClassificationRejected(f"{label} must be an object")
    if set(value) != expected:
        raise ClassificationRejected(f"{label} fields do not match the contract")
    return value


def _unique_strings(
    values: Any,
    label: str,
    *,
    pattern: re.Pattern[str] | None = None,
) -> tuple[str, ...]:
    if (
        not isinstance(values, list)
        or not values
        or any(
            not isinstance(value, str)
            or not value
            or (pattern is not None and pattern.fullmatch(value) is None)
            for value in values
        )
        or len(set(values)) != len(values)
    ):
        raise ClassificationRejected(f"{label} must be unique nonempty strings")
    return tuple(values)


def _taxonomy_id(data: Mapping[str, Any]) -> str:
    payload = dict(data)
    payload.pop("taxonomy_id", None)
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def load_taxonomy(path: Path = TAXONOMY_PATH) -> TaskTaxonomy:
    """Load and validate the one active, content-addressed task taxonomy."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClassificationRejected(f"cannot load task taxonomy: {exc}") from exc
    data = _exact_fields(raw, _TAXONOMY_FIELDS, "taxonomy")
    if (
        data["schema_version"] != "1.0.0"
        or not isinstance(data["version"], str)
        or not data["version"]
        or not isinstance(data["taxonomy_id"], str)
    ):
        raise ClassificationRejected("invalid taxonomy identity")

    families = _unique_strings(data["families"], "taxonomy families", pattern=_IDENTIFIER)
    if len(families) != 10:
        raise ClassificationRejected("active taxonomy must contain 10 families")
    family_set = set(families)

    if not isinstance(data["classes"], list) or len(data["classes"]) != 19:
        raise ClassificationRejected("active taxonomy must contain 19 classes")
    class_to_family: dict[str, str] = {}
    for raw_entry in data["classes"]:
        entry = _exact_fields(raw_entry, _CLASS_FIELDS, "task class")
        task_class = entry["task_class"]
        task_family = entry["task_family"]
        if (
            not isinstance(task_class, str)
            or _IDENTIFIER.fullmatch(task_class) is None
            or task_class in class_to_family
            or not isinstance(task_family, str)
            or task_family not in family_set
            or not isinstance(entry["label"], str)
            or not entry["label"]
            or not isinstance(entry["threshold_rank"], int)
            or isinstance(entry["threshold_rank"], bool)
            or not 1 <= entry["threshold_rank"] <= 18
            or not isinstance(entry["mapping_rationale"], str)
            or not entry["mapping_rationale"]
        ):
            raise ClassificationRejected("invalid task class")
        _unique_strings(
            entry["validation_gates"],
            f"{task_class} validation_gates",
            pattern=_IDENTIFIER,
        )
        _unique_strings(
            entry["required_capabilities"],
            f"{task_class} required_capabilities",
            pattern=_CAPABILITY,
        )
        _unique_strings(entry["source_provenance"], f"{task_class} source_provenance")
        class_to_family[task_class] = task_family

    dispositions = data["legacy_tag_dispositions"]
    if not isinstance(dispositions, list) or len(dispositions) != 10:
        raise ClassificationRejected(
            "active taxonomy must contain 10 legacy tag dispositions"
        )
    legacy_tags: dict[str, tuple[str, str | None]] = {}
    for raw_entry in dispositions:
        entry = _exact_fields(raw_entry, _LEGACY_TAG_FIELDS, "legacy tag disposition")
        task_tag = entry["task_tag"]
        task_family = entry["task_family"]
        disposition = entry["disposition"]
        default_task_class = entry["default_task_class"]
        if (
            not isinstance(task_tag, str)
            or _IDENTIFIER.fullmatch(task_tag) is None
            or task_tag in legacy_tags
            or task_family not in family_set
            or disposition not in {"exact_default", "family_only"}
            or not isinstance(entry["rationale"], str)
            or not entry["rationale"]
        ):
            raise ClassificationRejected("invalid legacy tag disposition")
        if disposition == "family_only":
            if default_task_class is not None:
                raise ClassificationRejected(
                    "ambiguous legacy tag cannot define a default class"
                )
        elif (
            not isinstance(default_task_class, str)
            or class_to_family.get(default_task_class) != task_family
        ):
            raise ClassificationRejected(
                "exact legacy tag must name a class in its family"
            )
        legacy_tags[task_tag] = (disposition, default_task_class)
    if set(legacy_tags) != family_set:
        raise ClassificationRejected(
            "legacy tag dispositions must cover every family exactly once"
        )

    aliases = data["class_aliases"]
    if not isinstance(aliases, dict):
        raise ClassificationRejected("class_aliases must be an object")
    for alias, canonical in aliases.items():
        if (
            not isinstance(alias, str)
            or _IDENTIFIER.fullmatch(alias) is None
            or not isinstance(canonical, str)
            or _IDENTIFIER.fullmatch(canonical) is None
            or alias in class_to_family
            or canonical not in class_to_family
        ):
            raise ClassificationRejected("invalid task class alias")

    provenance = _unique_strings(data["source_provenance"], "taxonomy provenance")
    if data["taxonomy_id"] != _taxonomy_id(data):
        raise ClassificationRejected("taxonomy_id does not match canonical content")
    return TaskTaxonomy(
        version=data["version"],
        taxonomy_id=data["taxonomy_id"],
        class_to_family=MappingProxyType(class_to_family),
        legacy_tags=MappingProxyType(legacy_tags),
        class_aliases=MappingProxyType(dict(aliases)),
        source_provenance=provenance,
    )


@lru_cache(maxsize=1)
def active_taxonomy() -> TaskTaxonomy:
    return load_taxonomy()


def resolve_task_class(task_class: str, taxonomy: TaskTaxonomy) -> str:
    canonical = taxonomy.class_aliases.get(task_class, task_class)
    if canonical not in taxonomy.class_to_family:
        raise ClassificationRejected(f"unknown task_class {task_class}")
    return canonical


def resolve_legacy_tag(task_tag: str, taxonomy: TaskTaxonomy) -> str:
    disposition = taxonomy.legacy_tags.get(task_tag)
    if disposition is None:
        raise ClassificationRejected(f"unknown legacy task_tag {task_tag}")
    status, default_task_class = disposition
    if status != "exact_default" or default_task_class is None:
        raise ClassificationRejected(
            f"ambiguous legacy task_tag {task_tag} requires an exact task_class"
        )
    return default_task_class


def build_draft_from_inference(
    inference: Any,
    taxonomy: TaskTaxonomy,
) -> dict[str, Any]:
    """Convert model inference into a strict draft without route authority."""
    if not isinstance(inference, dict):
        raise ClassificationRejected("classifier inference must be an object")
    has_task_class = "task_class" in inference
    has_task_tag = "task_tag" in inference
    if has_task_class == has_task_tag:
        raise ClassificationRejected(
            "classifier inference must contain exactly one of task_class or task_tag"
        )
    selector = "task_class" if has_task_class else "task_tag"
    _exact_fields(inference, _INFERENCE_COMMON_FIELDS | {selector}, "classifier inference")
    task_class = (
        resolve_task_class(inference["task_class"], taxonomy)
        if has_task_class
        else resolve_legacy_tag(inference["task_tag"], taxonomy)
    )
    return {
        "classifier_version": inference["classifier_version"],
        "input_ref": inference["input_ref"],
        "task_class": task_class,
        "task_family": taxonomy.class_to_family[task_class],
        "required_capabilities": tuple(inference["required_capabilities"]),
        "privacy_class": inference["privacy_class"],
        "importance": inference["importance"],
        "confidence": inference["confidence"],
        "decision_provenance": tuple(inference["decision_provenance"]),
    }


def validate(data: Any, taxonomy: TaskTaxonomy) -> None:
    """Validate shape, content identity, and exact taxonomy membership."""
    if not isinstance(data, dict):
        raise ClassificationRejected("classification must be an object")
    errors = sorted(_validator().iter_errors(data), key=lambda error: list(error.path))
    if errors:
        raise ClassificationRejected(errors[0].message)
    if _major(data["schema_version"]) != SUPPORTED_SCHEMA_MAJOR:
        raise ClassificationRejected(f"unsupported schema version {data['schema_version']}")
    if data["classification_id"] != _classification_id(data):
        raise ClassificationRejected("classification_id does not match canonical content")
    if data["taxonomy_version"] != taxonomy.version:
        raise ClassificationRejected(f"taxonomy version {data['taxonomy_version']} is not active")

    expected_family = taxonomy.class_to_family.get(data["task_class"])
    if expected_family is None:
        raise ClassificationRejected(f"unknown task_class {data['task_class']}")
    if data["task_family"] != expected_family:
        raise ClassificationRejected(
            f"task_family {data['task_family']} does not match " f"{data['task_class']}"
        )


def build_classification(
    *,
    classified_at: str,
    classifier_version: str,
    input_ref: str,
    task_class: str,
    task_family: str,
    required_capabilities: tuple[str, ...],
    privacy_class: str,
    importance: str,
    confidence: float,
    decision_provenance: tuple[str, ...],
    taxonomy: TaskTaxonomy,
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    """Build classification evidence only; no callable identity is accepted."""
    data: dict[str, Any] = {
        "schema_version": schema_version,
        "classification_id": "",
        "classified_at": classified_at,
        "classifier_version": classifier_version,
        "taxonomy_version": taxonomy.version,
        "input_ref": input_ref,
        "task_class": task_class,
        "task_family": task_family,
        "required_capabilities": list(required_capabilities),
        "privacy_class": privacy_class,
        "importance": importance,
        "confidence": confidence,
        "decision_provenance": list(decision_provenance),
    }
    data["classification_id"] = _classification_id(data)
    validate(data, taxonomy)
    return data


def from_data(data: Any, taxonomy: TaskTaxonomy) -> TaskClassification:
    validate(data, taxonomy)
    return TaskClassification(
        schema_version=data["schema_version"],
        classification_id=data["classification_id"],
        classified_at=data["classified_at"],
        classifier_version=data["classifier_version"],
        taxonomy_version=data["taxonomy_version"],
        input_ref=data["input_ref"],
        task_class=data["task_class"],
        task_family=data["task_family"],
        required_capabilities=tuple(data["required_capabilities"]),
        privacy_class=data["privacy_class"],
        importance=data["importance"],
        confidence=data["confidence"],
        decision_provenance=tuple(data["decision_provenance"]),
    )
