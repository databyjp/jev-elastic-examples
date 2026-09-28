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

The core concept behind model routing is to use the right tool for the job. If you have something simple, like a query rewrite or basic summarisation - send it to a small model, like a Anthropic Haiku, GPT Luna, or a DeepSeek flash.

But if you need something that requires complex reasoning, like planning out a big software refactor - well let's send that to a large model, like an GPT Sol, Anthropic Opus or Kimi-K3.

A lot of people do this with a lightweight LLM, like Claude Haiku.

Here's an example that I slopped together.

[Show `ROUTING_INSTRUCTION` in `scripts/01_inference_endpoint_router/routing_scenario.py`]
First, I set up the task for my model, which is for it to find the least capable,
or, smallest, model that can handle a given task

[Show `ROUTE_CRITERIA` in `scripts/01_inference_endpoint_router/routing_scenario.py`]
Then, I have some basic rules here on which models to use for what type of task,
in increasing complexity.

Here I also actually have a "human review" criteria, too -
maybe it's something that I don't want to delegate at all.

[Show `CODING_AGENT_REQUESTS` in `scripts/01_inference_endpoint_router/routing_scenario.py`]
And then I've got some simple prompts here, which we'll ask our LLM to route for us.

So I just send this to my inference provider - `openrouter` in this case,
and in this function [show `openrouter_payload`], I request for it to emit
`json_schema` so that theoretically, I can parse it and plug it back into my control flow.

Let's run this. I've got it set up to run multiple times, so we can get some basic stats.

And we see it takes about 5 seconds, and about 0.2 cents per run. So it's not bad - 0.2 cents isn't a lot of money. But also, this isn't a big job - and if you're serving millions of users - each user making multiple requests - stuff like this adds up pretty quickly.

So let's see the same thing, with Jev.

[open `scripts/01_inference_endpoint_router/02_jev_serial.py`]
The inputs for Jev is actually pretty similar -

[show `MODEL_ROUTING_QUESTION`]
so we set up this `MODEL_ROUTING_QUESTION` object here,
which uses the same ROUTING_INSTRUCTION and ROUTE_CRITERIA as what we gave Haiku.

Then for each of the same scenarios from `CODING_AGENT_REQUESTS` that we used for Haiku,
we instantiate a `TypeSafeClient` client, and run a request with this `client.system_one` method,
passing the `MODEL_ROUTING_QUESTION` that we just set up

The rest of the code here is just me keeping count of the tokens - and tracking the results.

When I run this with Jev, I get the exact same results here, across the same runs - makes sense since this is a fairly contrived task;

BUT - this is the cool part - it did it around 1 second per task, whereas Haiku took about 5 seconds per task. And the cost was about 0.01c per task - about one twentieth of our cheap model!

If I did this with Sonnet or Opus, it would have been like five to ten times more expensive probably.

Now, let's talk about performance some more. Some of you might have been screaming at the screen - because I'm running these functions synchronously in a for loop.

Not great, since that means I'm paying for network latency in series. If you're using LLMs for model routing, you'd make use of concurrency - for example,

[show `scripts/01_inference_endpoint_router/03_haiku_concurrent.py`]
you could use an async library like asyncio, like I've done here, and just gather the responses like so.

If I run this, you'll see that each run now occurs in around 1.5 seconds, which is much faster, and makes sense, since the four requests are now getting sent concurrently rather than in series.

Now, with Jev, there's actually an even neater trick.

If we take a look at this script here
[Show `scripts/01_inference_endpoint_router/04_jev_parallel.py`] -

we build this `questions` dictionary first with all the questions, and then each request to TypeSafe just includes all of them, at once.

Meaning that I only pay for the network latency once - I don't even need to deal with any concurrency to minimise its impact.

So if I now run this - each run takes about a quarter of a second!

And the cost is even lower, with - I think each run being about seven thousandth of a cent.

And I will note that for these tasks, Jev and Claude Haiku gave the exact same answers.

This is why people like Jev so much.

For the right job, Jev can be significantly faster to run, and significantly cheaper to run - than an LLM. And you'll probably get quite similar results to running an LLM.

So - what *are* the right jobs?

The sweet spot is a semantic decision where you already know the shape of the valid answers.

Like yes-or-no probability, one option from a fixed list, or a score against a rubric.

The big difference with an LLM, though, is that the task, or the *quote* "mental load" needs to be relatively straightforward.

Think about it like this - if you need a model to do lots of reasoning, do maths, or write some code before spitting out an answer, that's probably not a Jev job.

But if you need a structured output like what we discussed, from unstructured text, Jev is great.

With that in mind, let's take a quick look at a few more examples where you can use this pattern.

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
