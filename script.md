---
type: Script
title: "How to Jevlevate your app"
status: draft
timestamp: 2026-09-25
---

# Video brief

**Working title:** How to Jevlevate your app

**Alternative titles:**

- [n] ways Jev can boost your app today
- Jev - the missing decision layer in your app
- [n] ways to add Jev to your Elasticsearch app

# Video script

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

This one is for the beginning of the pipeline - before anything reaches your main model, to prevent prompt injection attacks.

Prompt injection works by someone inserting a malicious prompt to override your instructions. The injector might be trying to do something like extract sensitive information, like credentials or personal information, or something as simple as just trying to get free use of an LLM.

This can come in the form of the input, like in a chatbot input box, or by contaminating a data store, so that they can poison the retrieved context.

So, here's what you can do with Jev.

[open `scripts/02_input_and_retrieval_safety_gate.py`]

I've got four tiny examples here: a normal refund question, a user asking for a service-account password, a normal policy passage, and a retrieved passage containing a fake `SYSTEM` instruction.

For each one, Jev answers two Noul questions: is this trying to override instructions, and is it trying to extract credentials?

[show `QUESTIONS`, then run the script]

You can see that the two ordinary examples are classified to go through the normal controls, while the other two go to review. Since these options are predetermined and provided to Jev, you can easily plug this into your program control flow as a quick, and cheap screening tool, as an additional security layer.

---

## Recipe 3: Reject retrieval results that are topically similar but useless

Next, let's move one step further into a RAG pipeline.

One common issue with search is that results can be returned because it shares the right words, but not be super useful for answering the question.

Here's how Jev can help to screen those responses.

[open `scripts/03_rag_relevance_threshold.py`]
Here, the question is: "How long do I have to return an unopened item?"

Imagine that the retriever, like Elasticsearch, returned these chunks from your database.

They're all plausible, but not quite. One passage is about returns, another is about international shipping and the third is about refunds.

You could get all these results into the LLM or the agentic chatbot, but - let see what we can do with Jev.

We can actually just ask Jev for a Noul - does this text directly help answer the query?

And if I run this:
[run the script; highlight include, exclude, exclude]

It correctly says hey, the returns chunk is relevant, so include that, but exclude the other.

Elasticsearch does the fast retrieval. Jev can then act as a second stage filter, to make sure that we don't pollute the LLM's context window in the next stage, and save money on token costs.

---

There are others in this repo that you can ask Jev to do - like:

[show `scripts/04_citation_support_checker.py`]
Check whether a citation actually provides support for a particular claim - so, for example, you're building an agentic research bot, and you're trying to see whether the original citation actually supports a claim.

You could get it to decide whether it `supports`, `contradicts` the claim, or actually if it's `not_addressed`.

When I run the script - you see Jev suggest the likelihood of each choice.

[show `scripts/05_tool_and_skill_selector.py`]
You can also imagine that instead of using an LLM, you could use Jev to trigger the right skill, or the right tool call.

[run code]
This could be another choice like I've set up here; where for each request, Jev selects one skill or tool that best suits the request.

Alternatively, you could set this up as a Noul, if you wanted Jev to judge for each tool or skill, whether it should be invoked the task.

[show `scripts/06_agent_trace_outcome_verifier.py`]
You can also imagine having Jev go through your observability outputs - like agent traces, and classifying them so you can review them faster in the future.

[run code]
Here, for example - I'm basically tagging certain messages in traces, to identify whether the requested outcome was completed,

---

## Draft wrap-up

So, to wrap up - Jev is an excellent tool to have in your tool kit.

Like that language "Probably" suggests, it's great for all those awkward jobs where ordinary rules aren't quite semantic enough, but a general-purpose LLM is doing far more work than you need.

You can use it with a simple, predictable pattern - give Jev a compact piece of state, define the possible answers up front, and extract the output back into a normal deterministic workflow.

If the task needs free-form writing, deep planning, or a chain of reasoning - use an LLM.

But if you can say, "Here are the valid answers; tell me which one fits this text," then Jev is probably worth trying.

I've put all the runnable demos, including the Haiku comparison, in the repository linked in the description.

These were some simple demos - but I'd love to see what you've been building with Jev - let me know in the comments. And if this was useful, give us a like - it helps other people find the video.

Thanks for watching, and I'll see you next time.
