# HeatShift evidence record

This file separates implemented features, observed executions and work still awaiting verification. Dates and times are India Standard Time unless an exported timestamp carries its own UTC offset.

## Latest complete verification

On **11 October 2026**, the complete offline suite passed **116 tests** (`python -m pytest -q`). The production React build also passed. This includes the global hosted-admission counter, safe failure diagnostics, actual Strands tool-parser regressions for sensitive log output, the Bedrock-only unavailable override, and API checks proving that a disabled assistant or depleted/unavailable counter prevents model invocation. Disabled requests return HTTP 503 before reserving a daily slot; none of these tests made a paid model call.

Browser verification covered the normal forecast comparison, refusal of conflicting locks, local acceptance, and the actual JSON download linked below. The 390-pixel responsive layout had no horizontal document overflow. A real Strands/Ollama garden-window request returned a three-tool trace and a reviewable proposal. Editing an input disabled applying the stale proposal and printing the old plan. Restoring the original inputs and applying the reviewed proposal changed the garden window to 13:00–17:00, retained all 195 work minutes, and required a separate acceptance decision.

The hosted app's **Print report** action was also verified through Chrome's actual **Save as PDF** workflow with **Default margins**. The resulting [two-page report for 12 October](evidence/printed-report-2026-10-12.pdf) was rendered with Poppler and visually checked: all report content was readable. The artifact contains the illustrative public plan and public app URL; it is not evidence of completed work or worker approval.

The AWS templates passed CloudFormation lint. The Linux ARM64 package, including timezone data, was verified against the current backend and client build. Packaging checks alone establish neither a deployment nor successful inference; the subsequent hosted checks below establish the working planner.

## Verified: AWS-hosted planner; cloud assistant blocked

