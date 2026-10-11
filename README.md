# skills-hub

A collection of upstream agent skill repositories, with a Python script that installs a curated selection into your coding tools. Repositories are Git submodules: their contents stay upstream, and this hub records the revisions it uses.

## Quick start

Requires Git and Python 3.10+. The shell wrapper uses Bash; you can also run `python3 sync_skills.py` directly.

```bash
git clone --recurse-submodules https://github.com/Pingsheng-Li/skills-hub.git
cd skills-hub

# Inspect the 18 selected starter skills and why each is included.
bash sync_skills.sh --list

# Preview, then install for Claude Code across your projects.
bash sync_skills.sh --targets claude --dry-run
bash sync_skills.sh --targets claude
```

For an existing clone with empty submodule directories, run `git submodule update --init --recursive` first.

Running `bash sync_skills.sh` without arguments installs the **starter** profile as symlinks into the user directories for Agents, Claude Code, OpenCode, Codex, and Gemini. Use `--targets` to choose just the tools you use.

**Existing users:** the default selection is now the 18-skill starter set. Use `--profile full` to keep the previous 73-skill selection. A sync normally removes previously managed skills that are absent from the new selection; use `--no-prune` to keep them, and `--dry-run` to preview changes.

## Curated selections

| Profile | Skills | Selection rationale |
| --- | ---: | --- |
| `starter` (default) | 18 | Common planning, implementation, verification, and documentation tasks. Specialized tools and large research workflows stay optional. |
| `research` | 14 | Literature discovery, research planning, experiments, analysis, and manuscript work. Can be combined with `starter`. |
| `full` | 73 | The original broader curated catalog, including UI, operations, document formats, and end-to-end academic workflows. |

The starter choices are:

| Task | Selected skills | Why |
| --- | --- | --- |
| Establish context and sources | `context-engineering`, `source-driven-development` | Keep project context focused and consult authoritative documentation. |
| Plan work | `spec-driven-development`, `planning-and-task-breakdown` | Turn requirements into verifiable steps. |
| Implement and debug | `incremental-implementation`, `test-driven-development`, `debugging-and-error-recovery`, `prototype` | Build in small increments, prove behavior, and investigate uncertain designs. |
| Design and review | `api-and-interface-design`, `code-review-and-quality`, `code-simplification`, `security-and-hardening` | Keep interfaces, implementation, and input handling maintainable. |
| Verify browser behavior | `webapp-testing` | Exercise real web applications through Playwright. |
| Maintain and hand off | `git-workflow-and-versioning`, `documentation-and-adrs`, `handoff`, `doc-coauthoring` | Record changes, decisions, and context for the next session. |
| Extend the collection | `skill-creator` | Create and evaluate task-specific skills. |

The research choices are:

| Task | Selected skills |
| --- | --- |
| Read source material | `pdf`, `xlsx` |
| Find and synthesize literature | `literature-search`, `literature-review`, `citation-management` |
| Develop a research direction | `idea-generation`, `novelty-assessment`, `research-planning` |
| Run and analyze experiments | `experiment-design`, `experiment-code`, `data-analysis`, `figure-generation` |
| Write and review papers | `academic-paper`, `academic-paper-reviewer` |

`CURATED_PICKS` in [sync_skills.py](sync_skills.py) records each skill's source, category, and selection reason. `PROFILE_SKILLS` defines the smaller sets. List a profile to see its exact upstream paths and reasons:

```bash
bash sync_skills.sh --profile research --list
bash sync_skills.sh --profile full --list

# Install both focused sets (32 skills).
bash sync_skills.sh --targets claude --profile starter,research
```

## Cherry-pick skills

`--only` starts from an empty selection. `--include` adds to your selection, and `--exclude` removes from it. Each accepts comma-separated names or repository-relative skill paths, and can be repeated.

```bash
# Install exactly these two skills for Claude Code.
bash sync_skills.sh --targets claude --only test-driven-development,pdf

# Add specialized skills to the starter profile.
bash sync_skills.sh --targets claude --include frontend-ui-engineering,mcp-builder

# Select a specific upstream implementation when names overlap.
bash sync_skills.sh --targets claude --only skills-anthropic/skills/skill-creator

# Customize the research profile.
bash sync_skills.sh --targets claude --profile research --exclude xlsx

# Inspect everything available upstream, beyond the curated catalog.
bash sync_skills.sh --all-skills --list
```

`--profile`, `--only`, and `--all-skills` are mutually exclusive starting points. `--include` and `--exclude` work with any of them. Exclusions take precedence. A run describes the complete desired selection for each target: to add skills while retaining previously installed ones, pass `--no-prune` or include them in the new selection.

## Claude Code

