# Future Roadmap Proposal for subagent-fleet

Based on an analysis of community discussions (Reddit, HN, and the local LLM ecosystem) around multi-machine agent orchestration, Claude Code, and Aider, here is a proposed future roadmap for `subagent-fleet` to address the most requested features and pain points.

## 1. Unified Observability & Tracing (High Priority)
**The Problem:** Users report that debugging multi-agent, multi-machine workflows is extremely difficult. When a task hops from a planner on a Mac Mini to an implementer on a workstation, it creates a "blind spot."
**The Solution:**
- Generate OpenTelemetry or LangSmith/Langfuse configurations natively within the LiteLLM gateway setup.
- Build a lightweight `subagent-fleet trace` terminal dashboard that streams logs from LiteLLM, showing exactly which machine is executing which subagent in real-time.

## 2. Aider Configuration Generation (High Priority)
**The Problem:** While Claude Code uses subagents, many local-first developers prefer **Aider** for its Git-first approach and its native "Architect / Editor" mode (where a heavy model plans and a fast local model edits).
**The Solution:**
- Add `subagent-fleet generate --target aider`.
- Automatically generate `.aider.model.settings.yml` and routing configs that map the Aider "Architect" to a heavy node (e.g., 64GB Mac Studio) and the Aider "Editor" to a fast local node.

## 3. Model Context Protocol (MCP) Integration (Medium Priority)
**The Problem:** The community is rapidly adopting MCP to standardize how agents access tools. Users want agents on different machines to share access to the same tools seamlessly.
**The Solution:**
- Allow `fleet.yaml` to define MCP server endpoints.
- When generating Claude Code agent configurations (`.claude/agents/*.md`), automatically inject the required MCP tool instructions and routing logic so remote subagents can trigger local MCP tools.

## 4. State Persistence & Crash Recovery (Medium Priority)
**The Problem:** If an agent running on an external workstation crashes midway through a complex implementation, the entire chain fails and context is lost.
**The Solution:**
- Implement state checkpointing configurations.
- Allow `subagent-fleet` to generate fallback routes in LiteLLM (e.g., if the heavy workstation goes offline, fallback to a slower local model automatically without breaking the workflow).

## 5. Dynamic "Task-Based" Routing (Long-Term)
**The Problem:** Currently, `subagent-fleet` uses static routing (Agent A -> Model B). Users want a "Manager" agent that looks at a prompt and dynamically decides which node has the right capabilities for the task.
**The Solution:**
- Introduce a pre-routing classification agent in the LiteLLM proxy layer that analyzes the prompt complexity and routes it to either a fast node or a heavy node automatically, overriding static assignments if necessary.

## 6. Integrations with Distributed Inference Engines (Long-Term)
**The Problem:** Users want to pool VRAM across multiple machines (e.g., Distributed Ollama, Exo, or RPC llama.cpp) rather than just routing whole tasks to single machines.
**The Solution:**
- While `subagent-fleet` is an orchestration layer, it could add native discovery and health checks for `exo` or distributed `llama.cpp` clusters, generating the appropriate API base URLs for these unified endpoints.

---

## Action Items for Next Release
1. **Add Aider Support:** Update the generator to produce Aider configuration files alongside Claude Code markdown files.
2. **Implement Fallback Generation:** Update `generators/litellm.py` to support `fallbacks` in `litellm_config.yaml` based on `fleet.yaml` definitions.
3. **Build `subagent-fleet trace`:** A simple TUI using the `rich` library that hooks into LiteLLM's logging to show active agent runs across the fleet.