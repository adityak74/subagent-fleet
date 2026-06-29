# Graph Report - /Users/adityakarnam/Projects/subagent-fleet  (2026-06-29)

## Corpus Check
- 109 files · ~84,371 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1029 nodes · 2289 edges · 82 communities (74 shown, 8 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 218 edges (avg confidence: 0.74)
- Token cost: 4,800 input · 1,200 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Lunr Search (wordcut.js)|Lunr Search (wordcut.js)]]
- [[_COMMUNITY_MkDocs Bundle JS|MkDocs Bundle JS]]
- [[_COMMUNITY_Lunr Search Index|Lunr Search Index]]
- [[_COMMUNITY_Node Discovery & Health|Node Discovery & Health]]
- [[_COMMUNITY_Lunr Search Workers|Lunr Search Workers]]
- [[_COMMUNITY_Lunr Core|Lunr Core]]
- [[_COMMUNITY_Plugin & Config Validation|Plugin & Config Validation]]
- [[_COMMUNITY_Fleet Dashboard Server|Fleet Dashboard Server]]
- [[_COMMUNITY_CLI Commands|CLI Commands]]
- [[_COMMUNITY_Lunr Arabic|Lunr Arabic]]
- [[_COMMUNITY_Lunr Turkish|Lunr Turkish]]
- [[_COMMUNITY_Lunr Japanese|Lunr Japanese]]
- [[_COMMUNITY_Code Generator Pipeline|Code Generator Pipeline]]
- [[_COMMUNITY_Lunr Korean|Lunr Korean]]
- [[_COMMUNITY_Event Parsing Tests|Event Parsing Tests]]
- [[_COMMUNITY_Core Data Models|Core Data Models]]
- [[_COMMUNITY_Lunr Chinese|Lunr Chinese]]
- [[_COMMUNITY_Lunr Spanish|Lunr Spanish]]
- [[_COMMUNITY_Lunr French|Lunr French]]
- [[_COMMUNITY_Lunr Italian|Lunr Italian]]
- [[_COMMUNITY_Lunr Portuguese|Lunr Portuguese]]
- [[_COMMUNITY_Lunr Multi-Language|Lunr Multi-Language]]
- [[_COMMUNITY_Lunr Danish|Lunr Danish]]
- [[_COMMUNITY_Lunr Dutch|Lunr Dutch]]
- [[_COMMUNITY_Lunr Finnish|Lunr Finnish]]
- [[_COMMUNITY_Config Loading & Errors|Config Loading & Errors]]
- [[_COMMUNITY_Lunr Romanian|Lunr Romanian]]
- [[_COMMUNITY_Lunr Swedish|Lunr Swedish]]
- [[_COMMUNITY_SSE Event Stream|SSE Event Stream]]
- [[_COMMUNITY_Claude Agent Generation|Claude Agent Generation]]
- [[_COMMUNITY_Agent Role Examples|Agent Role Examples]]
- [[_COMMUNITY_Lunr Finnish2|Lunr Finnish2]]
- [[_COMMUNITY_Log Line Parser|Log Line Parser]]
- [[_COMMUNITY_CLI Integration Tests|CLI Integration Tests]]
- [[_COMMUNITY_Lunr Hebrew|Lunr Hebrew]]
- [[_COMMUNITY_Lunr Hungarian|Lunr Hungarian]]
- [[_COMMUNITY_Lunr Hindi|Lunr Hindi]]
- [[_COMMUNITY_FleetConfig & Model Warmup|FleetConfig & Model Warmup]]
- [[_COMMUNITY_LiteLLM Config Generation|LiteLLM Config Generation]]
- [[_COMMUNITY_Node Status Events|Node Status Events]]
- [[_COMMUNITY_Dashboard UI Panels|Dashboard UI Panels]]
- [[_COMMUNITY_Lunr Norwegian|Lunr Norwegian]]
- [[_COMMUNITY_Plugin Marketplace Schema|Plugin Marketplace Schema]]
- [[_COMMUNITY_Agent Route Events|Agent Route Events]]
- [[_COMMUNITY_CLI Entry Points & Trace|CLI Entry Points & Trace]]
- [[_COMMUNITY_Lunr Armenian|Lunr Armenian]]
- [[_COMMUNITY_Lunr Vietnamese|Lunr Vietnamese]]
- [[_COMMUNITY_Gen4 Roadmap Features|Gen4 Roadmap Features]]
- [[_COMMUNITY_Bootstrap & Setup Skills|Bootstrap & Setup Skills]]
- [[_COMMUNITY_MkDocs Documentation|MkDocs Documentation]]
- [[_COMMUNITY_Lunr Greek|Lunr Greek]]
- [[_COMMUNITY_Lunr Tamil|Lunr Tamil]]
- [[_COMMUNITY_Lunr Russian|Lunr Russian]]
- [[_COMMUNITY_Lunr Telugu|Lunr Telugu]]
- [[_COMMUNITY_Lunr Sanskrit|Lunr Sanskrit]]
- [[_COMMUNITY_Lunr German|Lunr German]]
- [[_COMMUNITY_Lunr Stemmer|Lunr Stemmer]]
- [[_COMMUNITY_WoL Generator|WoL Generator]]
- [[_COMMUNITY_Aider Generator|Aider Generator]]
- [[_COMMUNITY_MCP Generator|MCP Generator]]
- [[_COMMUNITY_Router Generator|Router Generator]]
- [[_COMMUNITY_Scheduler Generator|Scheduler Generator]]

