---
type: outline
title: "How to Jevlevate your app"
status: phase-1-structure
timestamp: 2026-09-25
---

# Video brief

**Working title:** How to Jevlevate your app
**Working title:**

**Alternative titles:**

- [n] ways Jev can boost your app today
- Jev - the missing decision layer in your app
- [n] ways to add Jev to your Elasticsearch app

# Video outline

## Opening: an LLM is often doing the job of an `if` statement

Let's talk Jev. TypeScript AI just launched Jev, and the hype and excitement has gone through the roof!

It's surprising to many, but maybe we shouldn't be.

Here's the thing. A lot of us spent spent the last two years integrating GenAI models to everything from our search applications, customer support chatbots, or even actual programming logic.

Some of those things even work amazingly well - agentic search is really, really, smart, chatbots are more capable than ever, although - not without problems, and programming logic that use to require a huge block of code can be solved by asking a generative model to "make a judgement".

But this last part - dealing with logical or selection problems with GenAI models, is still a bit... suboptimal.

One, it can be hard to get generative AI models to produce an output that you can plug into a control flow. You can ask the model to produce a structured file like a JSON, or a TOML, but at the end of the day, you're really just throwing that ball in the air and praying to the GenAI gods [picture of a Hail Mary pass].

It's against this backdrop that TypeSafe AI launched Jev, what they call a "System One" model.

At a high level, you can think of Jev as a lovechild between an old-school classifier model, and an LLM. Like an LLM, Jev can take any unstructured text as input. BUT, Jev's far more disciplined about its outputs, meaning that it can only output a decision format that you define ahead of time. Jev can output a "Noul" a probability for a yes-or-no question, a "Choice", which is one option from a closed list, or a "Score" against a rubric.

