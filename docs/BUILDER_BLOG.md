# Draft: Building HeatShift, a schedule that respects the work

**Publication status: draft.** This article has not been published to AWS Builder Center. Before publication, add the verified repository and video links and update any later checks from the evidence record. The implementation uses AWS open source locally; it does not use cloud deployment or paid AWS inference.

Environmental projects often start with a chart. For HeatShift, we started with a decision: a campus supervisor has outdoor jobs to finish, and some of them could happen at a different time. Can we produce a cooler feasible work plan without quietly changing what the crew owes the day?

That last condition became the product. A lower number is unhelpful if it comes from deleting a job, shortening its duration, moving work outside paid hours or ignoring lunch.

## A small operational problem

HeatShift takes one crew, one date, a paid shift, up to eight jobs, each job's duration and allowed hours, fixed starts and protected breaks. It retrieves real hourly weather from Open-Meteo and searches for a feasible timetable in 15-minute increments.

The included example is an illustrative Delhi campus workload: grounds cleanup, garden maintenance, a fixed contractor inspection and pathway sweeping. It is not an actual DTU work order and has not been used in a field pilot.

The output is a schedule the supervisor can review, accept in their browser and export with its evidence. A weather chart explains the schedule; it is not the product's final action.

## Let deterministic code do the scheduling

The optimizer uses dynamic programming over time and the set of completed jobs. Its first objective is the sum of forecast apparent temperature multiplied by scheduled work minutes. All feasible plans retain the same amount of work, so this minimizes the duration-weighted average.

Ties prefer fewer moved jobs, then fewer minutes of movement. That matters operationally: when the forecast offers no improvement, changing a supervisor's already valid schedule creates disruption without benefit.

Jobs are uninterrupted. A 90-minute task cannot turn into two smaller tasks around a break. A fixed inspection remains fixed. If the original plan violates a constraint, HeatShift does not use it as a flattering comparison. If no feasible plan exists, it returns a conflict instead of dropping work.

We tested that behavior against overlapping locks, breaks, insufficient time and missing weather. An independent exhaustive enumeration also checks the optimizer's result for small scenarios. The initial engine and weather-adapter suite passed 34 tests; broader integration results are maintained in the repository's evidence record.

## Give the agent a bounded job

The integration uses the AWS open-source Strands Agents SDK. Its job is to inspect the current plan, understand a specific requested change, validate a proposal and invoke the deterministic planner. It has four tools: `inspect_plan`, `inspect_weather`, `propose_plan` and `optimize_plan`.

The model has no approval, messaging, deployment or shell tool. It does not perform the schedule arithmetic. Proposed changes are reviewed in the interface, and accepting a schedule remains a separate human decision.

Trace entries are generated inside executing tools. User-facing results are assembled from their returned evidence instead of displaying unrestricted model text. If inference fails, the application reports that failure; the direct planner remains usable.

The current local configuration runs Strands with Ollama and `qwen3:1.7b`. In a real test, the agent handled a request that garden maintenance start only after 13:00, validated the revised plan and retained all 195 minutes of work. That invocation took 3.5 seconds on the test host and returned a forecast-average difference of 3.346°C under the revised constraints. These are observations from that run, not general latency or environmental-outcome promises. Individual natural-language edits still deserve their own test.

We chose the event's AWS open-source “Build It” route, which is judged alongside deployed projects. Strands supplies the AWS integration while inference stays local. This version needs no AWS deployment, credits or cloud inference spend. The repository's run guide is local; cloud deployment files are not included.

## Make the source visible

HeatShift stores the forecast date, request coordinates, returned grid coordinates, retrieval timestamp, source URL and hourly values with the result. Cached responses keep their original timestamp and are labeled saved. A failed weather request can fall back only to a recent real response for the same requested location and date; no sample temperatures are substituted.

During a real retrieval on 11 October 2026, the illustrative workload for 12 October kept all 195 minutes of work while its duration-weighted forecast apparent temperature changed from 32.677°C to 28.431°C. That is an observed calculation using a forecast. It is not evidence of completed work, adherence to the schedule, reduced illness or measured personal exposure. A later forecast can produce a different result.

The weather grid also cannot describe every corner of a campus. Apparent temperature is not WBGT and does not capture each person's clothing, exertion, acclimatization or health. The product exposes those limits instead of turning its planning marker into a safety certification.

## The next useful experiment

The next step is a real supervisor-reviewed pilot. We would replace the illustrative tasks with an actual day's commitments, record which proposed changes were practical, and compare the plan with observed conditions. That would test whether the workflow helps someone run a workday, rather than merely producing an attractive calculation.

The lesson from this build is straightforward: an environmental assistant needs a concrete decision, trustworthy inputs and permission to say that a requested plan cannot work.

## Credits and disclosure

HeatShift uses React, FastAPI, Pydantic, Strands Agents, Ollama/Qwen, and Open-Meteo with contributing weather services. The repository lists component licenses and data attribution. Original application code is MIT licensed; dependencies, model weights and forecast data retain their own terms. OpenAI Codex assisted with research, architecture, implementation, testing and this draft. No field pilot, prize or cloud deployment is claimed by this article.
