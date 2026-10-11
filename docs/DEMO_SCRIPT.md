# HeatShift demo — target 2:45

This is a guide for a future continuous recording. A separate **2:14.77 narrated walkthrough** has already been prepared from actual application screenshots with a stock synthetic voice; it is not a continuous screen recording. YouTube upload remains pending. The guide below is not its word-for-word transcript. For a new recording, rehearse once, stay under three minutes and use the values actually visible.

Before recording, verify the normal scenario, conflict scenario and a real model invocation. If a model fails, do not substitute a scripted trace. The AWS Lambda planner is live, but hosted Bedrock inference is currently blocked. Show and identify the real local Strands run for the assistant scene. The provided campus workload must remain labeled illustrative.

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | HeatShift title and normal campus scenario. | “A campus supervisor cannot simply cancel today's outdoor work because the afternoon is hot. HeatShift helps move flexible work into cooler available hours while keeping the crew's commitments. This is an illustrative workload near Delhi, not an actual DTU work order.” |
| 0:20–0:55 | Open **Day settings** and the fixed inspection's task card. Show 195 work minutes and lunch, then **Before. After. All the work.** | “We have four jobs, one crew, a paid shift and a protected lunch break. This inspection is fixed. The planner searches the allowed 15-minute slots and keeps every job and its full duration. Here is the original plan, and here is the feasible proposal.” |
| 0:55–1:15 | Current metrics; expand **Weather source & how to read this plan** in **Nothing hidden in the numbers.** | “The comparison uses duration-weighted forecast apparent temperature. The date, retrieval time, weather grid and live or saved status are visible. These are forecast estimates, not measured exposure or a claim that this workday is medically safe.” |
| 1:15–1:55 | Send the exact request below. Under **AWS STRANDS**, expand **3 tool steps returned** and show **Read workday → Review changes → Find schedule** when those are the actual returned steps. Review **PROPOSED CHANGES · YOUR REVIEW**, then select **Apply reviewed changes**. | “Now I ask for a specific operational change. The AWS Strands agent inspects the plan, validates a proposal and calls the same deterministic optimizer. These entries come from executed tools. It cannot silently drop work or apply its suggestion. I review the change before applying it.” |
| 1:55–2:20 | Select **Conflicting locks**. Show no proposed schedule and the concrete conflict. | “A useful planner also needs to say no. These two locked jobs require the same crew at the same time. HeatShift reports the conflict. It does not unlock a job, shorten the work or invent a better score.” |
| 2:20–2:45 | Select **Normal day**, then **Accept proposed plan**. Show **Accepted in this browser** and **Export evidence** or **Print report**. The download icon is titled **Export JSON with source data**. Keep the observed local provider visible. | “A supervisor can accept and export a plan with its inputs and weather evidence. Acceptance stays in this browser; it does not assign workers. AWS Lambda hosts the planner. The Strands assistant works locally; hosted Bedrock requests are currently blocked. The next validation is a real supervisor-reviewed pilot. HeatShift delivers the same work, scheduled around the forecast.” |

Use this precise agent request during the rehearsal:

> Garden maintenance can only start after 13:00. Replan the other jobs.

This garden-window edit has a recorded successful run with `qwen3:1.7b`; rehearse it again in the final build. If the current run fails, show that outcome or use a narrower request that actually succeeds, such as “Find a cooler feasible schedule without changing any job, duration, allowed window, shift, lock or break.” Do not claim a constraint-editing demonstration if only unchanged-constraint optimization was shown.

Model waiting time can be shortened in editing with a visible “waiting time shortened” label. Preserve the real request, result, error state if relevant, and tool trace; do not fabricate speed or replace a failed response. Keep any explanation of edited waiting time brief.

The current narration is approximately 265 words, or 1:53 at 140 words per minute, leaving about 50 seconds for clicks and waiting in a 2:45 recording. These control labels were checked against the current frontend. At narrow widths, settings and task details are collapsed: open the required cards before recording. If a plan is already accepted, use the actual **Accepted in this browser** state rather than pretending to click acceptance again. A hosted recording needs its own verified provider and endpoint; do not reuse the local-model narration to imply unverified Bedrock execution.

## Final recording check

- Video duration is below 3:00; target 2:45 leaves margin.
- AWS's role is visible through Lambda hosting and/or a real local Strands execution. The assistant provider is identified correctly; no successful Bedrock inference is claimed.
- No credentials, account IDs, private console details or unrelated personal information appear.
- The video shows both a valid result and a refused infeasible case.
- The original/proposed workload is identical for any reported improvement.
- A live forecast value is not described as a realized saving or health outcome.
- Upload to YouTube as public or unlisted and test the link signed out before submitting.
