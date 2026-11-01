"""Tests for pgfn-fetcher Typer plugin."""

from typer.testing import CliRunner

from pgfn_fetcher.plugin import app


def test_cli_list() -> None:
    """Test quantilica pgfn list."""
    runner = CliRunner()
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "sida" in result.output
    assert "previdenciario" in result.output
    assert "fgts" in result.output


def test_cli_convert_help() -> None:
    """Test quantilica pgfn convert --help."""
    runner = CliRunner()
    result = runner.invoke(app, ["convert", "--help"])
    assert result.exit_code == 0
    assert "--lake" in result.output
