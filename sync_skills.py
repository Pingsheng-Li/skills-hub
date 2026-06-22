#!/usr/bin/env python3
"""
Sync a curated set of high-value agent skills into common coding-agent
skill directories.

By default this preserves the old behavior of installing to user-level
directories. Use --scope project to install into dot-directories in another
workspace.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MANIFEST = ".skill-sync-manifest.json"
VERSION = 1


@dataclass(frozen=True)
class Pick:
    path: str
    category: str
    reason: str


@dataclass(frozen=True)
class Target:
    name: str
    project_path: str | None
    user_path: str | None
    kind: str = "dir"  # "dir" syncs whole skill dirs, "file" syncs SKILL.md.


DEFAULT_PICKS: tuple[Pick, ...] = (
    Pick("agent-skills/skills/using-agent-skills", "meta", "Skill discovery and routing."),
    Pick("agent-skills/skills/context-engineering", "meta", "Agent context setup and rule-file hygiene."),
    Pick("agent-skills/skills/source-driven-development", "research", "Grounds framework/library work in official sources."),
    Pick("agent-skills/skills/doubt-driven-development", "research", "Adversarial review for high-stakes decisions."),
    Pick("agent-skills/skills/idea-refine", "planning", "Turns rough ideas into actionable proposals."),
    Pick("agent-skills/skills/interview-me", "planning", "Clarifies underspecified asks before implementation."),
    Pick("agent-skills/skills/spec-driven-development", "planning", "Creates specs before meaningful code changes."),
    Pick("agent-skills/skills/planning-and-task-breakdown", "planning", "Breaks specs into ordered, verifiable tasks."),
    Pick("agent-skills/skills/incremental-implementation", "implementation", "Builds in small, testable slices."),
    Pick("agent-skills/skills/test-driven-development", "implementation", "Test-first feature and bug work."),
    Pick("agent-skills/skills/debugging-and-error-recovery", "implementation", "Systematic root-cause debugging."),
    Pick("agent-skills/skills/api-and-interface-design", "engineering", "Stable APIs, module boundaries, and contracts."),
    Pick("agent-skills/skills/frontend-ui-engineering", "engineering", "Production UI implementation practices."),
    Pick("agent-skills/skills/browser-testing-with-devtools", "verification", "Runtime browser verification with DevTools MCP."),
    Pick("agent-skills/skills/code-review-and-quality", "quality", "Multi-axis code review."),
    Pick("agent-skills/skills/code-simplification", "quality", "Behavior-preserving simplification."),
    Pick("agent-skills/skills/security-and-hardening", "quality", "Security review and hardening workflows."),
    Pick("agent-skills/skills/performance-optimization", "quality", "Measure-first performance work."),
    Pick("agent-skills/skills/ci-cd-and-automation", "operations", "Build, test, and deployment automation."),
    Pick("agent-skills/skills/git-workflow-and-versioning", "operations", "Atomic commits and branch discipline."),
    Pick("agent-skills/skills/deprecation-and-migration", "operations", "Safe migrations and old-system removal."),
    Pick("agent-skills/skills/documentation-and-adrs", "docs", "Decision records and durable documentation."),
    Pick("agent-skills/skills/shipping-and-launch", "operations", "Launch, rollout, monitoring, and rollback checks."),
    Pick("skills-for-engineers/skills/engineering/setup-matt-pocock-skills", "setup", "Seeds repo context used by Matt Pocock engineering skills."),
    Pick("skills-for-engineers/skills/engineering/grill-with-docs", "planning", "Stress-tests plans against domain docs and ADRs."),
    Pick("skills-for-engineers/skills/engineering/improve-codebase-architecture", "architecture", "Finds architecture and testability improvements."),
    Pick("skills-for-engineers/skills/engineering/prototype", "implementation", "Builds throwaway prototypes to validate designs."),
    Pick("skills-for-engineers/skills/engineering/to-prd", "planning", "Converts conversation context into a PRD."),
    Pick("skills-for-engineers/skills/engineering/to-issues", "planning", "Splits plans into independently grabbable issues."),
    Pick("skills-for-engineers/skills/engineering/triage", "operations", "Issue triage workflow."),
    Pick("skills-for-engineers/skills/misc/setup-pre-commit", "operations", "Sets up commit-time quality gates."),
    Pick("skills-for-engineers/skills/misc/git-guardrails-claude-code", "operations", "Blocks dangerous git commands in Claude Code hooks."),
    Pick("skills-for-engineers/skills/productivity/handoff", "meta", "Creates handoffs for another agent/session."),
    Pick("skills-anthropic/skills/webapp-testing", "verification", "Playwright-based local web app testing."),
    Pick("skills-anthropic/skills/mcp-builder", "engineering", "Builds and evaluates MCP servers."),
    Pick("skills-anthropic/skills/skill-creator", "meta", "Creates, packages, and evaluates skills."),
    Pick("skills-anthropic/skills/doc-coauthoring", "docs", "Coauthors technical docs, proposals, and specs."),
    Pick("skills-anthropic/skills/pdf", "research", "PDF extraction, manipulation, forms, and OCR workflows."),
    Pick("skills-anthropic/skills/xlsx", "research", "Spreadsheet and tabular data workflows."),
    Pick("skills-anthropic/skills/docx", "docs", "Word document creation and editing."),
    Pick("skills-anthropic/skills/pptx", "docs", "Slide deck creation and editing."),
    Pick("academic-research-skills/deep-research", "research", "Academic deep research, literature reviews, systematic reviews, and fact-checking."),
    Pick("academic-research-skills/academic-paper", "research", "Academic paper writing, outlining, revision, citation checks, and formatting."),
    Pick("academic-research-skills/academic-paper-reviewer", "research", "Multi-perspective manuscript review and methodology critique."),
    Pick("academic-research-skills/academic-pipeline", "research", "End-to-end research-to-publication orchestration with integrity gates."),
    Pick("agent-research-skills/skills/github-research", "research", "Discovers, analyzes, and compares GitHub repositories for research topics."),
    Pick("agent-research-skills/skills/literature-search", "research", "Searches academic literature APIs and returns structured paper metadata and BibTeX."),
    Pick("agent-research-skills/skills/literature-review", "research", "Synthesizes literature through multi-perspective expert-dialogue review."),
    Pick("agent-research-skills/skills/idea-generation", "research", "Generates and scores research ideas with novelty checking."),
    Pick("agent-research-skills/skills/novelty-assessment", "research", "Assesses research novelty through systematic literature search and critique."),
    Pick("agent-research-skills/skills/research-planning", "research", "Builds research plans, paper architectures, and dependency-ordered tasks."),
    Pick("agent-research-skills/skills/atomic-decomposition", "research", "Decomposes research ideas into atomic concepts with math-code mapping."),
    Pick("agent-research-skills/skills/algorithm-design", "research", "Designs algorithms with LaTeX pseudocode and UML/Mermaid diagrams."),
    Pick("agent-research-skills/skills/math-reasoning", "research", "Supports derivations, proofs, formalization, notation, and statistical-test selection."),
    Pick("agent-research-skills/skills/symbolic-equation", "research", "Explores symbolic regression and scientific equation discovery."),
    Pick("agent-research-skills/skills/experiment-design", "research", "Plans staged experiments, baselines, ablations, datasets, and metrics."),
    Pick("agent-research-skills/skills/experiment-code", "implementation", "Generates and improves ML experiment training and evaluation code."),
    Pick("agent-research-skills/skills/code-debugging", "implementation", "Debugs experiment code with structured error categorization and retries."),
    Pick("agent-research-skills/skills/data-analysis", "research", "Generates statistical analysis with tests, effects, confidence intervals, and p-values."),
    Pick("agent-research-skills/skills/paper-writing-section", "docs", "Writes or improves individual academic paper sections."),
    Pick("agent-research-skills/skills/related-work-writing", "docs", "Writes related-work sections with thematic compare-and-contrast structure."),
    Pick("agent-research-skills/skills/survey-generation", "docs", "Generates full survey papers with outline, RAG writing, and citation validation."),
    Pick("agent-research-skills/skills/paper-to-code", "implementation", "Converts ML papers into runnable code repositories."),
    Pick("agent-research-skills/skills/figure-generation", "docs", "Creates publication-quality scientific figures and plots."),
    Pick("agent-research-skills/skills/table-generation", "docs", "Creates publication-quality LaTeX result tables from JSON or CSV."),
    Pick("agent-research-skills/skills/citation-management", "docs", "Harvests, validates, deduplicates, and formats BibTeX citations."),
    Pick("agent-research-skills/skills/backward-traceability", "research", "Links reported paper numbers back to code that produced them."),
    Pick("agent-research-skills/skills/latex-formatting", "docs", "Handles conference paper templates, LaTeX formatting, and submission checks."),
    Pick("agent-research-skills/skills/paper-compilation", "docs", "Compiles LaTeX papers and auto-fixes compilation and citation errors."),
    Pick("agent-research-skills/skills/excalidraw-skill", "docs", "Creates and edits Excalidraw diagrams through a canvas MCP workflow."),
    Pick("agent-research-skills/skills/self-review", "research", "Reviews academic papers with structured reviewer personas and meta-review."),
    Pick("agent-research-skills/skills/paper-revision", "docs", "Maps reviewer feedback to targeted paper revisions."),
    Pick("agent-research-skills/skills/rebuttal-writing", "docs", "Writes evidence-based point-by-point rebuttals."),
    Pick("agent-research-skills/skills/slide-generation", "docs", "Turns completed papers into Beamer slides or posters."),
    Pick("agent-research-skills/skills/paper-assembly", "research", "Orchestrates full paper assembly with checkpoints and state propagation."),
)


TARGETS: dict[str, Target] = {
    "agents": Target("agents", ".agents/skills", "~/.agents/skills"),
    "claude": Target("claude", ".claude/skills", "~/.claude/skills"),
    "opencode": Target("opencode", ".opencode/skills", "~/.config/opencode/skills"),
    "codex": Target("codex", ".codex/skills", "~/.codex/skills"),
    "gemini": Target("gemini", ".gemini/skills", "~/.gemini/skills"),
    "github": Target("github", ".github/skills", None),
    "kiro": Target("kiro", ".kiro/skills", "~/.kiro/skills"),
    "cursor": Target("cursor", ".cursor/rules", None, kind="file"),
}

DEFAULT_TARGET_NAMES = ("agents", "claude", "opencode", "codex", "gemini")
SCAN_ROOTS = (
    "agent-skills/skills",
    "skills-for-engineers/skills",
    "skills-anthropic/skills",
    "academic-research-skills",
    "agent-research-skills/skills",
)
EXCLUDED_PARTS = {".git", "node_modules", "__pycache__", "deprecated"}


@dataclass(frozen=True)
class Skill:
    name: str
    source: Path
    rel_source: str
    category: str = "all"
    reason: str = ""


def eprint(*parts: object) -> None:
    print(*parts, file=sys.stderr)


def parse_csv(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    items: list[str] = []
    for value in values:
        items.extend(part.strip() for part in value.split(",") if part.strip())
    return items


def read_frontmatter_value(skill_md: Path, key: str) -> str | None:
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = skill_md.read_text(errors="replace").splitlines()

    if not lines or lines[0].strip() != "---":
        return None

    for line in lines[1:]:
        if line.strip() == "---":
            return None
        if line.startswith(f"{key}:"):
            value = line.split(":", 1)[1].strip()
            return value.strip("\"'")
    return None


def skill_name(source: Path) -> str:
    return read_frontmatter_value(source / "SKILL.md", "name") or source.name


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def validate_pick(root: Path, pick: Pick) -> Skill:
    source = (root / pick.path).resolve()
    skill_md = source / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"selected skill is missing SKILL.md: {pick.path}")
    return Skill(skill_name(source), source, pick.path, pick.category, pick.reason)


def scan_all_skills(root: Path) -> list[Skill]:
    skills: list[Skill] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.is_dir():
            continue
        for skill_md in sorted(base.rglob("SKILL.md")):
            if EXCLUDED_PARTS.intersection(skill_md.relative_to(root).parts):
                continue
            source = skill_md.parent.resolve()
            skills.append(Skill(skill_name(source), source, relpath(source, root)))
    return skills


def selected_skills(root: Path, use_all: bool, includes: list[str], excludes: list[str]) -> list[Skill]:
    all_skills = scan_all_skills(root)
    by_name: dict[str, Skill] = {}
    by_path: dict[str, Skill] = {}
    for skill in all_skills:
        by_name.setdefault(skill.name, skill)
        by_path[skill.rel_source] = skill

    if use_all:
        skills = all_skills
    else:
        skills = [validate_pick(root, pick) for pick in DEFAULT_PICKS]

    for item in includes:
        skill = by_name.get(item) or by_path.get(item.rstrip("/"))
        if skill is None:
            candidate = (root / item).resolve()
            if (candidate / "SKILL.md").is_file():
                skill = Skill(skill_name(candidate), candidate, relpath(candidate, root))
            else:
                raise ValueError(f"unknown --include skill: {item}")
        if all(existing.name != skill.name for existing in skills):
            skills.append(skill)

    exclude_set = set(excludes)
    skills = [
        skill
        for skill in skills
        if skill.name not in exclude_set and skill.rel_source not in exclude_set
    ]

    seen: set[str] = set()
    unique: list[Skill] = []
    for skill in skills:
        if skill.name in seen:
            eprint(f"warning: duplicate skill name skipped: {skill.name} ({skill.rel_source})")
            continue
        seen.add(skill.name)
        unique.append(skill)
    return unique


def target_dir(root: Path, target: Target, scope: str) -> Path | None:
    raw = target.user_path if scope == "user" else target.project_path
    if raw is None:
        return None
    expanded = os.path.expanduser(raw)
    path = Path(expanded)
    return path if path.is_absolute() else root / path


def target_path(base: Path, skill: Skill, target: Target) -> Path:
    if target.kind == "file":
        return base / f"{skill.name}.md"
    return base / skill.name


def source_path(skill: Skill, target: Target) -> Path:
    if target.kind == "file":
        return skill.source / "SKILL.md"
    return skill.source


def load_manifest(base: Path) -> dict[str, object]:
    manifest_path = base / MANIFEST
    if not manifest_path.is_file():
        return {"version": VERSION, "skills": {}}
    try:
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        eprint(f"warning: ignoring unreadable manifest: {manifest_path}")
        return {"version": VERSION, "skills": {}}
    if not isinstance(loaded, dict) or not isinstance(loaded.get("skills"), dict):
        return {"version": VERSION, "skills": {}}
    return loaded


def write_manifest(base: Path, skills: list[Skill], target: Target, mode: str, dry_run: bool) -> None:
    manifest = {
        "version": VERSION,
        "mode": mode,
        "target": target.name,
        "kind": target.kind,
        "skills": {
            skill.name: {
                "source": skill.rel_source,
                "category": skill.category,
            }
            for skill in skills
        },
    }
    path = base / MANIFEST
    if dry_run:
        print(f"would write manifest: {path}")
        return
    try:
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        eprint(f"warning: cannot write manifest: {path}")


def remove_path(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"would remove: {path}")
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def ensure_base(base: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"would ensure directory: {base}")
        return True
    try:
        base.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        eprint(f"warning: cannot write target directory: {base}")
        return False
    return True


def install_skill(
    skill: Skill,
    target: Target,
    base: Path,
    mode: str,
    managed: set[str],
    force: bool,
    dry_run: bool,
) -> str:
    dest = target_path(base, skill, target)
    src = source_path(skill, target).resolve()

    if dest.exists() or dest.is_symlink():
        already_linked = dest.is_symlink() and dest.resolve() == src
        if already_linked and mode == "symlink":
            return f"unchanged: {skill.name} -> {dest}"

        if skill.name in managed or dest.is_symlink() or force:
            remove_path(dest, dry_run)
        else:
            return f"skipped unmanaged existing path: {dest}"

    if dry_run:
        action = "link" if mode == "symlink" else "copy"
        return f"would {action}: {src} -> {dest}"

    try:
        if mode == "symlink":
            dest.symlink_to(src, target_is_directory=target.kind == "dir")
        elif target.kind == "file":
            shutil.copy2(src, dest)
        else:
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"),
            )
    except PermissionError:
        return f"skipped permission denied: {dest}"

    action = "linked" if mode == "symlink" else "copied"
    return f"{action}: {skill.name} -> {dest}"


def sync_target(
    skills: list[Skill],
    target: Target,
    base: Path,
    mode: str,
    force: bool,
    prune: bool,
    dry_run: bool,
) -> None:
    if not ensure_base(base, dry_run):
        return

    manifest = load_manifest(base)
    old_skills = set(manifest.get("skills", {}).keys())
    new_skills = {skill.name for skill in skills}

    if prune:
        for stale in sorted(old_skills - new_skills):
            stale_path = base / (f"{stale}.md" if target.kind == "file" else stale)
            if stale_path.exists() or stale_path.is_symlink():
                remove_path(stale_path, dry_run)
                print(f"pruned: {stale_path}")

    for skill in skills:
        print(install_skill(skill, target, base, mode, old_skills, force, dry_run))

    write_manifest(base, skills, target, mode, dry_run)


def parse_target_names(raw: list[str]) -> list[str]:
    names = parse_csv(raw) or list(DEFAULT_TARGET_NAMES)
    if "all" in names:
        names = list(TARGETS)
    unknown = [name for name in names if name not in TARGETS]
    if unknown:
        raise ValueError(f"unknown target(s): {', '.join(unknown)}")
    return names


def list_skills(skills: list[Skill]) -> None:
    width = max((len(skill.name) for skill in skills), default=0)
    for skill in skills:
        category = f"[{skill.category}]" if skill.category else ""
        print(f"{skill.name:<{width}}  {category:<16} {skill.rel_source}")
        if skill.reason:
            print(f"{'':<{width}}  {'':<16} {skill.reason}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync curated coding, engineering, and research skills into agent skill directories."
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project", "both"),
        default="user",
        help="Install to user-level directories, project-local dot directories, or both. Default: user.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root for --scope project. Default: current directory.",
    )
    parser.add_argument(
        "--mode",
        choices=("symlink", "copy"),
        default="symlink",
        help="Sync as symlinks or physical copies. Default: symlink.",
    )
    parser.add_argument(
        "--targets",
        action="append",
        help=(
            f"Comma-separated targets. Defaults to {', '.join(DEFAULT_TARGET_NAMES)}. "
            f"Available: {', '.join(TARGETS)}, all."
        ),
    )
    parser.add_argument("--all-skills", action="store_true", help="Sync every non-deprecated skill found.")
    parser.add_argument("--include", action="append", help="Extra skill name or relative skill path to sync.")
    parser.add_argument("--exclude", action="append", help="Skill name or relative skill path to omit.")
    parser.add_argument("--list", action="store_true", help="List selected skills and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    parser.add_argument("--force", action="store_true", help="Replace unmanaged existing files/directories.")
    parser.add_argument(
        "--no-prune",
        action="store_true",
        help="Keep previously managed skills that are no longer selected.",
    )
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    script_root = Path(__file__).resolve().parent
    project_root = Path(args.root).expanduser().resolve()

    try:
        skills = selected_skills(
            script_root,
            args.all_skills,
            parse_csv(args.include),
            parse_csv(args.exclude),
        )
        target_names = parse_target_names(args.targets)
    except (FileNotFoundError, ValueError) as exc:
        eprint(f"error: {exc}")
        return 2

    if args.list:
        list_skills(skills)
        return 0

    scopes = ("user", "project") if args.scope == "both" else (args.scope,)
    for scope in scopes:
        root = project_root if scope == "project" else Path("/")
        for name in target_names:
            target = TARGETS[name]
            base = target_dir(project_root if scope == "project" else root, target, scope)
            if base is None:
                eprint(f"warning: target {name!r} has no {scope} path")
                continue
            print(f"\n== {scope}:{name} -> {base} ==")
            sync_target(
                skills,
                target,
                base.expanduser(),
                args.mode,
                args.force,
                not args.no_prune,
                args.dry_run,
            )

    return 0
    

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

