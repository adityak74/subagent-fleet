# Future Roadmap Proposal for subagent-fleet

*Updated: Mid-2026*

With the core orchestration layer, Aider/Claude Code support, and basic distributed routing completed, `subagent-fleet` has solved the "how do I route agents to machines" problem. Based on current trends in the local AI community, the next frontier of challenges revolves around **efficiency, reliability, and safety** in multi-agent systems.

Here is the proposed roadmap for the next major iterations of `subagent-fleet`, complete with citations from the community.

---

## 1. Power Management & Wake-on-LAN (WoL) (High Priority)
**The Demand:** As discussed frequently in `r/LocalLLaMA`, users are struggling with the electricity costs of running multi-GPU servers 24/7. High-end setups (like 3x Tesla P40s or dual RTX 4090s) can draw 116W+ just idling, whereas a Mac Mini idles at ~5W [1]. Users are currently hacking together custom "Wake Proxies" to suspend their heavy GPU nodes until an API request comes in [2].
**The Solution:**
- Introduce a `wake_on_lan` configuration block in `fleet.yaml` for specific nodes.
- When LiteLLM receives a request bound for a sleeping node, `subagent-fleet` intercepts the request, sends a Magic Packet to wake the machine, waits for a heartbeat, and then forwards the request.
- **Citations:**
  - [1] *r/LocalLLaMA discussions on cluster power consumption (2025/2026).*
  - [2] *Community workarounds utilizing KEDA/Kubesnooze or custom Raspberry Pi proxies for Ollama.*

## 2. Isolated Execution Workspaces (Sandboxing) (High Priority)
**The Demand:** Developers scaling multi-agent systems report that having multiple autonomous agents (like Claude Code or Aider) run shell commands in the same repository leads to conflicting edits, broken environments, and "debugging chaos" [3]. There is a growing demand for features akin to VS Code's "Agent HQ", which spins up dedicated Git worktrees for agents [4].
**The Solution:**
- Add a `subagent-fleet workspace` feature that automatically maps local subagents into isolated Docker containers or temporary Git Worktrees.
- When an agent is routed to a specific node, it operates within a temporary clone. Once the reviewer agent approves the changes, they are merged back.
- **Citations:**
  - [3] *r/LLMDevs & r/LocalLLaMA discussions on multi-agent "glue code" and environment contamination.*
  - [4] *Emerging industry standards for agent isolation (e.g., Microsoft Agent Framework).*

## 3. Human-in-the-Loop (HITL) Middleware (Medium Priority)
**The Demand:** Users suffer from "black box" execution fear. A common failure mode is an early "researcher/planner" agent hallucinating a bad plan, which cascades to an implementer agent that writes hundreds of lines of useless code [5]. The community is actively requesting standardized "hook points" to validate agent plans *before* execution [6].
**The Solution:**
- Implement deterministic pause hooks natively in the LiteLLM/subagent-fleet proxy. 
- Allow users to define `require_approval: true` in `fleet.yaml` for specific agents. The trace dashboard will pause execution and await a "Y/N" keystroke from the developer before passing the plan forward.
- **Citations:**
  - [5] *r/LocalLLaMA threads on error propagation in long-running autonomous chains.*
  - [6] *Requests for standard Human-in-the-Loop middleware in open-source orchestrators.*

## 4. Fleet Benchmarking & Evals (Medium Priority)
**The Demand:** Users are guessing their model allocations (e.g., "Is an 8B model enough for this task, or do I need to wake up the 70B model?"). There is a lack of localized, workflow-specific evaluation tools for clustered Ollama instances.
**The Solution:**
- Build a `subagent-fleet eval` command.
- Users provide a small JSONL dataset of their own prompts. The CLI runs these against different models in the fleet and generates a benchmark report, helping users mathematically optimize their node assignments.

## 5. Visual Fleet Topology Dashboard (Long-Term)
**The Demand:** As users build systems with 10+ agents across 5+ machines using cyclic workflows (like LangGraph), CLI YAML configurations become too difficult to visualize and manage.
**The Solution:**
- A lightweight local web UI (React + FastAPI) that visualizes the `fleet.yaml` as a node graph. 
- Users can drag-and-drop agents onto different machines, monitor live VRAM usage, and view live trace paths.

---

## ✅ Recently Completed
The following highly requested features have been successfully implemented and released in v0.0.4 - v0.0.7:
- **Unified Observability:** Langfuse, LangSmith, OTel integration and live `trace` TUI.
- **Aider Integration:** Native mapping of Architect/Editor modes.
- **MCP Generation:** Automatic `mcp.json` generation for tool sharing.
- **Distributed Inference (v1):** Discovery and routing for non-Ollama engines (vLLM, Exo, llama.cpp RPC).
- **Dynamic Routing:** Semantic python hooks to override static assignments based on prompt complexity.
- **State Persistence:** Automatic failover generation if heavy nodes go offline.