# Jev decision-layer demos

Seven small Python demos isolate the decision in each proposed video recipe. The examples use hard-coded prompts, retrieval results, citations, tool descriptions, and traces. They print the classifier result and the next code-policy route.

The first demo compares Claude Haiku through OpenRouter with Jev. The remaining demos call only Jev. None calls Elasticsearch, Elastic Inference Service, a selected tool, or any write API.

## Setup

```bash
uv sync
```

Add TypeSafe and OpenRouter API keys to `.env`:

```dotenv
TYPESAFE_AI_API_KEY=your-typesafe-key
OPENROUTER_API_KEY=your-openrouter-key
```

The Jev scripts also accept TypeSafe's standard `TYPESAFE_API_KEY` environment variable. The OpenRouter key is required only for the Haiku comparison scripts.

## Run the demos

Run the four inference-router variants in this order:

```bash
uv run python scripts/01_inference_endpoint_router/01_haiku_serial.py
uv run python scripts/01_inference_endpoint_router/02_jev_serial.py
uv run python scripts/01_inference_endpoint_router/03_haiku_concurrent.py
uv run python scripts/01_inference_endpoint_router/04_jev_parallel.py
```

The third script submits four independent OpenRouter requests concurrently. The fourth submits four independent Jev `Choice` questions in one `system_one` request.

Run the remaining recipe demos:

```bash
uv run python scripts/02_input_and_retrieval_safety_gate.py
uv run python scripts/03_rag_relevance_threshold.py
uv run python scripts/04_citation_support_checker.py
uv run python scripts/05_zero_result_recovery_router.py
uv run python scripts/06_tool_and_skill_selector.py
uv run python scripts/07_agent_trace_outcome_verifier.py
```

The router variants share `routing_scenario.py` so every mode receives the same requests, instructions, and route definitions. Each remaining recipe keeps its example state, Jev question, policy, and printed outcome in one file.

### Script 1 comparison

| Script | Classifier calls | Concurrency |
| --- | ---: | --- |
| `01_haiku_serial.py` | 4 | Serial HTTP requests |
| `02_jev_serial.py` | 4 | Serial `system_one` requests |
| `03_haiku_concurrent.py` | 4 | Concurrent HTTP requests with `asyncio.gather` |
| `04_jev_parallel.py` | 1 | Four Jev questions evaluated independently in one request |

Each script runs its mode five times while reusing one client. It reports every wall time, the mean and range, API calls per run and in total, mean token usage, route consistency, and cost. OpenRouter supplies Haiku's cost in each response. The Jev scripts calculate cost from response token usage using TypeSafe's [Jev 1.13 price](https://docs.typesafe.ai/models), verified on 2026-09-24: $0.042 per million input tokens and no output-token charge. Calculated costs are estimates rather than billing records.

There is no unmeasured warm-up, so the first measured run includes initial connection setup. The results describe that machine, network path, and provider state. They are not general provider benchmarks.

### Script 1 model routes

Script 1 uses three generally available EIS model IDs verified against Elastic's catalog on 2026-09-24:

- `anthropic-claude-4.5-haiku` for narrow, high-throughput work
- `anthropic-claude-4.6-sonnet` for balanced repository work
- `anthropic-claude-4.6-opus` for extended reasoning

Elastic's [supported-model catalog](https://www.elastic.co/docs/explore-analyze/elastic-inference/eis-supported-models) confirms the IDs and availability. Elastic's [Agent Builder model guidance](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/models) places these models in its high-throughput, balanced-performance, and extended-reasoning examples. The script uses this three-model subset rather than reproducing the full EIS catalog.

## Boundaries

- The safety gate is a classifier, not a security boundary.
- The citation checker tests whether one passage supports one atomic claim. It is not a general hallucination detector.
- EIS model invocation, retrieval, authorization, tool execution, and side effects stay outside these demos.
- The thresholds are illustrative. Production thresholds require labeled examples and calibration against the selected Jev model version.
