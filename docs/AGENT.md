# HeatShift agent

HeatShift uses the **AWS Strands Agents SDK** with a real tool-calling model. The delivered route runs locally through Ollama with `qwen3:1.7b`; no paid inference or cloud provisioning is needed. The deterministic planner remains usable when the model is unavailable. A failed or unavailable model returns HTTP 503; there is no scripted agent fallback.

## Local model

Install the pinned application dependencies, start Ollama and download `qwen3:1.7b`. Set:

```sh
export HEATSHIFT_AGENT_PROVIDER=ollama
export HEATSHIFT_AGENT_MODEL=qwen3:1.7b
export OLLAMA_HOST=http://127.0.0.1:11434
```

The local provider means inference happens through the local Ollama server. Strands is the AWS open source agent framework; **local inference is not an AWS cloud deployment**. Qwen thinking is disabled with `think: false`; no model reasoning is displayed or returned.

## Optional Amazon Bedrock provider code (inactive)

The backend also contains a Bedrock provider adapter. It is not selected, provisioned, or used by the delivered local route. A future deliberate switch would require ordinary AWS credentials and a model enabled in the selected region:

```sh
export HEATSHIFT_AGENT_PROVIDER=bedrock
export HEATSHIFT_AGENT_MODEL=amazon.nova-lite-v1:0
export AWS_REGION=us-east-1
```

The model ID is an example, not a claim of account access. A supported regional model or inference profile may be needed. The application does not provision credentials or grant permissions. Bedrock errors are sanitized; account details and provider response bodies are not returned. Bedrock inference may incur account charges; provider selection is explicit.

The adapter was checked offline against the installed Strands 1.59.0 and botocore service models: construction and the four-tool `ConverseStream` request schema validated, with a mocked client and zero credential lookups or inference calls. This confirms SDK compatibility, not account entitlement, regional model availability, latency or pricing. No Bedrock request has been made for this verification.

`get_agent_status()` probes Ollama's installed-model list with a 1.5-second timeout and caches it for 10 seconds. Bedrock status checks credential configuration with a capped wait, not model inference. Actual entitlement and availability are checked on invocation.

## Tool workflow

1. `inspect_plan` reads the complete current plan and its constraints.
2. `inspect_weather` retrieves date/location-matching weather through the same weather service as the application; it returns provenance and warnings.
3. `propose_plan` receives a small field patch, merges it into the current plan and validates the **complete resulting PlanRequest**. This avoids generating an entire plan for a one-field change. It protects unrelated tasks, durations, windows, locks, shift, breaks and other controls, and captures a candidate in the request-local session only.
4. `optimize_plan` fetches/reuses the same real weather and runs the deterministic optimizer. It cannot manufacture temperatures or perform LLM arithmetic. Infeasible plans remain infeasible.

For a plain optimization request the model uses the existing constraints, without proposing arbitrary edits. For a constraint change it must validate a proposal and then optimize it. The model has no filesystem, shell, messaging, deployment or plan-approval tool.

Each trace entry is recorded inside an actually executed tool; a successful planning result comes from the deterministic optimizer. The UI receives compact summaries of these executions, never invented tool events. Returned message text is assembled from tool evidence instead of displaying unrestricted model output. This prevents unsupported safety percentages, invented weather, or model reasoning from entering the user interface.

The agent uses sequential tools, up to six initial model turns and one reserved verification turn, ten executed tool calls and bounded generated tokens. If a small model ends after proposing an edit, the same real Strands agent gets one explicit request to finish with `optimize_plan`; the application does not fake that tool call. After the optimizer returns a verified result, a Strands hook stops the loop before an unnecessary model call to paraphrase it. All of this shares one 85-second timeout. Tool failure, model failure, incomplete proposal verification or missing weather is shown honestly. No proposal is persisted; applying/accepting it is a separate human action in the UI. Even an unchanged constraint set is returned with a schedule preview for review.

## Edit safeguards and limits

Structural safeguards are conservative intent checks, not a universal natural-language parser. Deleting a task requires an explicit removal request naming that task. A request such as “make this cooler” cannot drop work, shorten durations, unlock jobs, extend the paid shift, remove breaks or rewrite the baseline. Task references must match an ID, full title or unique title word; a shared word such as “maintenance” is insufficient. Negated commands and preservation language are not permission to modify a field.

Explicit requests like “Garden maintenance can only start after 13:00” can change that task's window. Supported concrete shift start/end, task earliest/latest, lock and duration edits are checked against the candidate before optimization. A model that skips a requested edit cannot return the unchanged plan as a successful answer. Changed clocks must come from the supplied request; noon and am/pm are normalized. Relative or ambiguous edits produce a clarification with no approval instead of guessed times. Use the structured editor for unsupported wording or precise multi-field changes. The agent has no geocoding tool and cannot invent coordinates for a new city.

Forecast apparent temperature is an outdoor planning proxy, not WBGT, individual worker exposure, medical advice, or a guarantee of safe work. The planning threshold is user-defined. The model cannot label a forecast comparison as measured health improvement, completed work or avoided illness.

## Verification

`tests/test_agent.py` checks preservation of work and controls, explicit-versus-negated deletion/unlocking, exact requested edit satisfaction, task-reference ambiguity, schema rejection, exact deterministic result/trace behavior, weather failure, stale-result invalidation, model-output isolation, sanitized model errors and bounded tool calls. These offline tests use labelled synthetic weather fixtures and make no model requests. A real model smoke test must be reported separately with its actual provider, model and observed tool trace; passing mocked unit tests alone does not establish live inference.

On 11 October 2026, real local `qwen3:1.7b` smoke tests executed `inspect_plan → propose_plan → optimize_plan` for both requests below:

- Garden maintenance cannot start before 13:00: the candidate changed only its `earliestStart` to `13:00`; all 195 work minutes, the inspection lock, shift and lunch remained intact. Observed duration: 3.5 seconds.
- “Do not unlock the inspection. Set the paid shift start to09:00.”: `shiftStart` became `09:00`, `shiftEnd` stayed `17:00`, the inspection remained locked, and 195 work minutes remained. Observed duration: 7.5 seconds.

Both used Open-Meteo weather and returned review-required proposals; no plan was applied. These are observed local smoke-test timings, not guaranteed latency. Forty offline agent tests passed separately. Bedrock was not invoked.
