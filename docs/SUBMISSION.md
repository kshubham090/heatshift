# HeatShift — submission draft

**Track:** Heat and Water

**Tagline:** A cooler plan. The same work.

## Short writeup

Campus grounds and maintenance crews have jobs that must get done, even when the day's hottest hours make outdoor work harder. HeatShift helps a supervisor reschedule flexible work while preserving paid hours, job duration, permitted windows, fixed commitments and breaks.

The application combines a real Open-Meteo forecast with an exact deterministic scheduler for one crew and up to eight jobs. It compares the same workload before and after planning, exposes its weather provenance, and produces a reviewable schedule, printable report and JSON evidence. If the original plan is invalid, it withholds improvement claims. If the constraints cannot all be satisfied, it explains the conflict instead of removing work.

The React interface, FastAPI service and deterministic planner are deployed on AWS Lambda. The public app has fetched real weather and reproduced the same 195-minute planning result. Our assistant uses AWS's open-source Strands Agents SDK: real local Ollama/Qwen3 (`qwen3:1.7b`) invocations validated requested changes and executed the planning tools. Suggestions require human review; the model does not invent weather, calculate the schedule or approve a plan. The hosted Bedrock adapter is configured, but inference currently fails with an AWS account/service restriction; successful hosted model execution is not claimed. The complete assistant remains reproducible locally.

We tested overlapping locks, break conflicts, missing weather, invalid comparison plans, unit errors and cache provenance. An independent exhaustive search checks the optimizer's result on small cases. The default campus workload is illustrative. The outcome is a forecast-based planning opportunity, not measured worker exposure, reduced illness or completed field work.

OpenAI Codex assisted with research, implementation, tests and documentation. Third-party software, model and data credits are listed in the repository README.

## Optional dated result sentence

Use only if the recording or evidence artifact shows this particular saved observation:

> In a real forecast retrieval on 11 October 2026 for the illustrative 12 October Delhi workload, all 195 minutes of work were retained while the duration-weighted forecast apparent temperature changed from 32.677°C to 28.431°C. This is a dated forecast comparison, not a measured health result; subsequent forecasts may differ.

## Links and completion record

Only confirmed links are listed below. Items awaiting publication or verification remain pending; do not paste placeholder links into the submission form.

| Item | Current record |
|---|---|
| Public repository | [github.com/kshubham090/heatshift](https://github.com/kshubham090/heatshift) — published; initial GitHub Actions verification passed. |
| YouTube demo under three minutes | A 2:14.77 narrated walkthrough of actual app screenshots is prepared. Upload and signed-out playback verification are pending; add the actual public/unlisted URL afterward. It is not a continuous screen recording. |
| AWS role | Verified Lambda hosting and real local Strands tool execution. Identify the provider shown; do not present local model results as successful Bedrock inference. |
| Hosted demo | [Live AWS Lambda planner](https://tap7v5jbtjbasqpzmskibpi7we0atrge.lambda-url.us-east-1.on.aws/). Interface, real weather and optimization verified; hosted assistant unavailable. |
| Optional AWS Builder Center blog | Add the published blog URL if the draft is published. |
| Team and registration details | Use the participant's actual registered details; no invented teammates. |

The verified AWS work includes both Lambda hosting and local Strands execution. These are distinct observations: the hosted planner works, while the assistant's successful model runs were local. The event states that local and deployed projects receive the same judging. The exact cause of the Bedrock restriction has not been established.

## Copy-ready answers for the inspected form

These drafts match the signed-in form's labels. The participant should confirm the contribution and feedback wording before submission. Personal profile fields are intentionally left blank in the [checklist](SUBMISSION_CHECKLIST.md).

### What does your project do?

HeatShift helps campus facilities supervisors move flexible outdoor jobs into cooler available hours while keeping every job, its duration, allowed window, fixed commitments, paid shift and breaks. It combines real Open-Meteo forecasts with an exact scheduler for one crew and up to eight jobs. Supervisors can compare schedules, inspect weather evidence, review suggested changes, accept a plan locally and export its evidence. Conflicting locks produce an explanation instead of silently dropping work. An illustrative Delhi-campus forecast calculation retained all 195 work minutes with a 4.246°C lower duration-weighted apparent temperature. This is a dated forecast estimate, not measured exposure or a health outcome; no field pilot is claimed.

### How did you use AWS in your project?

AWS Lambda hosts the React interface and FastAPI planner through a public Function URL; real hosted weather retrieval and optimization are verified. CloudFormation describes the deployment, IAM limits runtime permissions, S3 stores the private deployment package, CloudWatch retains function logs for seven days, and DynamoDB atomically caps hosted assistant attempts at 25 per day. This is an attempt limit, not a spending cap. AWS's open-source Strands Agents SDK powers the assistant's inspect, validate and optimize tools. Real local Ollama/Qwen3 runs successfully changed task constraints and produced reviewable schedules. The deployed Bedrock Nova Lite adapter is configured, but AWS currently rejects its model requests with an account/service restriction. Successful Bedrock inference is not claimed; the complete assistant remains reproducible locally.

### Team leader's contributions

I directed the project, selected HeatShift, set the product and spending requirements, and approved the AWS deployment. I used OpenAI Codex extensively for research, architecture, implementation, debugging, tests, documentation and demo preparation. The resulting deliverables include the exact scheduler, real-weather adapter, constraint-review workflow, AWS Strands integration, React interface, automated checks, public repository, AWS-hosted planner and narrated walkthrough. The video uses actual application screenshots with a stock synthetic voice. Codex is disclosed as an AI tool, not listed as a human teammate.

### Help us evaluate you: your feedback on the AWS services you used

Amazon Bedrock needs clearer readiness checks and error guidance. The hosted adapter had credentials configured, but both its request and a minimal direct Nova Lite playground prompt failed; the playground returned “ValidationException: Operation not allowed.” A selectable model and healthy application endpoint did not establish usable inference. An actionable error distinguishing model entitlement, account restrictions and regional availability would have saved time. CloudShell was also unavailable during setup, so deployment required the console route. I have not established that these failures share one cause. HeatShift keeps the deterministic planner usable and reports the assistant failure rather than substituting a fake response.

### What did you like about the AWS services you used?

AWS Lambda and Function URLs let the built React interface and FastAPI service run together as one public application. CloudFormation made the deployment and IAM permissions reviewable and reproducible. DynamoDB's conditional update gave the hosted assistant a shared daily admission counter across Lambda instances, instead of relying only on process memory. The Strands Agents SDK was useful for a tool-based workflow: the same deterministic inspection, validation and optimization tools worked with a local Ollama model, so genuine agent behavior could be tested independently of Bedrock access. Keeping scheduling in ordinary Python also made the result independently testable.
