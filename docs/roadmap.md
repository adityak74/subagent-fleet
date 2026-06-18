# Future Roadmap Proposal for subagent-fleet (Generation 4)

*Updated: Early 2027 Projections*

With Generation 3 successfully released (KV Cache Sharing, Hybrid Routing, Zero-Trust A2A Security, and Namespaced Memory), `subagent-fleet` has resolved the major bottlenecks of structured, hierarchical agent workflows. 

However, looking ahead at bleeding-edge research and power-user discussions across the `r/LocalLLaMA` and `r/LLMDevs` communities, the paradigm is shifting again. The rigid "Supervisor -> Worker" model is giving way to **decentralized, peer-to-peer swarm intelligence**. 

Here is the proposed "Generation 4" roadmap for `subagent-fleet`.

---

## 1. Decentralized "Blackboard" Architecture (High Priority)
**The Demand:** In complex local setups, the "Supervisor" agent becomes a massive bottleneck and a Single Point of Failure (SPOF). Small local models (e.g., 8B parameters) struggle to synthesize outputs from 5+ specialized subagents, leading to "computational traffic jams" [1]. Users want to move to a peer-to-peer "Blackboard" pattern where agents broadcast intermediate results to a shared pool, and other agents react autonomously based on local triggers [2].
**The Solution:**
- Deprecate rigid point-to-point delegation chains.
- Introduce a `subagent-fleet blackboard` daemon. Agents write structured outputs (Markdown/JSON) to this shared state. Other agents subscribe to specific triggers (e.g., the `reviewer` agent automatically wakes up when a `coder` agent posts a "PR_READY" event to the blackboard).
- **Citations:**
  - [1] *Community discussions on Supervisor bottlenecks in Swarm frameworks.*
  - [2] *Emerging multi-agent patterns in frameworks like SwarmSys (Explorers, Workers, Validators).*

## 2. GPU Microscheduling for Parallel Swarms (High Priority)
**The Demand:** While swarms are theoretically parallel, local hardware (like a single RTX 4090 or Mac Studio) forces these requests to process serially. Running 4 agents simultaneously causes VRAM out-of-memory (OOM) errors or massive latency spikes [3]. 
**The Solution:**
- Build a native **GPU Microscheduler** into the `subagent-fleet` proxy layer.
- Instead of raw pass-through to LiteLLM, `subagent-fleet` queues inter-agent requests, monitors live VRAM via `ollama ps` or `vllm metrics`, and dispatches agent inferences only when compute cycles are available, dynamically adjusting `max_parallel` limits on the fly.
- **Citations:**
  - [3] *r/LocalLLaMA feature requests for handling parallel inference batching in local swarms.*

## 3. Generative UI / Dynamic Rendering (Medium Priority)
**The Demand:** Terminal logs (even with rich tracing) are becoming insufficient to monitor 10+ autonomous agents. Users want the UI to be as dynamic as the swarm itself [4]. If a researcher agent finds tabular data, the UI should render a table; if a coder agent writes a patch, it should render a diff view.
**The Solution:**
- Expand the `subagent-fleet dashboard` to support **Generative UI**.
- Intercept agent outputs via Server-Sent Events (SSE) and stream them to the local React dashboard. Use a lightweight parsing model to dynamically render React components (Charts, Tables, Markdown, Diffs) based on the agent's current intent.
- **Citations:**
  - [4] *Discussions on Vercel AI SDK and the shift toward Generative UI in multi-agent systems.*

## 4. Markdown-Based State Persistence (Medium Priority)
**The Demand:** Relying on Redis or SQLite for state management is often seen as overkill or "too opaque" for local developers. If the orchestration layer crashes, the state is locked in a database [5]. Developers strongly prefer "Markdown-based state" that survives ephemeral session restarts and can be version-controlled in Git.
**The Solution:**
- Introduce `state_driver: markdown` in `fleet.yaml`.
- Instead of memory databases, `subagent-fleet` manages state by continuously updating `TASKS.md`, `DECISIONS.md`, and `CONTEXT.md` in a `.fleet_state/` directory. Agents read these files before acting, ensuring a "shared view of reality" that developers can easily read and edit by hand.
- **Citations:**
  - [5] *Community consensus on Aider/Claude Code workflows favoring human-readable context files over hidden databases.*

## 5. Dynamic Role Switching (Long-Term)
**The Demand:** Defining 30+ static agents in YAML is cumbersome. Users want agents that can monitor the environment and change their own system prompts [6]. For example, a "Coding Agent" that notices a backlog of untested code dynamically switches to a "Testing Agent" persona.
**The Solution:**
- Allow agents to mutate their own configurations via a specialized MCP tool (`fleet-config-editor`).
- This allows a swarm to self-balance—if research is done, 4 researcher agents can rewrite their own prompts to become implementer agents to help clear the coding backlog.
- **Citations:**
  - [6] *Research into Active Inference and self-balancing agent clusters.*

---

## ✅ Completed Milestones (Generations 1, 2 & 3)
The following features have been fully implemented (up to `v0.1.2`):
- **Gen 1:** Discovery, routing, LiteLLM/Claude Code generation, unified observability.
- **Gen 2:** Aider support, Wake-on-LAN power management, Sandboxed Workspaces, HITL Middleware, dynamic routing hooks, and state fallbacks.
- **Gen 3:** Cross-Agent KV Cache Sharing (vLLM prefix caching), Hybrid Cloud Tiered Routing, Zero-Trust Agent-to-Agent Security, and Namespaced Agent Memory (SQLite).