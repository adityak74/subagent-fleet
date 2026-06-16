# Future Roadmap Proposal for subagent-fleet (Generation 3)

*Updated: Late 2026*

With the core orchestration layer, Aider/Claude Code support, and advanced features (WoL, Sandboxing, HITL) completed in `v0.1.2`, `subagent-fleet` has matured into a production-grade local coordinator. 

Based on the latest trends and pain points discussed in `r/LocalLLaMA` and the broader AI community, the "Generation 3" frontier focuses heavily on **token efficiency, zero-trust security, and hybrid deployments**.

Here is the proposed roadmap for the next evolution of `subagent-fleet`, complete with citations from the community.

---

## 1. Cross-Agent KV Cache Sharing (High Priority)
**The Demand:** Multi-agent systems are "token eaters." A research-style swarm can burn 15x more tokens than a single-agent interaction [1]. If a planner agent reads a massive 100k-token repository, the implementer agent currently has to re-ingest that entire context, burning massive amounts of compute and time. The community is requesting frameworks that allow agents to share a "base" KV cache (from a shared model backbone) to save VRAM and eliminate redundant pre-filling [2].
**The Solution:**
- Implement deep integration with engines like **vLLM** and **TensorRT-LLM** that support prefix caching.
- Add a `context_pool` feature in `fleet.yaml` that allows agents running on the *same node* to share their prompt context automatically, slashing time-to-first-token (TTFT) for chained tasks.
- **Citations:**
  - [1] *r/LocalLLaMA discussions on "Context Debt and Token Burn" in multi-agent orchestration.*
  - [2] *Emerging frameworks like TokenDance and LRAgent pushing for multi-LoRA KV sharing.*

## 2. Hybrid Cloud "Tiered" Routing (High Priority)
**The Demand:** Enterprises and power users want a "Local Orchestrator + Cloud Frontier" model. They want orchestrators capable of routing PII-sensitive or trivial tasks to local models (e.g., Llama-4-8B on an M4 Mac) while delegating highly complex architectural reasoning to cloud models (e.g., Claude 3.7 or GPT-5) [3].
**The Solution:**
- Update `subagent-fleet` discovery to support external cloud providers (Anthropic, OpenAI) via the LiteLLM gateway.
- Allow agents in `fleet.yaml` to specify fallback cascades: e.g., `model: claude-3-7-sonnet`, `fallback: heavy-local-coder`. If the cloud provider goes down or limits rate usage, the fleet seamlessly fails over to the local multi-GPU server.
- **Citations:**
  - [3] *Discussions in r/LLMDevs on the economics and privacy compliance (ISO 42001) of Edge Hybrid architectures.*

## 3. Zero-Trust Agent-to-Agent (A2A) Security (Medium Priority)
**The Demand:** As agents dynamically delegate tasks, the "least-privilege principle" becomes difficult to enforce. A single hallucinated or compromised agent (e.g., via prompt injection from a malicious PR) can propagate unauthorized access across the entire swarm, potentially executing malicious bash commands [4].
**The Solution:**
- Introduce a **Zero-Trust Message Bus** within the subagent-fleet proxy.
- Before a message is passed from a `researcher` agent to an `implementer` agent, `subagent-fleet` intercepts and sanitizes the inter-agent payload to prevent multi-hop prompt injection.
- Add Role-Based Access Control (RBAC) definitions in `fleet.yaml`, explicitly defining which agents are allowed to invoke specific tools or MCP servers.
- **Citations:**
  - [4] *Industry security reports (e.g., Knostic AI) and community concerns on malicious A2A prompt injections.*

## 4. Namespaced Agent Memory & RAG (Medium Priority)
**The Demand:** Long-running agent fleets suffer from "context bleed" when using a single global shared memory pool. Conflicting instructions or stale facts from one agent disrupt the logic of another [5]. Users want isolated SQLite databases per agent, with strictly "opt-in" shared memory channels [6].
**The Solution:**
- Build a lightweight, native SQLite memory manager in `subagent-fleet`.
- Configure `memory_namespace: isolated` or `shared_pool_id` in `fleet.yaml`. This ensures the `planner` agent has a dedicated scratchpad that the `reviewer` agent cannot accidentally overwrite, while still allowing them to push final decisions to a common bulletin board.
- **Citations:**
  - [5] *GitHub feature requests on projects like Mem0 and Hermes Agent regarding isolated memory databases.*
  - [6] *r/LocalLLaMA threads on race conditions in cyclic multi-agent graph workflows.*

---

## ✅ Completed Milestones (Generation 1 & 2)
The following features have been fully implemented (up to `v0.1.2`):
- **Gen 1:** Discovery, routing, LiteLLM/Claude Code generation, unified observability (LangSmith/Langfuse).
- **Gen 2:** Aider support, Wake-on-LAN power management, Sandboxed Workspaces, HITL Middleware, dynamic routing hooks, and state fallbacks.