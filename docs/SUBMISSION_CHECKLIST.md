# HeatShift: final submission checklist

**Deadline:** midnight IST at the end of 11 October 2026, before 12 October begins. The recorded extension is [here](https://x.com/WeMakeDevs/status/2109187691317498287).

**Submission page:** https://www.wemakedevs.org/aws/env/submit

The signed-in form was inspected on 11 October 2026. It shows **12 required answers**: three team details, seven project details and two feedback answers. The exact visible labels are below. Character limits were not shown. The form says submissions can be edited until the deadline; no terms checkbox was visible in the inspected form.

## The 12 required fields

Personal profile values are intentionally blank pending the participant's confirmation. Do not infer them from the repository owner or enter a coding assistant as a teammate.

| Exact field label | Value / ready answer | Status |
|---|---|---|
| Team leader's WeMakeDevs username | | Required; confirm from the participant's WeMakeDevs home page. |
| Team leader's GitHub | | Required; confirm the participant's profile URL. |
| Team leader's LinkedIn | | Required; confirm the participant's profile URL. |
| Project title | HeatShift | Ready |
| Track you are submitting for | Heat and Water | Ready; select this checkbox. |
| GitHub link to project | https://github.com/kshubham090/heatshift | Published; [initial CI passed](https://github.com/kshubham090/heatshift/actions/runs/38148246065). |
| YouTube video demo link | | Required; upload and signed-out playback check pending. |
| What does your project do? | [Copy-ready answer](SUBMISSION.md#what-does-your-project-do) | Ready |
| How did you use AWS in your project? | [Copy-ready answer](SUBMISSION.md#how-did-you-use-aws-in-your-project) | Ready; hosted planner and local agent evidence are distinguished. |
| Team leader's contributions | [Copy-ready answer](SUBMISSION.md#team-leaders-contributions) | Draft for participant review; AI assistance disclosed. |
| Help us evaluate you: your feedback on the AWS services you used | [Copy-ready answer](SUBMISSION.md#help-us-evaluate-you-your-feedback-on-the-aws-services-you-used) | Draft based on observed service behavior. |
| What did you like about the AWS services you used? | [Copy-ready answer](SUBMISSION.md#what-did-you-like-about-the-aws-services-you-used) | Draft based on implemented services. |

## Optional fields actually observed

- **Deployed link to project:** https://tap7v5jbtjbasqpzmskibpi7we0atrge.lambda-url.us-east-1.on.aws/ — hosted planner verified; hosted Bedrock assistant unavailable.
- **Blog links:** leave blank unless the [draft](BUILDER_BLOG.md) is published. The form accepts up to four blogs, one per actual team member.
- **Team leader's resume:** optional for the project form, but the form explicitly says a publicly accessible resume is necessary for Amazon Fast Track Interview consideration. Do not publish a resume or invent its URL.
- Second, third and fourth team members' WeMakeDevs usernames, GitHub, LinkedIn, resumes and contributions: fill only for actual registered human teammates. Resume URLs must be public if supplied.

## Finish in this order

- [x] Prepare the public repository and a verified hosted planner.
- [x] Prepare the 2:14.77 narrated walkthrough from actual application screenshots. It uses a stock synthetic voice and is not a continuous screen recording.
- [ ] Complete the remaining deployment checks and let the participant review the prepared video. Upload is pending that review.
- [ ] When ready to proceed, upload the approved video to YouTube as public or unlisted and check the final URL signed out. Keep the video under 3:00.
- [ ] Confirm the three required leader profile values and actual team composition. Review the contribution and feedback text before entering it.
- [ ] Confirm the repository contains the final code/docs and remains public. Its history must reflect event-period work.
- [ ] Fill all 12 required fields, add the verified deployed URL and select Heat and Water. Submit once per team before the deadline, then retain the confirmation. Use the form's edit flow for later corrections before the deadline.

The hosted planner is live. Successful Bedrock inference is **not** claimed: AWS rejected a hosted request and a minimal direct model request. The complete assistant is verified locally using Strands/Ollama. Submission remains a draft pending final checks and the participant's video review.

The workload is illustrative. Describe its forecast comparisons as estimates, not measured exposure, reduced illness or completed field work. See [EVIDENCE.md](EVIDENCE.md) for the tests, screenshots, exported forecast and distinct hosting/model results.
