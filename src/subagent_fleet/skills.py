from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path


class SkillInstallError(ValueError):
    """Raised when bundled assistant skills cannot be installed."""


@dataclass(frozen=True, slots=True)
class AssistantTarget:
    name: str
    directory: Path
    description: str


@dataclass(frozen=True, slots=True)
class BundledSkill:
    name: str
    description: str
    template_name: str


@dataclass(frozen=True, slots=True)
class SkillInstallResult:
    target: str
    skill: str
    path: Path
    written: bool


ASSISTANT_TARGETS: dict[str, AssistantTarget] = {
    "claude-code": AssistantTarget(
        name="claude-code",
        directory=Path(".claude") / "skills",
        description="Project-local Claude Code skills.",
    ),
    "codex": AssistantTarget(
        name="codex",
        directory=Path(".codex") / "skills",
        description="Project-local Codex skills.",
    ),
    "opencode": AssistantTarget(
        name="opencode",
        directory=Path(".opencode") / "skills",
        description="Project-local OpenCode skills.",
    ),
}

BUNDLED_SKILLS: dict[str, BundledSkill] = {
    "subagent-fleet-bootstrap": BundledSkill(
        name="subagent-fleet-bootstrap",
        description="Install the subagent-fleet CLI first, then set up assistant skills and fleet config.",
        template_name="subagent-fleet-bootstrap.md",
    ),
    "subagent-fleet-setup": BundledSkill(
        name="subagent-fleet-setup",
        description="Set up, validate, generate, and verify a local subagent fleet.",
        template_name="subagent-fleet-setup.md",
    ),
    "subagent-fleet-operations": BundledSkill(
        name="subagent-fleet-operations",
        description="Use and troubleshoot an existing generated subagent fleet.",
        template_name="subagent-fleet-operations.md",
    ),
}


def install_skills(
    *,
    output_root: Path,
    targets: list[str],
    skills: list[str],
    force: bool = False,
) -> list[SkillInstallResult]:
    resolved_targets = resolve_targets(targets)
    resolved_skills = resolve_skills(skills)
    results: list[SkillInstallResult] = []
    for target in resolved_targets:
        for skill in resolved_skills:
            content = load_skill_template(skill)
            path = output_root / target.directory / skill.name / "SKILL.md"
            if path.exists() and not force:
                raise FileExistsError(f"{path} already exists; use --force to overwrite")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            results.append(SkillInstallResult(target=target.name, skill=skill.name, path=path, written=True))
    return results


def resolve_targets(values: list[str] | None) -> list[AssistantTarget]:
    names = _split_values(values or ["all"])
    if "all" in names:
        if len(names) > 1:
            raise SkillInstallError("Use either all or specific targets, not both")
        return list(ASSISTANT_TARGETS.values())
    unknown = sorted(set(names) - set(ASSISTANT_TARGETS))
    if unknown:
        raise SkillInstallError(f"unknown target: {', '.join(unknown)}")
    return [ASSISTANT_TARGETS[name] for name in names]


def resolve_skills(values: list[str] | None) -> list[BundledSkill]:
    names = _split_values(values or ["all"])
    if "all" in names:
        if len(names) > 1:
            raise SkillInstallError("Use either all or specific skills, not both")
        return list(BUNDLED_SKILLS.values())
    unknown = sorted(set(names) - set(BUNDLED_SKILLS))
    if unknown:
        raise SkillInstallError(f"unknown skill: {', '.join(unknown)}")
    return [BUNDLED_SKILLS[name] for name in names]


def load_skill_template(skill: BundledSkill) -> str:
    return (
        resources.files("subagent_fleet")
        .joinpath("skill_templates")
        .joinpath(skill.template_name)
        .read_text()
    )


def _split_values(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                names.append(item)
    if not names:
        raise SkillInstallError("at least one value is required")
    return names
