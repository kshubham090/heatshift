# HeatShift — submission draft

**Track:** Heat and Water

**Tagline:** A cooler plan. The same work.

## Short writeup

Campus grounds and maintenance crews have jobs that must get done, even when the day's hottest hours make outdoor work harder. HeatShift helps a supervisor reschedule flexible work while preserving paid hours, job duration, permitted windows, fixed commitments and breaks.

The application combines a real Open-Meteo forecast with an exact deterministic scheduler for one crew and up to eight jobs. It compares the same workload before and after planning, exposes its weather provenance, and produces a reviewable schedule, printable report and JSON evidence. If the original plan is invalid, it withholds improvement claims. If the constraints cannot all be satisfied, it explains the conflict instead of removing work.

Our AWS integration uses the Strands Agents SDK with local Ollama and Qwen3, configured as `qwen3:1.7b`. A real model invocation has validated a requested garden-work time change and executed the planning tools successfully. Suggestions require human review; the model does not invent weather, calculate the schedule or approve a plan. This follows the event's AWS open-source “Build It” route: no AWS cloud deployment, credits or paid inference is used.

We tested overlapping locks, break conflicts, missing weather, invalid comparison plans, unit errors and cache provenance. An independent exhaustive search checks the optimizer's result on small cases. The default campus workload is illustrative. The outcome is a forecast-based planning opportunity, not measured worker exposure, reduced illness or completed field work.

OpenAI Codex assisted with research, implementation, tests and documentation. Third-party software, model and data credits are listed in the repository README.

## Optional dated result sentence

Use only if the recording or evidence artifact shows this particular saved observation:

> In a real forecast retrieval on 11 October 2026 for the illustrative 12 October Delhi workload, all 195 minutes of work were retained while the duration-weighted forecast apparent temperature changed from 32.677°C to 28.431°C. This is a dated forecast comparison, not a measured health result; subsequent forecasts may differ.

## Links and completion record

These items are intentionally unfilled until the result exists. Do not paste placeholder links into the submission form.

| Required item | Current record |
|---|---|
| Public repository | Add the verified repository URL after publication. |
| YouTube demo under three minutes | Add the public/unlisted URL after upload and a signed-out playback check. |
| AWS role demonstrated in video | Show actual local Strands tool execution and its provider/model; no cloud deployment is needed. |
| Hosted demo | Not used for the local Build It submission. |
| Optional AWS Builder Center blog | Add the published blog URL if the draft is published. |
| Team and registration details | Use the participant's actual registered details; no invented teammates. |

This submission deliberately uses the permitted local AWS open-source route. The event states that local and deployed projects receive the same judging. Do not deploy cloud resources or claim AWS credits under this project's zero-spend requirement.