This is great, because it plugs directly into a mental model of how programs and control flows actually work. Steve Faulkner from Cloudflare even proposed a programming language wrapping Jev called "Probably" (https://x.com/southpolesteve/status/2100767781868150938) - although, as this commenter pointed out - it was a missed opportunity to call it JevaScript (https://x.com/NickGideo/status/2100816570003914755)!

The TypeSafe AI folks call Jev a "System One" model, like in Daniel Kahneman's book "Thinking, fast and slow" - because Jev's very good at making these decisions in a much faster time than LLMs.

And, just like Kahneman's System One thinking, Jev isn't very good at things that require reasoning.

So, in this video - let me show you some things that you can do with Jev right NOW.

---

Here's one that I think a lot of you will relate to, which is model routing.

## Recipe 1: Route coding tasks to the right model

### The problem

- A coding agent should not send every task to the same model.
- A localized test expectation does not need the same reasoning budget as an intermittent leader-failover race.
- Some requests should not reach a model at all. Rotating a production signing key and deleting the old key requires explicit approval and separate authorization checks.
- Use actual EIS model IDs for the three model routes:
  - `anthropic-claude-4.5-haiku`
  - `anthropic-claude-4.6-sonnet`
  - `anthropic-claude-4.6-opus`
  - `human_review`
  [show the four coding requests entering four named routes]

### The conventional LLM implementation

- Start with Claude Haiku 4.5 through OpenRouter as a realistic classifier baseline.
- Give Haiku the request, the same four route definitions, and a strict JSON Schema that permits only one `model_id`.
- Run one HTTP request per coding task in series.
  [screen recording: `01_haiku_serial.py`, focusing on the loop and structured-output payload]
- Explain what this approach provides and what it still does:
  - The JSON shape is constrained.
  - The model still generates a response token by token.
  - Four independent classifications require four serial round trips in this version.

### The serial Jev implementation

- Replace the system prompt and JSON Schema with one Jev `Choice` over the same routes.
- Send each coding request as state and read `response.choices["model"]`.
- Show the returned choice and full probability distribution. Do not interpret a high probability as authorization.
  [screen recording: `02_jev_serial.py`, then terminal output]
- Compare serial with serial. This isolates the classifier before introducing concurrency.

### When the application has several independent routing requests

- Explain the obvious LLM optimization. Independent Haiku calls do not have to wait for one another.
- Use `asyncio.gather` to submit four OpenRouter requests concurrently.
  [screen recording: `03_haiku_concurrent.py`, highlight `asyncio.gather`]
- Make the boundary explicit: this overlaps four HTTP requests and four model generations. It does not turn them into one inference request.

### Jev's one-request version

- Put all four coding requests into one shared state object.
- Create four `Choice` questions, each explicitly pointing to one request by index.
- Send the state and question map through one `system_one` call. Jev evaluates the questions independently and in parallel.
  [screen recording: `04_jev_parallel.py`, progressively highlight shared state, question map, and single call]
- Show the architectural difference rather than only the stopwatch:
  [diagram: Haiku async = four client requests → four generations; Jev = one client request → four independent typed questions]

### What the comparison shows

- Explain the measurement before showing the result:
  - Same four coding requests and route definitions.
  - Five measured runs through one reused client.
  - No hidden warm-up, so the first run includes initial connection setup.
  - Report every wall time, mean, range, request count, mean tokens, cost, and route consistency.
- Use the final recording pass as the authoritative result. Current validation snapshot:

  | Mode | Calls per run | Mean wall time | Observed range | Mean cost per run |
  | --- | ---: | ---: | ---: | ---: |
  | Haiku serial | 4 | 4.796 s | 4.098–5.491 s | $0.002451 |
  | Jev serial | 4 | 1.049 s | 0.912–1.380 s | $0.000102 |
  | Haiku concurrent | 4 | 1.326 s | 1.181–1.481 s | $0.002451 |
  | Jev, four questions in one request | 1 | 0.336 s | 0.244–0.655 s | $0.000073 |

  [show table as an editor overlay; do not read every number aloud]
- State the useful findings:
  - Haiku concurrency removes most of the serial waiting time.
  - Jev's one-request form reduces the application-level request count from four to one.
  - All twenty classifications in every mode agreed on the four selected routes in this hand-built sample.
  - Jev's parallel form uses fewer input tokens than four separate Jev requests because shared state and request overhead are sent once.
- State what the comparison does not prove:
  - Four hand-picked examples do not establish routing accuracy.
  - Local timing includes this machine, network, OpenRouter provider selection, and current service load.
  - OpenRouter reports Haiku's cost. The scripts calculate Jev cost from TypeSafe's documented price and token usage, so it is an estimate rather than a billing record.
  - The TypeSafe account accepts `jev-latest`; the script prints the resolved `jev-1.13.0` model used in the measured run.
  - Production routing still needs endpoint availability, cost ceilings, permissions, fallback behavior, and evaluation on labeled requests.

### Transition to the shorter recipes

- Name the repeated pattern established by the router: compact state, bounded question, probabilities, code policy, safe fallback.
- Tell the viewer the remaining recipes reuse that pattern at different points in an AI product, so they do not need four implementations each.
  [return to lifecycle graphic and move highlight to input and retrieval]

---

## Recipe 2: Screen user input and retrieved text separately

- Problem: both user messages and retrieved passages can contain instruction overrides or attempts to extract credentials. They enter the application through different paths and should remain separate cases.
- State: source type plus the supplied text.
- Jev questions: two independent `Noul` questions for instruction override and credential extraction.
- Code policy: if either score crosses the illustrative review threshold, route the text to review before use. Otherwise continue through the application's normal controls.
- Proof case: contrast an ordinary refund question with a user request to print a service-account password; then contrast a policy passage with a retrieved passage containing an injected `SYSTEM` instruction.
  [screen recording: `02_input_and_retrieval_safety_gate.py`, then four-row terminal result]
- Boundary: this is one classifier in a larger security design. It does not replace prompt isolation, access control, redaction, allowlists, or review.

---

## Recipe 3: Reject retrieval results that are topically similar but useless

- Problem: retrieval similarity can rank a passage highly because it shares words with the query, even when it does not answer the question.
- Example query: "How long do I have to return an unopened item?"
- Candidate contrast: a return-policy passage and an international-shipping passage both mention thirty days.
- Jev question: `Noul` asks whether this specific chunk directly helps answer this specific query.
- Code policy: include above the measured relevance threshold; exclude below it.
  [show three retrieved chunks with similarity implied, then Jev include/exclude labels]
- Elastic seam: Elasticsearch performs candidate retrieval and access filtering. Jev receives the query and compact candidate text after retrieval.
- Boundary: the script uses hard-coded candidates. It does not claim that Jev replaces retrieval, reranking, or evaluation of the complete RAG answer.

---

## Recipe 4: Check whether a citation supports one claim

- Problem: a generated answer can attach a real citation to a claim the cited passage does not establish.
- State: one atomic claim and one located citation passage.
- Jev question: `Choice` among `supports`, `contradicts`, and `not_addressed`.
- Proof cases:
  - A passage directly supports the return-window claim.
  - A passage contradicts the opened-item claim.
  - A passage says nothing about free return shipping.
  [show claim-evidence matrix with one row per verdict]
- Code policy: allow the supported claim, revise or reject the contradicted claim, and send the unaddressed claim through a missing-evidence path.
- Boundary: code still owns citation IDs, exact quote lookup, and claim extraction. This is citation-support checking, not a universal hallucination detector.

---

## Recipe 5: Decide what to do after a zero-result search

- Problem: "zero results" is not one failure. A typo, acronym, active filter, ambiguous term, exact identifier, and genuine corpus gap need different responses.
- State: the query, known terms, and active filters.
- Jev question: one `Choice` over six named causes.
- Focus narration on contrasting outcomes rather than reading all six:
  - `refnd polcy` → offer a spelling correction.
  - `enterprise audit logs` with `plan:free` → suggest removing the conflicting filter.
  - `quantum fax integration` → log a corpus gap.
  [show all six routes in terminal output; visually emphasize the three narrated cases]
- Code policy owns the actual rewrite, filter change, clarification interface, exact-ID lookup, and gap logging.
- Elastic seam: this decision happens after Elasticsearch returns no hits and the application attaches deterministic query context.

---

## Recipe 6: Select a tool or skill, including no tool

- Problem: an agent with several tools or skills should not load or call one merely because its name resembles the request.
- State: one user request plus a bounded catalog of capability names and descriptions.
- Jev question: `Choice` among documentation search, account lookup, usage report, refund workflow, and `no_tool_or_skill`.
- Proof cases: route a public documentation question to search, a usage question to the report tool, a refund operation to the workflow skill, and a writing request to no tool.
  [show request → selected capability cards; end on the no-tool result]
- Code policy: use confidence only as an illustrative review signal. Code still validates parameters, permissions, and execution.
- Elastic seam: the same pattern can select an Agent Builder tool or skill description, but the script does not call Agent Builder.

---

## Recipe 7: Catch an agent that claims success after its tool failed

- Problem: an agent can look active and still fail the user's task. The final answer may even claim success after a failed tool call.
- Use the deliberately simple trace:
  - User asks for a duplicate charge refund.
  - Refund tool returns HTTP 403 and creates no refund.
  - Final message says the refund was processed.
- Deterministic preparation: code extracts the tool status and whether the refund record exists before Jev runs.
- Jev questions: separate `Noul` judgments for task completion, final-message support, and user dissatisfaction.
- Code policy: a deterministic tool error or unsupported success claim sends the run to priority review.
  [show trace waterfall: request → refund tool 403 → false success message → priority review]
- Add the expectation-gap contrast: the refund succeeds, but the customer remains unhappy about the delay. Completion and satisfaction must remain separate decisions.
  [split screen: silent failure versus completed-but-unsatisfying run]
- Elastic seam: Agent Builder traces can provide tool and model spans. Content capture requires explicit privacy settings, and any demo should use synthetic or approved redacted data.
- Boundary: Jev does not establish root cause, authorize remediation, or securely evaluate an unbounded hostile trace. Code normalizes exact facts and controls the review workflow.

---

## Wrap-up: use Jev for semantic decisions with a closed answer space

- Recap the seven positions in the product lifecycle:
  - Route the model.
  - Screen input and retrieved text.
  - Filter RAG evidence.
  - Check citation support.
  - Recover from zero results.
  - Select a tool or skill.
  - Verify the completed agent run.
  [show lifecycle graphic with all seven positions active]
- Give the suitability test:
  - The application can define the answer space before the request.
  - The hard part is a narrow semantic judgment over supplied text.
  - Code can retain arithmetic, authorization, side effects, and thresholds.
  - There is an explicit low-confidence, no-match, or human-review path.
  - A labeled evaluation set can test the question and policy.
- State where Jev does not fit: free-form generation, exact arithmetic, chronology, IDs, permissions, or an irreversible decision based on one probability.
- Point viewers to the repository containing all seven runnable demos and the four-way router comparison.
- End on a specific question: "What semantic `if` statement in your product would you move out of a general-purpose LLM first?"

# Visual assets needed

- **Decision-layer pattern:** A reusable four-stage graphic showing compact state, typed Jev question, code policy, and action or fallback. It needs variants that can highlight one stage while preserving the same semantic structure.
- **Seven-recipe lifecycle:** A product-flow graphic placing the seven recipes before model invocation, around retrieval, inside tool use, and after the completed agent run.

# Source references

- TypeSafe introduction: https://docs.typesafe.ai/
- TypeSafe models and pricing: https://docs.typesafe.ai/models
- Jev 1.13 limitations: https://docs.typesafe.ai/model-jaggedness/jev-1.13
- TypeSafe parallel-questions cookbook: https://docs.typesafe.ai/cookbooks/parallel_questions
- OpenRouter Claude Haiku 4.5: https://openrouter.ai/anthropic/claude-haiku-4.5
- OpenRouter structured outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- EIS supported models: https://www.elastic.co/docs/explore-analyze/elastic-inference/eis-supported-models
- Elastic Agent Builder model guidance: https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/models
- Elastic Agent Builder trace collection: https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/collect-traces