## God Nodes (most connected - your core abstractions)
1. `m()` - 56 edges
2. `FleetConfig` - 35 edges
3. `H()` - 31 edges
4. `I()` - 28 edges
5. `w()` - 28 edges
6. `glob()` - 27 edges
7. `e()` - 23 edges
8. `z()` - 22 edges
9. `slice()` - 21 edges
10. `join()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `MkDocs Home Page` --semantically_similar_to--> `subagent-fleet README`  [INFERRED] [semantically similar]
  docs/index.md → README.md
- `MkDocs Future Roadmap Page` --semantically_similar_to--> `Generation 4 Roadmap Proposal`  [INFERRED] [semantically similar]
  docs/roadmap.md → ROADMAP_PROPOSAL.md
- `MkDocs Architecture Spec Page` --semantically_similar_to--> `subagent-fleet Technical Specification (SPEC.md)`  [INFERRED] [semantically similar]
  docs/spec.md → SPEC.md
- `subagent-fleet-setup Skill Template` --semantically_similar_to--> `subagent-fleet-setup Skill (Plugin)`  [INFERRED] [semantically similar]
  src/subagent_fleet/skill_templates/subagent-fleet-setup.md → plugins/subagent-fleet/skills/subagent-fleet-setup/SKILL.md
- `test_generate_env_with_observability()` --calls--> `generate_env_file()`  [INFERRED]
  tests/test_observability.py → src/subagent_fleet/generators/env_file.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Agent Trio: Planner, Implementer, Reviewer** — planner_agent_role, implementer_agent_role, reviewer_agent_role [EXTRACTED 1.00]
- **Core Config-to-Generation Pipeline: fleet.yaml drives LiteLLM and Ollama config** — fleet_yaml_config, litellm_gateway_concept, ollama_node_concept [EXTRACTED 1.00]
- **MkDocs Documentation Deployment: workflow deploys site from mkdocs config and docs pages** — github_workflows_docs_yml_workflow, mkdocs_yml_config, docs_index_home [EXTRACTED 1.00]
- **Skill Template -> Plugin Skill Dual-Path Pattern (Bootstrap, Operations, Setup)** — template_bootstrap, template_operations, template_setup, plugin_bootstrap_skill, plugin_operations_skill, plugin_setup_skill [EXTRACTED 1.00]
- **Dashboard Four-Panel UI Layout (Node Health, Agent Routing, Trace Stream, Warmup)** — src_subagent_fleet_ui_templates_dashboard_html, src_subagent_fleet_ui_templates_dashboard_node_health_panel, src_subagent_fleet_ui_templates_dashboard_agent_routing_panel, src_subagent_fleet_ui_templates_dashboard_trace_stream_panel, src_subagent_fleet_ui_templates_dashboard_warmup_panel [EXTRACTED 1.00]
- **Fleet Lifecycle: Setup -> Generate Files -> Operate via Operations Skill** — plugin_setup_skill, generated_files_concept, plugin_operations_skill [INFERRED 0.85]

## Communities (82 total, 8 thin omitted)

### Community 0 - "Lunr Search (wordcut.js)"
Cohesion: 0.05
Nodes (27): cleanUpNextTick(), drainQueue(), escapeBraces(), expandTop(), expectedException(), fail(), getMessage(), globUnescape() (+19 more)

### Community 1 - "MkDocs Bundle JS"
Cohesion: 0.07
Nodes (33): an(), Ao(), At(), Bi(), bs(), ce(), da(), di() (+25 more)

### Community 2 - "Lunr Search Index"
Cohesion: 0.14
Nodes (44): ai(), as(), ba(), de(), es(), fs(), g(), ge() (+36 more)

### Community 3 - "Node Discovery & Health"
Cohesion: 0.08
Nodes (29): BaseHTTPRequestHandler, discover_fleet(), discover_node(), discovery_to_json(), get_loaded_models(), get_ollama_tags(), NodeDiscovery, _parse_models() (+21 more)

### Community 4 - "Lunr Search Workers"
Cohesion: 0.08
Nodes (42): aa(), ar(), be(), bn(), ca(), cr(), dn(), Do() (+34 more)

### Community 5 - "Lunr Core"
Cohesion: 0.12
Nodes (12): deprecationWarning(), finish(), glob(), globSync(), inflight(), isArray(), isIgnored(), mark() (+4 more)

### Community 6 - "Plugin & Config Validation"
Cohesion: 0.12
Nodes (29): claude_marketplace(), claude_plugin_manifest(), codex_marketplace(), codex_plugin_manifest(), _install_claude(), _install_codex(), install_plugin_marketplaces(), _install_plugin_skills() (+21 more)

### Community 7 - "Fleet Dashboard Server"
Cohesion: 0.06
Nodes (27): create_dashboard_server(), DashboardServer, Path, HTTP server for the Fleet Dashboard.      Serves:         - /dashboard or / : HT, Initialize the dashboard server.          Args:             fleet_config: Loaded, Factory function to create a configured DashboardServer instance.      Args:, Start serving requests until shutdown is called., Integration tests for Fleet Dashboard UI server. (+19 more)

### Community 8 - "CLI Commands"
Cohesion: 0.13
Nodes (31): help, Option, clean(), discover(), doctor(), init(), install_assistant_plugins(), install_assistant_skills() (+23 more)

### Community 9 - "Lunr Arabic"
Cohesion: 0.12
Nodes (31): a(), Ae(), B(), Bo(), Br(), ci(), dr(), e() (+23 more)

### Community 10 - "Lunr Turkish"
Cohesion: 0.21
Nodes (30): a(), b(), c(), d(), E(), er(), f(), g() (+22 more)

### Community 11 - "Lunr Japanese"
Cohesion: 0.13
Nodes (24): arrayToHash(), debuglog(), _deepEqual(), deprecate(), _extend(), format(), formatArray(), formatError() (+16 more)

### Community 12 - "Code Generator Pipeline"
Cohesion: 0.11
Nodes (16): generate(), Generate LiteLLM, Claude Code, and Aider configuration files., generate_blackboard_daemon(), Path, Path, write_generated(), generate_mcp_config(), Path (+8 more)

### Community 13 - "Lunr Korean"
Cohesion: 0.15
Nodes (19): Cn(), dt(), Fn(), gn(), ja(), kn(), li(), Me() (+11 more)

### Community 14 - "Event Parsing Tests"
Cohesion: 0.11
Nodes (11): LogLineParser, Parse raw LiteLLM log lines into structured TraceLogEvent objects.      Recogniz, Tests for LogLineParser on known log patterns., Verify POST /v1/chat/completions lines are parsed as routing events., Verify '200 OK' lines are parsed as success events., Verify Exception/Error lines are parsed as error events., Verify API Base lines are parsed as routing events., Verify Model: lines are parsed as routing events. (+3 more)

### Community 15 - "Core Data Models"
Cohesion: 0.17
Nodes (15): BaseModel, MappingNode, AgentConfig, config_to_plain_dict(), _construct_mapping(), GatewayConfig, McpServerConfig, ModelConfig (+7 more)

### Community 16 - "Lunr Chinese"
Cohesion: 0.25
Nodes (11): childrenIgnored(), ignoreMap(), isAbsolute(), join(), makeAbs(), normalize(), normalizeArray(), relative() (+3 more)

### Community 17 - "Lunr Spanish"
Cohesion: 0.21
Nodes (13): a(), b(), c(), d(), e(), h(), i(), l() (+5 more)

### Community 18 - "Lunr French"
Cohesion: 0.21
Nodes (13): a(), c(), e(), f(), i(), k(), l(), m() (+5 more)

### Community 19 - "Lunr Italian"
Cohesion: 0.21
Nodes (14): a(), d(), e(), f(), i(), l(), m(), o() (+6 more)

### Community 20 - "Lunr Portuguese"
Cohesion: 0.23
Nodes (14): a(), c(), d(), f(), i(), l(), m(), n() (+6 more)

### Community 21 - "Lunr Multi-Language"
Cohesion: 0.19
Nodes (14): a(), c(), d(), e(), f(), l(), m(), n() (+6 more)

### Community 22 - "Lunr Danish"
Cohesion: 0.19
Nodes (14): ae(), ce(), constructor(), fe(), ie(), ke(), le(), ne() (+6 more)

### Community 23 - "Lunr Dutch"
Cohesion: 0.28
Nodes (13): a(), b(), c(), f(), i(), k(), l(), m() (+5 more)

### Community 24 - "Lunr Finnish"
Cohesion: 0.23
Nodes (13): a(), c(), e(), f(), i(), l(), m(), o() (+5 more)

### Community 25 - "Config Loading & Errors"
Cohesion: 0.29
Nodes (14): ConfigError, format_validation_error(), load_config(), Path, Raised when fleet.yaml cannot be loaded or validated., Path, test_rejects_duplicate_mapping_keys(), test_rejects_invalid_url() (+6 more)

### Community 26 - "Lunr Romanian"
Cohesion: 0.19
Nodes (14): Ee(), Fe(), Go(), J(), ji(), Ke(), Kr(), l() (+6 more)

### Community 27 - "Lunr Swedish"
Cohesion: 0.23
Nodes (12): balanced(), braceExpand(), expand(), filter(), isMatch(), make(), match(), maybeMatch() (+4 more)

### Community 28 - "SSE Event Stream"
Cohesion: 0.19
Nodes (10): Event types and utilities for SSE streaming in the Fleet Dashboard., Serialize any supported event type to SSE wire format.      Args:         event:, Event representing warmup progress for a single model., Serialize to SSE wire format., serialize_event(), WarmupProgressEvent, Tests for the serialize_event helper function., Verify serialize_event works with NodeStatusEvent. (+2 more)

### Community 29 - "Claude Agent Generation"
Cohesion: 0.18
Nodes (9): Environment, generate_claude_agents(), Path, default_aliases(), template_env(), generate_env_file(), Path, test_claude_agent_markdown_has_frontmatter() (+1 more)

### Community 30 - "Agent Role Examples"
Cohesion: 0.23
Nodes (13): Example Generated Implementer Agent File, Example Generated LiteLLM Configuration, Example Generated Planner Agent File, Example Generated Reviewer Agent File, fleet.yaml Declarative Configuration File, Implementer Agent Role: heavy-model implementation with Edit/MultiEdit/Bash tools, LiteLLM Gateway Integration Pattern, Ollama Node Discovery and Health Check (+5 more)

### Community 31 - "Lunr Finnish2"
Cohesion: 0.21
Nodes (7): i(), l(), n(), s(), t(), u(), _()

### Community 32 - "Log Line Parser"
Cohesion: 0.18
Nodes (8): Event representing a parsed LiteLLM log line., Serialize to SSE wire format., Parse a single log line into a TraceLogEvent.          Args:             line: R, TraceLogEvent, Tests for TraceLogEvent serialization and timestamp generation., Verify timestamp is automatically set if not provided., Verify explicit timestamp is not overwritten., TestTraceLogEvent

### Community 33 - "CLI Integration Tests"
Cohesion: 0.24
Nodes (9): Path, test_generate_creates_expected_files(), test_init_creates_fleet_yaml(), test_plugins_install_all_targets(), test_plugins_install_does_not_overwrite_without_force(), test_plugins_install_specific_target(), test_skills_install_all_targets(), test_skills_install_does_not_overwrite_without_force() (+1 more)

### Community 34 - "Lunr Hebrew"
Cohesion: 0.33
Nodes (10): a(), c(), d(), e(), l(), m(), n(), o() (+2 more)

### Community 35 - "Lunr Hungarian"
Cohesion: 0.33
Nodes (10): a(), c(), f(), l(), m(), n(), o(), r() (+2 more)

### Community 36 - "Lunr Hindi"
Cohesion: 0.30
Nodes (3): collectNonEnumProps(), EventEmitter(), isFunction()

### Community 37 - "FleetConfig & Model Warmup"
Cohesion: 0.36
Nodes (8): FleetConfig, select_models(), warmup_model(), warmup_models(), WarmupResult, test_warmup_falls_back_to_minimal_prompt(), test_warmup_model_posts_empty_messages(), test_warmup_selects_agent_model()

### Community 38 - "LiteLLM Config Generation"
Cohesion: 0.20
Nodes (6): generate_litellm_config(), Path, test_litellm_output_contains_ollama_provider_and_api_base(), test_generate_env_with_observability(), test_generate_litellm_with_observability(), test_observability_defaults()

### Community 39 - "Node Status Events"
Cohesion: 0.24
Nodes (7): NodeStatusEvent, Event representing a full snapshot of node discovery results., Serialize to SSE wire format (event name + data payload)., Tests for NodeStatusEvent serialization., Verify SSE wire format has correct event name and data field., Verify data payload is valid JSON., TestNodeStatusEvent

### Community 40 - "Dashboard UI Panels"
Cohesion: 0.28
Nodes (9): Generated Fleet Output Files (litellm_config.yaml, .env.subagent-fleet, .claude/agents/*.md), subagent-fleet-operations Skill (Plugin), Agent Routing Model (agent -> model key -> Ollama node -> LiteLLM alias), Dashboard Agent Routing Panel, Fleet Dashboard HTML Template, Dashboard Node Health Panel, Dashboard Live Trace Stream Panel, Dashboard Model Warmup Progress Panel (+1 more)

### Community 41 - "Lunr Norwegian"
Cohesion: 0.33
Nodes (7): a(), c(), e(), i(), s(), t(), u()

### Community 42 - "Plugin Marketplace Schema"
Cohesion: 0.25
Nodes (7): description, name, owner, name, url, plugins, $schema

### Community 43 - "Agent Route Events"
Cohesion: 0.29
Nodes (6): AgentRouteEvent, Event representing agent routing table updates., Serialize to SSE wire format., Tests for AgentRouteEvent serialization., Verify SSE wire format has correct event name., TestAgentRouteEvent

### Community 44 - "CLI Entry Points & Trace"
Cohesion: 0.29
Nodes (3): Repository Guidelines (AGENTS.md), Public API for launching the Fleet Dashboard., subagent-fleet Python CLI Tool (init/validate/discover/generate/warmup/status/doctor/clean)

### Community 45 - "Lunr Armenian"
Cohesion: 0.33
Nodes (7): c(), f(), p(), vn(), vt(), Yo(), zr()

### Community 46 - "Lunr Vietnamese"
Cohesion: 0.29
Nodes (7): er(), hr(), ie(), _o(), Rr(), t(), Zt()

### Community 47 - "Gen4 Roadmap Features"
Cohesion: 0.40
Nodes (6): Decentralized Blackboard Architecture: agents publish events to shared pool instead of Supervisor SPOF (Gen4), Dynamic Role Switching via fleet-config-editor MCP tool for self-balancing swarms (Gen4), Generative UI: SSE-stream agent outputs to dynamic React dashboard (Gen4), GPU Microscheduler: queue inter-agent requests against live VRAM before dispatching (Gen4), Markdown-Based State Driver: TASKS.md/DECISIONS.md/CONTEXT.md in .fleet_state/ instead of Redis/SQLite (Gen4), Generation 4 Roadmap Proposal

### Community 48 - "Bootstrap & Setup Skills"
Cohesion: 0.47
Nodes (6): Bootstrap Workflow: Install CLI -> Verify -> Install Skills -> Setup, Network Safety: No Public Internet Exposure for Ollama/LiteLLM, subagent-fleet-bootstrap Skill (Plugin), subagent-fleet-setup Skill (Plugin), subagent-fleet-bootstrap Skill Template, subagent-fleet-setup Skill Template

### Community 49 - "MkDocs Documentation"
Cohesion: 0.33
Nodes (6): MkDocs Home Page, MIT License, MkDocs Future Roadmap Page, MkDocs Architecture Spec Page, GitHub Actions Docs Deploy Workflow, MkDocs Site Configuration

### Community 50 - "Lunr Greek"
Cohesion: 0.33
Nodes (6): MkDocs Material Documentation Site, Documentation Site 404 Page, subagent-fleet Favicon (Person Reading Book Icon), subagent-fleet Documentation Site Home, Future Roadmap Documentation Page, Architecture (SPEC) Documentation Page

### Community 52 - "Lunr Russian"
Cohesion: 0.33
Nodes (4): Unit tests for Fleet Dashboard UI events module., Tests for WarmupProgressEvent serialization., Verify SSE wire format has correct event name., TestWarmupProgressEvent

### Community 53 - "Lunr Telugu"
Cohesion: 0.70
Nodes (4): e(), n(), r(), t()

### Community 57 - "Lunr German"
Cohesion: 0.40
Nodes (3): generate_aider_config(), Path, test_generate_aider_config()

## Knowledge Gaps
- **14 isolated node(s):** `$schema`, `name`, `description`, `name`, `url` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `launch_dashboard()` connect `CLI Commands` to `CLI Entry Points & Trace`, `Fleet Dashboard Server`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `FleetConfig` connect `FleetConfig & Model Warmup` to `Node Discovery & Health`, `Plugin & Config Validation`, `LiteLLM Config Generation`, `CLI Commands`, `Fleet Dashboard Server`, `Code Generator Pipeline`, `Core Data Models`, `Config Loading & Errors`, `Claude Agent Generation`, `Lunr German`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `subagent-fleet Python CLI Tool (init/validate/discover/generate/warmup/status/doctor/clean)` connect `CLI Entry Points & Trace` to `CLI Integration Tests`, `Agent Role Examples`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `FleetConfig` (e.g. with `NodeDiscovery` and `AgentRoute`) actually correct?**
  _`FleetConfig` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `H()` (e.g. with `aa()` and `ca()`) actually correct?**
  _`H()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `I()` (e.g. with `Me()` and `oi()`) actually correct?**
  _`I()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `name`, `description` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._