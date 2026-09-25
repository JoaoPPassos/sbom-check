"""Regression tests for the CycloneDX fixture corpus."""

import json
from pathlib import Path

import pytest

from cyclone_validator import CycloneDXValidationEngine, JsonSchemaValidator

FIXTURES = Path(__file__).parents[2] / "fixtures" / "cyclonedx"
VERSIONS = ("1.3", "1.4", "1.5", "1.6", "1.7")


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("version", VERSIONS)
def test_valid_fixture_passes_declared_schema(version: str) -> None:
    """Each supported version is validated against its declared schema."""
    document = _load_fixture(f"valid-{version}.json")

    result = JsonSchemaValidator().validate(document, version)

    assert result.is_valid
    assert result.messages == []


@pytest.mark.parametrize("version", VERSIONS)
def test_invalid_fixture_reports_all_schema_failures(version: str) -> None:
    """Each invalid fixture reports both component defects with paths."""
    document = _load_fixture(f"invalid-{version}.json")

    result = CycloneDXValidationEngine().validate_dict(document)

    assert not result.is_valid
    assert {message.field_path for message in result.messages} >= {
        "$.components[0].type",
        "$.components[1].name",
    }
    assert all(message.rule_id == "cyclonedx_schema_error" for message in result.messages if message.rule_id != "semantic_validation_skipped")


def test_representative_scancode_fixture_passes() -> None:
    """The representative ScanCode-shaped document remains schema-valid."""
    document = _load_fixture("representative-scancode-1.3.json")

    result = CycloneDXValidationEngine().validate_dict(document)

    assert result.is_valid
    assert result.messages == []
