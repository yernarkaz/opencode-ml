# Model Selection Guide for ML Pipeline Agents

**Last updated**: June 2026  
**Pricing source**: [GitHub Copilot Models and Pricing](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)

---

## Pricing Reference (per 1M tokens)

### Anthropic Models

| Model | Input | Output | Category | Use case |
|---|---|---|---|---|
| **Claude Haiku 4.5** | $1.00 | $5.00 | Versatile | Structured output, instruction-following, deterministic tasks |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | Versatile | Code generation, pattern compliance, general-purpose |
| **Claude Opus 4.8** | $5.00 | $25.00 | Powerful | Deep reasoning, architecture decisions, complex trade-offs |

### OpenAI Models (alternatives)

| Model | Input | Output | Category | Use case |
|---|---|---|---|---|
| GPT-5.4 nano | $0.20 | $1.25 | Lightweight | Ultra-cheap, simple tasks |
| GPT-5 mini | $0.25 | $2.00 | Lightweight | Cheap, lightweight tasks |
| GPT-5.3-Codex | $1.75 | $14.00 | Code-optimised | Code generation (42% cheaper than Sonnet) |
| GPT-5.4 | $2.50 | $15.00 | Versatile | General-purpose, reasoning |
| GPT-5.5 | $5.00 | $30.00 | Powerful | Deep reasoning, complex tasks |

---

## Current Agent Assignments

| Agent | Model | Steps | Rationale |
|---|---|---|---|
| **ml-orchestrator** | Claude Haiku 4.5 | 40 | Pure routing, table-driven dispatch. No code, no reasoning. |
| **ml-experiment-planner** | Claude Opus 4.8 | 20 | Sequential-thinking MCP, architecture trade-offs, reasoning depth critical. |
| **ml-code-builder** | Claude Sonnet 4.6 | 60 | Pattern-compliant code generation, leakage guards, test execution. Reliability > cost. |
| **ml-code-reviewer** | Claude Haiku 4.5 | 20 | Fixed checklist, deterministic pass/fail. No generative complexity. |
| **ml-data-analyst** | Claude Haiku 4.5 | 20 | Tool-driven profiling. Model only formats 5-section markdown. |
| **ml-autoresearch** | Claude Sonnet 4.6 | 200 | Autonomous loop, code edits, git ops, error recovery. Reliability critical. |

---

## Decision Framework

### When to use Claude Haiku 4.5 (3× cheaper)

✅ **Use Haiku when:**
- Task is deterministic (fixed checklist, structured output)
- Model is primarily instruction-following (routing, formatting)
- Tool does the heavy lifting (profiling, analysis)
- No code generation required
- Temperature ≤ 0.2 (low creativity)
- Steps ≤ 20 (short, focused interactions)

❌ **Don't use Haiku for:**
- Code generation with strict patterns
- Complex reasoning or trade-off analysis
- Tasks requiring deep context understanding
- Multi-step reasoning chains

### When to use Claude Sonnet 4.6 (baseline)

✅ **Use Sonnet when:**
- Code generation is required
- Pattern compliance is critical (str_to_bool, leakage guards)
- Task involves test execution or validation
- Long-running loops (> 50 steps)
- Reliability is more important than cost
- General-purpose capability needed

❌ **Don't use Sonnet for:**
- Pure routing or formatting (use Haiku)
- Deep reasoning tasks (use Opus)
- Ultra-cheap tasks (use GPT-5 mini/nano)

### When to use Claude Opus 4.8 (1.67× more expensive)

✅ **Use Opus when:**
- Deep reasoning is required (architecture decisions, trade-offs)
- Sequential-thinking MCP is used
- Task involves multiple interacting variables
- Configurable reasoning levels needed
- 1M context window required
- Quality of reasoning directly impacts output

❌ **Don't use Opus for:**
- Deterministic tasks (use Haiku)
- Code generation (use Sonnet)
- Simple routing (use Haiku)

---

## Cost Optimization Strategies

### Strategy 1: Task-specific model selection (current approach)

Assign the cheapest model that meets the task's quality requirements.

**Pros:**
- Maximizes cost savings
- Maintains quality where it matters
- Fine-grained control

**Cons:**
- Requires careful task analysis
- More configuration to maintain

**Estimated savings**: ~35% per typical session

### Strategy 2: Tier-based assignment

Use one model per tier (lightweight, versatile, powerful).

**Pros:**
- Simpler to manage
- Fewer model changes

**Cons:**
- Less cost optimization
- May overpay for simple tasks

### Strategy 3: Hybrid (recommended)

- **Haiku** for deterministic, tool-driven, routing tasks
- **Sonnet** for code generation and general-purpose
- **Opus** for deep reasoning only

---

## Monitoring and Adjustment

### Metrics to track

1. **Cost per session** — compare actual vs. baseline
2. **Quality degradation** — monitor for Haiku-related failures
3. **Reasoning quality** — assess Opus improvements for planner
4. **Latency** — Haiku is faster; Opus may be slower

### When to reconsider assignments

- If Haiku tasks start failing (move to Sonnet)
- If Opus reasoning doesn't improve outcomes (move to Sonnet)
- If new pricing emerges (re-evaluate all assignments)
- If task complexity changes (adjust model tier)

---

## Important Notes

### Claude Sonnet pricing is flat

Claude Sonnet 4, 4.5, and 4.6 are **identically priced** ($3 input / $15 output).
There is no cost benefit to "downgrading" within the Sonnet family.

### Retired models (as of June 2026)

The following models are no longer available:
- o3, o4-mini (retired Oct 2025)
- gpt-4.1 (retired June 2026)
- Claude Sonnet 3.5, 3.7 (retired Oct 2025)

Do not reference these in new agent configurations.

### Cache write costs

Anthropic models include a cache write cost (25% of input cost).
This is relevant for long-context tasks but negligible for typical agent interactions.

---

## Future Considerations

- Monitor for new model releases (GPT-6, Claude 5, etc.)
- Evaluate Gemini 3.5 Flash as a Haiku alternative
- Consider GPT-5.3-Codex for ml-code-builder (42% cheaper on input)
- Track Opus reasoning level impact on planner quality

