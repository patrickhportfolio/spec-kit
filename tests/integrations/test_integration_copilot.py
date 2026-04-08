"""Tests for CopilotIntegration."""

import json
import os

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


class TestCopilotIntegration:
    def test_copilot_key_and_config(self):
        copilot = get_integration("copilot")
        assert copilot is not None
        assert copilot.key == "copilot"
        assert copilot.config["folder"] == ".github/"
        assert copilot.config["commands_subdir"] == "skills"
        assert copilot.registrar_config["extension"] == "/SKILL.md"
        assert copilot.context_file == ".github/copilot-instructions.md"

    def test_command_filename_skill_md(self):
        copilot = get_integration("copilot")
        assert copilot.command_filename("plan") == "speckit-plan/SKILL.md"

    def test_setup_creates_orchestrator(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        orchestrator = tmp_path / ".github" / "agents" / "speckit.agent.md"
        assert orchestrator.exists()
        assert orchestrator in created
        content = orchestrator.read_text(encoding="utf-8")
        assert "Speckit Orchestrator" in content
        assert "speckit-specify" in content

    def test_setup_creates_skills(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            assert f.parent.parent == tmp_path / ".github" / "skills"
            assert f.parent.name.startswith("speckit-")

    def test_setup_does_not_create_prompts(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        prompt_files = [f for f in created if ".prompt.md" in f.name]
        assert len(prompt_files) == 0
        prompts_dir = tmp_path / ".github" / "prompts"
        assert not prompts_dir.exists() or len(list(prompts_dir.iterdir())) == 0

    def test_setup_creates_vscode_settings_new(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        assert copilot._vscode_settings_path() is not None
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        settings = tmp_path / ".vscode" / "settings.json"
        assert settings.exists()
        assert settings in created
        assert any("settings.json" in k for k in m.files)
        data = json.loads(settings.read_text(encoding="utf-8"))
        assert "chat.tools.terminal.autoApprove" in data
        assert "chat.promptFilesRecommendations" not in data

    def test_setup_merges_existing_vscode_settings(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir(parents=True)
        existing = {"editor.fontSize": 14, "custom.setting": True}
        (vscode_dir / "settings.json").write_text(json.dumps(existing, indent=4), encoding="utf-8")
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        settings = tmp_path / ".vscode" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        assert data["editor.fontSize"] == 14
        assert data["custom.setting"] is True
        assert settings not in created
        assert not any("settings.json" in k for k in m.files)

    def test_all_created_files_tracked_in_manifest(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"Created file {rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = copilot.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.install(tmp_path, m)
        m.save()
        modified_file = created[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        removed, skipped = copilot.uninstall(tmp_path, m)
        assert modified_file.exists()
        assert modified_file in skipped

    def test_directory_structure(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        copilot.setup(tmp_path, m)
        # Orchestrator in agents/
        agents_dir = tmp_path / ".github" / "agents"
        assert agents_dir.is_dir()
        agent_files = sorted(agents_dir.glob("speckit.agent.md"))
        assert len(agent_files) == 1
        # Skills in skills/
        skills_dir = tmp_path / ".github" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
        assert len(skill_dirs) == 11
        expected_skills = {
            "speckit-analyze", "speckit-checklist", "speckit-clarify",
            "speckit-constitution", "speckit-implement", "speckit-plan",
            "speckit-retroactive", "speckit-search", "speckit-specify",
            "speckit-tasks", "speckit-taskstoissues",
        }
        actual_skills = {d.name for d in skill_dirs}
        assert actual_skills == expected_skills
        for d in skill_dirs:
            assert (d / "SKILL.md").is_file()

    def test_templates_are_processed(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        copilot.setup(tmp_path, m)
        skills_dir = tmp_path / ".github" / "skills"
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            content = skill_file.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{skill_file} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{skill_file} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{skill_file} has unprocessed {{ARGS}}"
            assert "\nscripts:\n" not in content
            assert "\nagent_scripts:\n" not in content

    def test_skill_frontmatter_format(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        copilot.setup(tmp_path, m)
        skills_dir = tmp_path / ".github" / "skills"
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            content = skill_file.read_text(encoding="utf-8")
            assert content.startswith("---\n")
            assert "name: speckit-" in content
            assert "description:" in content
            assert "allowed-tools: shell" in content
            # Should NOT have SkillsIntegration-style metadata
            assert "compatibility:" not in content
            assert "metadata:" not in content

    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by specify init --integration copilot --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app
        project = tmp_path / "inventory-sh"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        actual = sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file())
        expected = sorted([
            ".github/agents/speckit.agent.md",
            ".github/skills/speckit-analyze/SKILL.md",
            ".github/skills/speckit-checklist/SKILL.md",
            ".github/skills/speckit-clarify/SKILL.md",
            ".github/skills/speckit-constitution/SKILL.md",
            ".github/skills/speckit-implement/SKILL.md",
            ".github/skills/speckit-plan/SKILL.md",
            ".github/skills/speckit-retroactive/SKILL.md",
            ".github/skills/speckit-search/SKILL.md",
            ".github/skills/speckit-specify/SKILL.md",
            ".github/skills/speckit-tasks/SKILL.md",
            ".github/skills/speckit-taskstoissues/SKILL.md",
            ".vscode/settings.json",
            ".specify/integration.json",
            ".specify/init-options.json",
            ".specify/integrations/copilot.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/integrations/copilot/scripts/update-context.ps1",
            ".specify/integrations/copilot/scripts/update-context.sh",
            ".specify/scripts/bash/check-prerequisites.sh",
            ".specify/scripts/bash/common.sh",
            ".specify/scripts/bash/create-new-feature.sh",
            ".specify/scripts/bash/setup-plan.sh",
            ".specify/scripts/bash/update-agent-context.sh",
            ".specify/templates/agent-file-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            ".specify/memory/constitution.md",
            "specs/registry.schema.json",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )

    def test_complete_file_inventory_ps(self, tmp_path):
        """Every file produced by specify init --integration copilot --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app
        project = tmp_path / "inventory-ps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "ps", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        actual = sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file())
        expected = sorted([
            ".github/agents/speckit.agent.md",
            ".github/skills/speckit-analyze/SKILL.md",
            ".github/skills/speckit-checklist/SKILL.md",
            ".github/skills/speckit-clarify/SKILL.md",
            ".github/skills/speckit-constitution/SKILL.md",
            ".github/skills/speckit-implement/SKILL.md",
            ".github/skills/speckit-plan/SKILL.md",
            ".github/skills/speckit-retroactive/SKILL.md",
            ".github/skills/speckit-search/SKILL.md",
            ".github/skills/speckit-specify/SKILL.md",
            ".github/skills/speckit-tasks/SKILL.md",
            ".github/skills/speckit-taskstoissues/SKILL.md",
            ".vscode/settings.json",
            ".specify/integration.json",
            ".specify/init-options.json",
            ".specify/integrations/copilot.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/integrations/copilot/scripts/update-context.ps1",
            ".specify/integrations/copilot/scripts/update-context.sh",
            ".specify/scripts/powershell/check-prerequisites.ps1",
            ".specify/scripts/powershell/common.ps1",
            ".specify/scripts/powershell/create-new-feature.ps1",
            ".specify/scripts/powershell/setup-plan.ps1",
            ".specify/scripts/powershell/update-agent-context.ps1",
            ".specify/templates/agent-file-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            ".specify/memory/constitution.md",
            "specs/registry.schema.json",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