The `claude` target (`claude-code` is an alias) uses Claude Code's native skill directories. Each installed skill has a `SKILL.md` and its supporting files:

```text
~/.claude/skills/
  test-driven-development/ -> /path/to/skills-hub/agent-skills/skills/test-driven-development/
    SKILL.md
```

Personal skills live in `~/.claude/skills/`; project skills live in `.claude/skills/`. Claude Code supports symlinked skill directories and direct invocation such as `/test-driven-development` or `/webapp-testing`. See the [official skills documentation](https://code.claude.com/docs/en/skills).

```bash
# Install only into another project's Claude Code skill directory.
bash sync_skills.sh --targets claude-code --scope project --root /path/to/project

# Use the same custom config location as your Claude Code session.
CLAUDE_CONFIG_DIR=/path/to/claude-config bash sync_skills.sh --targets claude
```

`CLAUDE_CONFIG_DIR` changes only the personal Claude target to `$CLAUDE_CONFIG_DIR/skills`; the project path stays `.claude/skills`. See [Claude Code configuration](https://code.claude.com/docs/en/settings).

Start Claude Code in your project and type `/` to check available skills. The sync installs skills, not upstream plugins: plugin commands, registered agents, hooks, MCP servers, API keys, and runtime packages are not configured by this script. Follow an individual skill's setup instructions when it needs additional tools. For example, `webapp-testing` needs Playwright and its browser binaries.

Symlinks are the recommended mode: the source repository and its shared resources remain available, and upstream updates appear through existing links. Keep this checkout at a stable path. `--mode copy` copies each selected skill folder and its contents, but does not collect references outside that folder. For skills that depend on repository-level resources, use symlinks or the upstream plugin installation. Copies must be re-synced after updating upstream.

## Other targets and options

| Target | User scope | Project scope |
| --- | --- | --- |
| `agents` | `~/.agents/skills` | `.agents/skills` |
| `claude` / `claude-code` | `~/.claude/skills` or `$CLAUDE_CONFIG_DIR/skills` | `.claude/skills` |
| `opencode` | `~/.config/opencode/skills` | `.opencode/skills` |
| `codex` | `~/.codex/skills` | `.codex/skills` |
| `gemini` | `~/.gemini/skills` | `.gemini/skills` |
| `github` | — | `.github/skills` |
| `kiro` | `~/.kiro/skills` | `.kiro/skills` |
| `cursor` | — | `.cursor/rules` (only `SKILL.md`, as a Markdown file) |

```bash
bash sync_skills.sh --targets claude,codex --scope both --root /path/to/project
bash sync_skills.sh --targets claude --scope project --root /path/to/project --only pdf --mode copy
bash sync_skills.sh --help
```

`--root` selects the destination project; sources always come from this hub's checkout. `--targets all` selects every target; targets without a user path are skipped in user scope. Target adapters install files; individual skill capabilities still depend on the tools available in each agent.

Each destination keeps a `.skill-sync-manifest.json` recording skills installed by this script. Existing personal files, directories, and symlinks are preserved unless already managed or explicitly replaced with `--force`. Skipped paths are not adopted into the manifest. `--no-prune` retains both previously managed skills and their tracking entries so a later sync can still manage them. Managed copies are replaced on re-sync, so keep personal edits outside managed destinations.

## Upstream repositories and updates

| Submodule | Source | Focus |
| --- | --- | --- |
| `agent-skills` | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | Software engineering workflows |
| `skills-for-engineers` | [mattpocock/skills](https://github.com/mattpocock/skills) | Practical engineering and productivity |
| `skills-anthropic` | [anthropics/skills](https://github.com/anthropics/skills) | Documents, browser testing, MCP, and skill authoring |
| `academic-research-skills` | [imbad0202/academic-research-skills](https://github.com/imbad0202/academic-research-skills) | Academic writing, review, and research orchestration |
| `agent-research-skills` | [lingzhi227/agent-research-skills](https://github.com/lingzhi227/agent-research-skills) | Literature, experiments, analysis, and paper production |

To use the revisions recorded by the hub:

```bash
git pull --ff-only
git submodule update --init --recursive
```

To advance the submodules to their latest upstream branches:

```bash
git submodule update --init --remote --recursive
git diff --submodule=short
bash sync_skills.sh --profile full --list
```

The latter changes the hub's submodule pointers; commit those changes to record the updated revisions. Re-run your preferred sync command if the selection changed or you use copy mode. Upstream projects retain their own licenses; consult the license files in each submodule before redistributing skills.

## Development checks

```bash
python3 -B -m unittest discover -s tests -v
git diff --check
```

Tests use temporary directories and do not modify your installed skills. They cover profile selection, exact picks, Claude Code locations and supporting files, dry runs, and preservation of personal skills.
