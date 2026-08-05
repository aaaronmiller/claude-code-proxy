"""Explicit identity mapping excludes unresolved and ambiguous names."""

import copy
import json
from pathlib import Path

from src.services.models.callable_catalog import from_data as catalog_from_data
from src.services.models.callable_identity import (
    from_data as identity_from_data,
    load,
    resolve,
)

FIXTURES = Path(__file__).parent / "fixtures" / "catalogs"


def _catalog_data():
    return json.loads((FIXTURES / "valid_callable_catalog.json").read_text(encoding="utf-8"))


def _identity_data():
    return json.loads(
        (FIXTURES / "valid_callable_identity_mapping.json").read_text(encoding="utf-8")
    )


def test_exact_mapping_resolves_callable_record():
    catalog = catalog_from_data(_catalog_data())
    identity_map = load(FIXTURES / "valid_callable_identity_mapping.json")
    assert catalog is not None and identity_map is not None

    result = resolve(["benchmark:qwen3-coder-free"], catalog, identity_map)
    assert result.excluded == ()
    assert result.resolved[0][1].api_model_id == "qwen/qwen3-coder:free"


def test_similar_display_name_is_not_inferred():
    catalog = catalog_from_data(_catalog_data())
    identity_map = identity_from_data(_identity_data())
    assert catalog is not None and identity_map is not None

    result = resolve(["Qwen 3 Coder Free"], catalog, identity_map)
    assert result.resolved == ()
    assert result.excluded[0].reason == "unresolved-identity"


def test_ambiguous_mapping_is_excluded():
    catalog_data = _catalog_data()
    second = copy.deepcopy(catalog_data["records"][0])
    second["callable_id"] = "openrouter:qwen/qwen3-coder:free:secondary"
    second["credential_ref"] = "OPENROUTER_SECONDARY_API_KEY"
    catalog_data["records"].append(second)
    catalog = catalog_from_data(catalog_data)

    identity_data = _identity_data()
    duplicate = copy.deepcopy(identity_data["mappings"][0])
    duplicate["callable_id"] = second["callable_id"]
    identity_data["mappings"].append(duplicate)
    identity_map = identity_from_data(identity_data)
    assert catalog is not None and identity_map is not None

    result = resolve(["benchmark:qwen3-coder-free"], catalog, identity_map)
    assert result.resolved == ()
    assert result.excluded[0].reason == "ambiguous-identity"
    assert len(result.excluded[0].candidates) == 2


def test_missing_and_unreachable_callable_are_excluded():
    catalog = catalog_from_data(_catalog_data())
    identity_data = _identity_data()
    identity_data["mappings"][0]["callable_id"] = "missing"
    identity_map = identity_from_data(identity_data)
    assert catalog is not None and identity_map is not None
    assert (
        resolve(["benchmark:qwen3-coder-free"], catalog, identity_map).excluded[0].reason
        == "missing-callable"
    )

    unreachable_data = _catalog_data()
    unreachable_data["records"][0]["reachable"] = False
    unreachable = catalog_from_data(unreachable_data)
    identity_map = identity_from_data(_identity_data())
    assert unreachable is not None and identity_map is not None
    assert (
        resolve(["benchmark:qwen3-coder-free"], unreachable, identity_map).excluded[0].reason
        == "unreachable-callable"
    )