On **11 October 2026**, the public [AWS Lambda app](https://tap7v5jbtjbasqpzmskibpi7we0atrge.lambda-url.us-east-1.on.aws/) loaded the React interface. `/api/health` returned HTTP 200 and reported the Bedrock provider as configured. A real hosted forecast/optimizer request retained all **195 work minutes** and returned the **4.246°C** forecast-average difference for the illustrative 12 October workload.

The hosted assistant request failed. A separate minimal request to the direct regional model `amazon.nova-lite-v1:0` in the official Bedrock playground also returned **`ValidationException: Operation not allowed`**. This is an AWS account/service restriction; the specific cause has not been established. A healthy endpoint and configured provider are not proof of successful model inference. **No successful Bedrock model execution is claimed.** The verified Strands/Ollama executions below remain the assistant evidence.

## Prepared: narrated video walkthrough

A **2:14.77** MP4 walkthrough was prepared from actual application screenshots with a stock synthetic narration voice. It is **not a continuous screen recording** and does not establish unrecorded interactions or successful Bedrock inference. The screenshots include states from the verified application flows; detailed execution evidence is recorded separately here. The video awaits the participant's review. YouTube upload, signed-out playback verification and event submission remain pending.

## Verified: deterministic engine and weather adapter

On **11 October 2026**, the following command passed **34 tests** for the domain modules:

```sh
python -m pytest tests/test_optimizer.py tests/test_weather.py -q
```

The tests include:

- A cooler plan retaining every job, its duration, task windows, fixed starts and breaks.
- An all-locked workday returning unchanged rather than invented improvement.
- Equal-temperature alternatives preserving the original starts.
- An overlapping original plan returning a valid proposal without original improvement metrics.
- Conflicting locks, a locked job crossing a break, insufficient working time, and a nonpreemptive job unable to fit around a break.
- An over-subscribed task window with a concrete required/available-minutes explanation.
- Duration-weighted arithmetic and threshold inclusion, including a 30-minute job spanning two forecast hours.
- Rejection of missing forecast hours, a mismatched date/location, invalid time increments, duplicate task IDs, out-of-bounds shifts and non-finite inputs.
- Fifteen small cases compared with an independent exhaustive enumeration of feasible start combinations.
- Provider failures, missing temperatures, Fahrenheit data, duplicate hours, wrong dates, wrong timezone, out-of-range values and saved-data age/location/date checks.

Weather values inside unit tests are explicitly labeled synthetic fixtures. Those tests demonstrate correctness and failure handling, not a live forecast or environmental outcome.

A separate middleware regression run passed **4 tests** in `tests/test_review_api.py`: an oversized chunked body stops reading after the first chunk exceeding 64 KiB; valid chunked UTF-8 JSON reaches the route unchanged; more than 2,000 real ASGI client peers retain at most 2,000 rate-limit entries with LRU eviction; unknown POST routes allocate no entries. These checks exercised the actual middleware rather than replacing it with a mock. The complete-suite result is recorded above.

The finalized agent-boundary run passed **40 tests** in `tests/test_agent.py`. Coverage includes negated edits, preservation of the original baseline, unique task identification, exact requested clock values, refusal of omitted requested changes, schema validation, rejected proposals, genuine tool-recording behavior and sanitized failure paths. These offline tests do not substitute for the real invocations below.

## Verified: real forecast and complete planning result

A separate application-level call on **11 October 2026** fetched a real Open-Meteo response and passed it into the real optimizer.

| Field | Observed value |
|---|---|
| Forecast date | 12 October 2026 |
| Requested location | Latitude 28.75, longitude 77.12, near Delhi/DTU |
| Source and mode | Open-Meteo; live |
| Retrieval time in the retained browser export | 11 October 2026, 19:52:32 IST (`2026-10-11T14:22:32.193513+00:00`) |
| Hours received | 24 |
| Scenario | Illustrative campus workload; not an actual DTU work order |
| Result | Improved; original schedule valid |
| Work retained | 195 minutes across four jobs |
| Original weighted apparent temperature | 32.677°C |
| Proposed weighted apparent temperature | 28.431°C |
| Difference, original minus proposed | 4.246°C |
| Original minutes at or above the user's 32°C marker | 165 |
| Proposed minutes at or above that marker | 15 |

The observed proposed schedule was:

| Job | Time, IST | Duration |
|---|---|---|
| Grounds cleanup | 08:00–09:00 | 60 minutes |
| Garden maintenance | 09:00–10:00 | 60 minutes |
| Fixed contractor inspection | 10:00–10:30 | 30 minutes; original lock preserved |
| Pathway sweeping | 10:30–11:15 | 45 minutes |

The protected 12:30–13:00 break and 08:00–17:00 paid shift were preserved. These results are an observed forecast calculation. They are **not** evidence that these jobs were performed, workers followed the plan, or illness/exposure was reduced. The value will change as forecasts change.

The application's actual browser export is retained as [forecast-comparison-2026-10-11.json](evidence/forecast-comparison-2026-10-11.json). It contains the raw request, result, all hourly weather values and precise source metadata. The export records **not accepted**; it is not evidence of supervisor acceptance or completed work. The [planner screenshot](images/planner.png) and [conflict screenshot](images/conflict.png) show the corresponding interface flows.

## Model and dependency evidence

The installed Python distributions reported Strands Agents 1.59.0, FastAPI 0.143.0, Pydantic 2.14.0, HTTPX 0.28.1, Uvicorn 0.54.0, Mangum 0.22.0 and Boto3 1.43.111. Their licenses were checked using package metadata and installed license files.

The local Ollama model-inspection endpoint returned an Apache 2.0 license for both the earlier `qwen3:4b` model and the current `qwen3:1.7b` model. Both were reported as Q4_K_M quantized models. These inspections establish availability and license metadata; separate invocations below establish actual execution. The configured model tag, rather than a rounded parameter-size label, identifies the reproducible default.

## Verified: real local Strands invocations

On **11 October 2026**, an initial real model smoke test used **Strands Agents 1.59.0, provider `ollama`, model `qwen3:4b`**. It completed in **48.7 seconds**, executing `inspect_plan` followed by `optimize_plan`. The deterministic result reported a **4.246°C** reduction in duration-weighted forecast apparent temperature for the same illustrative 195-minute workload. This is a historical run, not the current default model.

A later real run used **`qwen3:1.7b`** to handle a requested change: **garden maintenance could only start after 13:00**. It succeeded in **3.5 seconds**, retained all **195 minutes** of work and returned a **3.346°C** lower duration-weighted forecast apparent temperature for the revised constraints. This verifies that specific constraint edit and is the basis for the current local model choice.

A second current-model test used the exact request **“Do not unlock inspection. Set paid shift start to 09:00.”** It completed in **7.5 seconds** with an actual `inspect_plan` → `propose_plan` → `optimize_plan` trace. The proposal set the shift to **09:00–17:00**, retained the locked inspection and all **195 work minutes**, and required review before application. No input was automatically approved.

These were actual local model invocations, not mocked tool traces. The durations are observed runs on this host, not response-time guarantees. Neither test establishes that every possible natural-language request is supported. Additional requested changes are recorded only after their results are verified.

The verified local configuration uses the event's AWS open-source route. It makes no AWS cloud inference requests and does not create AWS resources or consume AWS credits. Cloud deployment is not required for this route. The separate hosted planner and its restricted model access are recorded above.

## Verification still to record

| Item | Status in this record | What establishes completion |
|---|---|---|
| Full application test suite | 116 offline tests and production build passed | Recorded in Latest complete verification above. |
| Normal/conflict browser workflows | Verified and pictured above | Retained planner and conflicting-lock screenshots. |
| JSON evidence export | Verified; exact downloaded artifact linked above | Raw request, schedule, metrics and full weather provenance are present. |
| Acceptance and printed report | Local acceptance and complete printed report verified | Browser acceptance saved the plan. Hosted Chrome Save as PDF produced the linked two-page report with Default margins; Poppler rendering was visually checked and readable. |
| Real Strands agent invocation | Verified locally as above | Record any additional constraint-edit demonstration separately. |
| AWS cloud deployment | Hosted interface, health and real forecast optimization verified | Public Lambda URL linked above. Hosted assistant invocation failed; health/provider configuration is not inference success. |
| Public repository | [Published](https://github.com/kshubham090/heatshift) | GitHub API confirms PUBLIC visibility. [Initial CI passed](https://github.com/kshubham090/heatshift/actions/runs/38148246065). |
| Demo video | 2:14.77 screenshot-based narrated walkthrough prepared; participant review pending | YouTube upload and signed-out playback pending. This is not a continuous screen recording. |
| Field validation | Not performed | A real supervisor's constraints and practical review; later measured conditions if available. |

Update a row only after the corresponding check actually occurs. A health badge, infrastructure template, successful model download or unit test with a mock does not substitute for the operation it describes.

## How to preserve the final demo evidence

Load the final scenario and let the app complete its real forecast request. Export JSON from the result. The export contains the original request, proposed and original schedules, metrics, constraint checks and the weather's date, requested/grid coordinates, retrieval time, source URL, mode, warnings and hourly values. Keep that file alongside the final recording. If accepted locally, the export records local acceptance, not worker assignment or task completion.

For the agent scene, retain the actual returned tool trace and show it in the recording. A later natural-language summary must not be substituted for missing executed tools.
