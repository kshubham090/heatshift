# HeatShift demo — target 2:45

This is a recording guide, not evidence that recording, upload, deployment or model execution has happened. Record the actual working application. Rehearse once, keep the final video under three minutes, and use the numbers visible in that recording rather than memorized forecast values.

Before recording, verify the normal scenario, conflict scenario and a real model invocation. If a model fails, do not substitute a scripted trace. This submission uses the permitted AWS open-source route: show the real local Strands run. Cloud hosting is neither used nor required. The provided campus workload must remain labeled illustrative.

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | HeatShift title and normal campus scenario. | “A campus supervisor cannot simply cancel today's outdoor work because the afternoon is hot. HeatShift helps move flexible work into cooler available hours while keeping the crew's commitments. This is an illustrative workload near Delhi, not an actual DTU work order.” |
| 0:20–0:55 | Job inputs, 195 minutes of work, the fixed inspection, lunch break, then original/proposed timeline. | “We have four jobs, one crew, a paid shift and a protected lunch break. This inspection is fixed. The planner searches the allowed 15-minute slots and keeps every job and its full duration. Here is the original plan, and here is the feasible proposal.” |
| 0:55–1:15 | Current metrics and expanded weather provenance. | “The comparison uses duration-weighted forecast apparent temperature. The date, retrieval time, weather grid and live or saved status are visible. These are forecast estimates, not measured exposure or a claim that this workday is medically safe.” |
| 1:15–1:55 | Send the exact agent request below. Show actual returned tools, proposal review and the application action. | “Now I ask for a specific operational change. The AWS Strands agent inspects the plan, validates a proposal and calls the same deterministic optimizer. These entries come from executed tools. It cannot silently drop work or apply its suggestion. I review the change before applying it.” |
| 1:55–2:20 | Select **Conflicting locks**. Show no proposed schedule and the concrete conflict. | “A useful planner also needs to say no. These two locked jobs require the same crew at the same time. HeatShift reports the conflict. It does not unlock a job, shorten the work or invent a better score.” |
| 2:20–2:45 | Return to normal scenario, accept locally, show print or JSON evidence. Show the Strands source/configuration and local provider. | “A supervisor can accept and export a plan with its inputs and weather evidence. Acceptance stays in this browser; it does not assign workers. We use AWS's open-source Strands framework with a local model, so this build needs no AWS cloud spend. The next validation is a real supervisor-reviewed pilot. HeatShift delivers the same work, scheduled around the forecast.” |

Use this precise agent request during the rehearsal:

> Garden maintenance can only start after 13:00. Replan the other jobs.

This garden-window edit has a recorded successful run with `qwen3:1.7b`; rehearse it again in the final build. If the current run fails, show that outcome or use a narrower request that actually succeeds, such as “Find a cooler feasible schedule without changing any job, duration, allowed window, shift, lock or break.” Do not claim a constraint-editing demonstration if only unchanged-constraint optimization was shown.

Model waiting time can be shortened in editing with a visible “waiting time shortened” label. Preserve the real request, result, error state if relevant, and tool trace; do not fabricate speed or replace a failed response. Keep any explanation of edited waiting time brief.

## Final recording check

- Video duration is below 3:00; target 2:45 leaves margin.
- AWS's role is visible through a real local Strands execution; no cloud deployment is claimed.
- No credentials, account IDs, private console details or unrelated personal information appear.
- The video shows both a valid result and a refused infeasible case.
- The original/proposed workload is identical for any reported improvement.
- A live forecast value is not described as a realized saving or health outcome.
- Upload to YouTube as public or unlisted and test the link signed out before submitting.
