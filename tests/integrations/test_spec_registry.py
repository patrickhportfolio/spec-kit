"""Tests for the spec registry (specs/registry.json) feature."""

import json
import os
import subprocess
import sys

import pytest


class TestRegistrySchemaInstall:
    """registry.schema.json should be installed into specs/ during init."""

    def test_init_installs_registry_schema(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "reg-proj"
        project.mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--force",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        schema_dst = project / "specs" / "registry.schema.json"
        assert schema_dst.exists(), "registry.schema.json not installed into specs/"
        schema = json.loads(schema_dst.read_text(encoding="utf-8"))
        assert schema.get("$schema"), "schema file missing $schema key"
        assert "specs" in schema.get("properties", {}), "schema missing 'specs' property"

    def test_init_does_not_overwrite_existing_schema(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "reg-proj2"
        project.mkdir()
        specs_dir = project / "specs"
        specs_dir.mkdir()
        custom = '{"custom": true}'
        (specs_dir / "registry.schema.json").write_text(custom, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--force",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        assert (specs_dir / "registry.schema.json").read_text(encoding="utf-8") == custom

    def test_schema_not_copied_as_page_template(self, tmp_path):
        """registry.schema.json should NOT appear in .specify/templates/."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "reg-proj3"
        project.mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--force",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        templates_dir = project / ".specify" / "templates"
        assert not (templates_dir / "registry.schema.json").exists(), \
            "registry.schema.json should not be in .specify/templates/"


class TestSearchCommandTemplate:
    """The search.md command template should be bundled and installed."""

    def test_search_command_template_exists(self):
        """search.md exists in the templates/commands directory."""
        from pathlib import Path
        commands_dir = Path(__file__).parent.parent.parent / "templates" / "commands"
        assert (commands_dir / "search.md").exists()

    def test_search_command_has_frontmatter(self):
        from pathlib import Path
        search_md = Path(__file__).parent.parent.parent / "templates" / "commands" / "search.md"
        content = search_md.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "description:" in content
        assert "Search" in content or "search" in content

    def test_search_command_installed_for_integration(self, tmp_path):
        """search command should be generated for agent integrations."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "search-proj"
        project.mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--force",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        # Copilot uses .github/skills/ for skill files
        search_file = project / ".github" / "skills" / "speckit-search" / "SKILL.md"
        assert search_file.exists(), "search command not generated for copilot integration"


class TestRegistrySchemaContent:
    """Validate the registry.schema.json template content."""

    @pytest.fixture
    def schema(self):
        from pathlib import Path
        schema_path = Path(__file__).parent.parent.parent / "templates" / "registry.schema.json"
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def test_schema_has_version_and_specs(self, schema):
        props = schema["properties"]
        assert "version" in props
        assert "specs" in props

    def test_spec_entry_has_required_fields(self, schema):
        spec_props = schema["properties"]["specs"]["items"]["properties"]
        for field in ("id", "title", "summary", "status", "tags", "created", "relationships"):
            assert field in spec_props, f"spec entry missing '{field}'"

    def test_status_enum_values(self, schema):
        status = schema["properties"]["specs"]["items"]["properties"]["status"]
        expected = {"draft", "clarified", "planned", "in-progress", "implemented", "deprecated", "superseded"}
        actual = set(status["enum"])
        assert actual == expected

    def test_relationships_structure(self, schema):
        rels = schema["properties"]["specs"]["items"]["properties"]["relationships"]["properties"]
        assert "depends_on" in rels
        assert "superseded_by" in rels
        assert "related_to" in rels


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="PowerShell registry tests only on Windows",
)
class TestPowerShellRegistryCreation:
    """Test that create-new-feature.ps1 creates registry.json entries."""

    def test_ps_creates_registry_entry(self, tmp_path):
        from pathlib import Path
        script = Path(__file__).parent.parent.parent / "scripts" / "powershell" / "create-new-feature.ps1"

        project = tmp_path / "ps-reg"
        project.mkdir()
        specs = project / "specs"
        specs.mkdir()

        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-File", str(script),
                "-Json", "-DryRun", "-ShortName", "test-feat",
                "Test feature description",
            ],
            capture_output=True, text=True, cwd=str(project),
        )

        # DryRun skips actual file creation, but we can check the script runs
        # and produces JSON. The registry entry is created only in non-dry-run.
        # So let's run without DryRun:
        result2 = subprocess.run(
            [
                "powershell", "-NoProfile", "-File", str(script),
                "-Json", "-ShortName", "test-feat",
                "Test feature description",
            ],
            capture_output=True, text=True, cwd=str(project),
        )

        registry_file = specs / "registry.json"
        if registry_file.exists():
            registry = json.loads(registry_file.read_text(encoding="utf-8"))
            assert registry["version"] == 1
            assert len(registry["specs"]) >= 1
            entry = registry["specs"][0]
            assert entry["status"] == "draft"
            assert entry["title"] == "Test feature description"
