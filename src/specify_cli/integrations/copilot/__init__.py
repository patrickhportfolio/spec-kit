"""Copilot integration — GitHub Copilot in VS Code.

Copilot uses a single orchestrator agent (``speckit.agent.md``) that routes
user intent to skills (``speckit-<name>/SKILL.md`` in ``.github/skills/``).

- The orchestrator lives at ``.github/agents/speckit.agent.md``
- Skills use the ``speckit-<name>/SKILL.md`` layout in ``.github/skills/``
- Installs ``.vscode/settings.json`` with terminal auto-approve paths
- Context file lives at ``.github/copilot-instructions.md``
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from ..base import IntegrationBase
from ..manifest import IntegrationManifest


class CopilotIntegration(IntegrationBase):
    """Integration for GitHub Copilot in VS Code."""

    key = "copilot"
    config = {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".github/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = ".github/copilot-instructions.md"

    def command_filename(self, template_name: str) -> str:
        """Copilot skills use ``speckit-<name>/SKILL.md`` layout."""
        return f"speckit-{template_name}/SKILL.md"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install orchestrator agent, skills, and VS Code settings.

        Creates:
        1. ``.github/agents/speckit.agent.md`` — single orchestrator
        2. ``.github/skills/speckit-<name>/SKILL.md`` — one per command template
        3. ``.vscode/settings.json`` — terminal auto-approve settings
        4. Integration-specific update-context scripts
        """
        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        templates = self.list_command_templates()
        if not templates:
            return []

        created: list[Path] = []
        script_type = opts.get("script_type", "sh")
        arg_placeholder = self.registrar_config.get("args", "$ARGUMENTS")

        # 1. Generate the orchestrator agent file
        created.extend(self._install_orchestrator(project_root, manifest))

        # 2. Generate skills from command templates
        skills_dir = project_root / ".github" / "skills"
        skills_dir_resolved = skills_dir.resolve()
        try:
            skills_dir_resolved.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Skills destination {skills_dir_resolved} escapes "
                f"project root {project_root_resolved}"
            ) from exc

        for src_file in templates:
            command_name = src_file.stem
            skill_name = f"speckit-{command_name.replace('.', '-')}"

            # Parse original frontmatter for description
            raw = src_file.read_text(encoding="utf-8")
            frontmatter: dict[str, Any] = {}
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1])
                        if isinstance(fm, dict):
                            frontmatter = fm
                    except yaml.YAMLError:
                        pass

            # Process body through standard template pipeline
            processed_body = self.process_template(
                raw, self.key, script_type, arg_placeholder
            )
            # Strip processed frontmatter — we rebuild it for skills
            if processed_body.startswith("---"):
                parts = processed_body.split("---", 2)
                if len(parts) >= 3:
                    processed_body = parts[2]

            description = frontmatter.get("description", "")
            if not description:
                description = f"Spec Kit: {command_name} workflow"

            # Build SKILL.md with simplified frontmatter
            skill_content = (
                f"---\n"
                f"name: {skill_name}\n"
                f"description: >\n"
                f"  {description}\n"
                f"allowed-tools: shell\n"
                f"---\n"
                f"{processed_body}"
            )

            skill_dir = skills_dir / skill_name
            skill_file = skill_dir / "SKILL.md"
            dst = self.write_file_and_record(
                skill_content, skill_file, project_root, manifest
            )
            created.append(dst)

        # 3. Write .vscode/settings.json
        settings_src = self._vscode_settings_path()
        if settings_src and settings_src.is_file():
            dst_settings = project_root / ".vscode" / "settings.json"
            dst_settings.parent.mkdir(parents=True, exist_ok=True)
            if dst_settings.exists():
                self._merge_vscode_settings(settings_src, dst_settings)
            else:
                shutil.copy2(settings_src, dst_settings)
                self.record_file_in_manifest(dst_settings, project_root, manifest)
                created.append(dst_settings)

        # 4. Install integration-specific update-context scripts
        created.extend(self.install_scripts(project_root, manifest))

        return created

    def _install_orchestrator(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> list[Path]:
        """Install the orchestrator agent file from the template."""
        tpl_dir = self.shared_templates_dir()
        if not tpl_dir:
            return []

        orchestrator_src = tpl_dir / "orchestrator.md"
        if not orchestrator_src.is_file():
            return []

        content = orchestrator_src.read_text(encoding="utf-8")
        agents_dir = project_root / ".github" / "agents"
        dst = self.write_file_and_record(
            content, agents_dir / "speckit.agent.md", project_root, manifest
        )
        return [dst]

    def _vscode_settings_path(self) -> Path | None:
        """Return path to the bundled vscode-settings.json template."""
        tpl_dir = self.shared_templates_dir()
        if tpl_dir:
            candidate = tpl_dir / "vscode-settings.json"
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _merge_vscode_settings(src: Path, dst: Path) -> None:
        """Merge settings from *src* into existing *dst* JSON file.

        Top-level keys from *src* are added only if missing in *dst*.
        For dict-valued keys, sub-keys are merged the same way.

        If *dst* cannot be parsed (e.g. JSONC with comments), the merge
        is skipped to avoid overwriting user settings.
        """
        try:
            existing = json.loads(dst.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            import logging
            template_content = src.read_text(encoding="utf-8")
            logging.getLogger(__name__).warning(
                "Could not parse %s (may contain JSONC comments). "
                "Skipping settings merge to preserve existing file.\n"
                "Please add the following settings manually:\n%s",
                dst, template_content,
            )
            return

        new_settings = json.loads(src.read_text(encoding="utf-8"))

        if not isinstance(existing, dict) or not isinstance(new_settings, dict):
            import logging
            logging.getLogger(__name__).warning(
                "Skipping settings merge: %s or template is not a JSON object.", dst
            )
            return

        changed = False
        for key, value in new_settings.items():
            if key not in existing:
                existing[key] = value
                changed = True
            elif isinstance(existing[key], dict) and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in existing[key]:
                        existing[key][sub_key] = sub_value
                        changed = True

        if not changed:
            return

        dst.write_text(
            json.dumps(existing, indent=4) + "\n", encoding="utf-8"
        )
