"""Tests for the standalone CycloneDX validation CLI."""

import json
from pathlib import Path

from click.testing import CliRunner

from cyclone_validator.cli import main

FIXTURES = Path(__file__).parents[2] / "fixtures" / "cyclonedx"


def invoke_cli(*arguments: str):
    """Invoke the CLI through Click's test runner."""
    return CliRunner().invoke(main, list(arguments))


def test_help_describes_cyclonedx_validation():
    result = invoke_cli("--help")

    assert result.exit_code == 0
    assert "Validate CycloneDX JSON documents" in result.output
    assert "--output-format" in result.output
    assert "--recursive" in result.output


def test_valid_document_passes_schema_validation():
    result = invoke_cli(
        "--output-format",
        "json",
        str(FIXTURES / "valid-1.7.json"),
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"] == {"total_files": 1, "valid_files": 1, "invalid_files": 0}
    assert payload["results"][0]["is_valid"] is True
    assert payload["results"][0]["messages"] == []


def test_invalid_document_reports_schema_paths():
    result = invoke_cli(
        "--output-format",
        "json",
        str(FIXTURES / "invalid-1.7.json"),
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    validation_result = payload["results"][0]
    assert validation_result["is_valid"] is False
    assert {message["field_path"] for message in validation_result["messages"]} == {
        "$.components[0].type",
        "$.components[1].name",
    }
    assert all(
        message["rule_id"] == "cyclonedx_schema_error"
        for message in validation_result["messages"]
    )


def test_unsupported_version_is_reported_as_structured_error(tmp_path):
    document = json.loads((FIXTURES / "valid-1.7.json").read_text())
    document["specVersion"] = "1.2"
    document_path = tmp_path / "unsupported.json"
    document_path.write_text(json.dumps(document))

    result = invoke_cli("--output-format", "json", str(document_path))

    assert result.exit_code == 1
    payload = json.loads(result.output)
    message = payload["results"][0]["messages"][0]
    assert message["rule_id"] == "unsupported_version"
    assert "1.2" in message["message"]


def test_recursive_validation_reports_summary_counts(tmp_path):
    input_directory = tmp_path / "documents"
    input_directory.mkdir()
    (input_directory / "valid.json").write_bytes(
        (FIXTURES / "valid-1.6.json").read_bytes()
    )
    (input_directory / "invalid.json").write_bytes(
        (FIXTURES / "invalid-1.6.json").read_bytes()
    )

    result = invoke_cli(
        "--recursive",
        "--output-format",
        "json",
        str(input_directory),
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["summary"] == {"total_files": 2, "valid_files": 1, "invalid_files": 1}
    assert [Path(item["file"]).name for item in payload["results"]] == [
        "invalid.json",
        "valid.json",
    ]

