# Weekly Status Report — Intoxalock Removal Device Project

**Week of:** July 6–10, 2026
**Prepared by:** Sebastian Buitrago Toro

## Summary

This week was foundational rather than feature-facing, and deliberately so: before building out the voice agent itself, the priority was putting a solid, repeatable engineering base in place — a monorepo scaffold with clear conventions, a repeatable spec-to-code workflow, and a working example Lambda that every future piece of this system (including the AWS orchestration layer) will be built on the same way. With that base in place, the "Daisy" voice agent (the service-center scheduling call) was then built entirely as version-controlled code rather than configured by hand in the ElevenLabs dashboard, and a first test suite was created and used to compare AI models for quality and speed.

## 1. Project architecture and conventions

The codebase is organized as a single monorepo containing everything the project needs: individual deployable services ("apps," each typically one AWS Lambda), shared libraries used across services, and centralized infrastructure-as-code. This keeps related work in one place and avoids the coordination overhead of managing many small repositories.

Each service follows a hexagonal architecture — business logic sits at the center, isolated from AWS and framework details, with clearly defined boundaries for how data comes in and out. Within a service, features are built as vertical slices: each feature owns its own logic end-to-end, which lets us add or change one feature without risking side effects in another.

Testing follows a "trophy" shape: rather than a large, slow, and brittle suite of full end-to-end tests, most coverage lives in fast integration tests that exercise real behavior against a real (or realistic local) data store, complemented by a thin layer of unit tests for core business logic. This gives strong confidence with a fast, low-maintenance suite.

Finally, we standardized on a common set of API conventions (REST resource naming, consistent error responses, pagination, versioning) and code-quality gates (linting, type-checking, import boundaries, automated tests) that every service must pass before it's considered done. These conventions are documented in the project so any future engineer — or AI assistant — builds new features the same way, automatically.

## 2. Project harness and workflow definition

To keep delivery predictable, the project uses a structured, four-step workflow for building any new feature, one vertical slice at a time:

1. **Specification** — a rough request is refined into a clear, testable written spec, with edge cases and decisions captured up front.
2. **Scenario authoring** — the spec is broken into small, shippable slices, and each slice gets concrete, human-readable test scenarios (in Gherkin/plain-English form) that are reviewed and approved before any code is written.
3. **Build** — each slice is implemented test-first against its approved scenarios, following the architecture and conventions above, with progress logged as it goes.
4. **Independent review** — a separate reviewer checks the finished slice against its scenarios and the architecture rules, and only approves it once the automated gates pass.

This harness ensures nothing gets built without an agreed spec, nothing ships without tests that were written down and approved beforehand, and every finished piece is reviewed by a second pass before being considered complete. It's the same discipline we'll apply to every future feature on this project, including the voice agent itself.

The `apps/todo-lambda` app was built this week purely as a worked example of this whole process end-to-end — spec, slices, tests, build, review — so it can serve as a reference template for how real features should be built going forward.

## 3. ElevenLabs service-center agent, defined as code

The original proof-of-concept for "Daisy" (the agent that calls a service shop to confirm an Intoxalock removal appointment) was built by hand in the ElevenLabs web platform. This week, that entire definition — the conversation prompt, the tools the agent can call, the webhooks it triggers, and the success criteria it's graded against — was rebuilt as plain, version-controlled Python code.

Concretely, that means:

- The **prompt** is no longer a block of text living only in a dashboard; it's an authored, structured document in code that can be reviewed, diffed, and refined like any other project asset — and it has already gone through several rounds of tightening based on test results.
- The **tools** (saving the call outcome, detecting voicemail, ending the call) and the **webhook** that reports results back are all declared in code, not clicked together manually.
- One environment-independent definition is pushed to both a dev and a production agent via a repeatable command, so dev and prod can never silently drift apart the way hand-configured settings can.

The practical benefit: every change to how Daisy behaves is now a reviewable, revertible code change instead of a manual edit that's easy to lose track of.

## 4. Agent test suite, model comparison, and iteration

To validate Daisy's behavior before trusting her with real calls, a dedicated test suite was built covering the core scheduling flow, edge cases (ambiguous dates, garbled prices, a shop that stalls or gives non-answers), guardrails (refusing to leak customer information, resisting attempts to manipulate her instructions), and failure handling (the save step failing and needing a retry). Tests run against a live, simulated conversation, with an AI "shop" playing the other side of the call — this catches real conversational judgment, not just scripted responses.

Running this suite let us iterate quickly: several rounds of prompt refinements were driven directly by test failures, closing gaps such as how Daisy handles a shop that reverses a decision mid-call, or offers several times at once.

We also used the suite to compare underlying AI models for this task. Claude Sonnet produced the strongest conversation quality, but Claude Haiku 4.5 came very close on quality while responding noticeably faster — an important factor for a live phone call, where latency is directly felt by the person on the other end. Based on that trade-off, the agent is currently configured to run on Haiku 4.5, with continued testing to confirm it holds up as we expand coverage.

## Next steps

With the engineering base and the voice agent both in place, the next phase is building the AWS orchestration layer described in the Solution Architecture document: a **Confirmation Orchestrator** built on AWS Step Functions, with one long-running execution per removal request. It will coordinate the full lifecycle — waiting until the service center is open, calling the center through Daisy, handling the customer's decision when the center offers alternative times, generating the work order on confirmation, sending the appointment reminder, and escalating to a human representative only on genuine exceptions. This includes standing up the supporting pieces: the reusable Outbound Call Service (concurrency-capped, retried calling), the DynamoDB stores for request state, attempt history, and call capacity, and the four integration contracts with Intoxalock's systems (request intake, appointment confirmation, alternative-slot notification, and escalation).

We'll also continue expanding the agent test suite into the scenarios currently flagged as pending policy decisions (e.g., voicemail handling, AI-disclosure requirements, do-not-call requests) as we align on the desired behavior for each — this feeds directly into the orchestrator's center-confirmation stage.
