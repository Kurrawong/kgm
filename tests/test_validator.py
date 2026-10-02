from pathlib import Path

import pytest
from typer.testing import CliRunner

from kgm import validate
from kgm.cli import app
from kgm.validator import ManifestValidationError

runner = CliRunner()


def test_validator_valid():
    assert validate(Path(__file__).parent / "demo-vocabs" / "manifest.ttl")


def test_validator_invalid_01():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(Path(__file__).parent / "demo-vocabs" / "manifest-invalid-01.ttl")
    assert "The manifest file is invalid" in str(exc_info.value)


def test_validator_invalid_03():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(Path(__file__).parent / "demo-vocabs" / "manifest-invalid-02.ttl")
    assert str(exc_info.value) == "The content link vocabz/*.ttl is not a directory"


def test_validator_invalid_02():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(Path(__file__).parent / "demo-vocabs" / "manifest-invalid-03.ttl")
    assert (
        str(exc_info.value)
        == "Remote content link non-resolving: https://raw.githubusercontent.com/RDFLib/prez/refs/heads/main/prez/reference_data/profiles/ogc_records_profile.ttlx"
    )


def test_validator_valid_multi():
    assert validate(Path(__file__).parent / "demo-vocabs" / "manifest-multi.ttl")


def test_validator_valid_main_entity():
    assert validate(Path(__file__).parent / "demo-vocabs" / "manifest-mainEntity.ttl")


def test_validator_invalid_main_entity():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(
            Path(__file__).parent / "demo-vocabs" / "manifest-mainEntity-invalid.ttl"
        )
    assert "N04" in str(exc_info.value)


def test_validator_invalid_main_entity2():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(
            Path(__file__).parent / "demo-vocabs" / "manifest-mainEntity-invalid2.ttl"
        )
    assert "N04" in str(exc_info.value)


def test_validator_valid_conformance():
    assert validate(Path(__file__).parent / "demo-vocabs" / "manifest-conformance.ttl")


def test_validator_valid_conformance_local():
    assert validate(
        Path(__file__).parent / "demo-vocabs" / "manifest-conformance-local.ttl"
    )


def test_validator_invalid_conformance_local():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(
            Path(__file__).parent / "demo-vocabs" / "manifest-conformance-local-invalid.ttl"
        )
    assert "Message: Requirement 2.1.4, 2.2.1 or 2.3.1" in str(exc_info.value)


def test_validator_valid_conformance_all():
    # language-test.ttl is known to have 6 errors according to VocPub 4.10, image-test.ttl none
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(Path(__file__).parent / "demo-vocabs" / "manifest-conformance-all.ttl")
    assert "Results (8)" in str(exc_info.value)


def test_validator_invalid_conformance_all():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(
            Path(__file__).parent
            / "demo-vocabs"
            / "manifest-conformance-all-local-invalid.ttl"
        )
    assert "Results (1)" in str(exc_info.value)


def test_own_validator():
    m = Path(__file__).parent / "validator/manifest-conformance-own.ttl"
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(m)
    assert "Results (5)" in str(exc_info.value)


def test_validator_cli():
    result = runner.invoke(
        app,
        [
            "validate",
            str(Path(__file__).parent / "demo-vocabs" / "manifest-invalid-01.ttl"),
        ],
    )
    assert result.exit_code != 0
    assert "MinCountConstraintComponent" in str(result.exception)


def test_validator_invalid_conformance_missing():
    with pytest.raises(ManifestValidationError) as exc_info:
        validate(
            Path(__file__).parent
            / "demo-vocabs"
            / "manifest-conformance-local-missing.ttl"
        )
    assert "could not be found" in str(exc_info.value)


def test_error_reporting():
    m = Path(__file__).parent / "validator/manifest-syntax-error.ttl"
    with pytest.raises(SyntaxError) as exc_info:
        validate(m)
    assert "Failed to load " in str(exc_info.value)
