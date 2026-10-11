# Optional AWS hosting: review before deployment

This is a prepared deployment option, not evidence of a live deployment. The existing local Ollama route remains the default. No AWS resource or model call was created by the packaging and validation work.

For an eligible AWS **Free Plan**, access ends when the plan’s credits or time expire rather than automatically continuing under a paid plan. Verify the actual account plan, credit eligibility and each service’s availability before creating resources. Do not upgrade an account or select a paid subscription, provisioned model throughput or a quota purchase as part of this workflow. These templates do not change the account plan. Credit balances and billing records should remain private.

## Recommended small deployment

One Python 3.13 ARM64 Lambda serves the built React app and FastAPI through Mangum. Its HTTPS Function URL is public. A real AWS Strands agent calls the **on-demand, direct regional** Bedrock model `amazon.nova-lite-v1:0` in `us-east-1`. The deterministic optimizer and Open-Meteo weather fetch remain the same code.

A small DynamoDB table atomically admits **25 hosted assistant attempts per day, shared by every visitor**. A private S3 bucket holds the deployment ZIP; it is not a public website. CloudWatch retains function logs for seven days. There is no API Gateway, NAT gateway, provisioned capacity, custom domain, or always-running server in this design.

The app stack contains seven resources: Lambda, its URL, two public-invocation permissions, execution role, log group and daily-counter table. The optional bucket template adds one private bucket.

## The permissions and public access to approve

[`infra/aws-template.yaml`](../infra/aws-template.yaml) requests `CAPABILITY_IAM` because CloudFormation creates a generated-name execution role. Its trust policy permits only `lambda.amazonaws.com` to assume that role. Its application permissions are:

| Action | Exact resource scope |
| --- | --- |
| `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` | `arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0` when deployed in the recommended region |
| `dynamodb:UpdateItem` | Only the counter table created by this stack |
| `logs:CreateLogStream`, `logs:PutLogEvents` | Only streams in `/aws/lambda/<FunctionName>` |

The runtime role cannot create AWS resources, read arbitrary S3 objects, manage account settings, or invoke other models. It uses temporary role credentials; do not paste account access keys into environment variables or source files. The person or role operating CloudFormation separately needs deployment permissions for these resources, including passing the generated execution role to Lambda.

The two `AWS::Lambda::Permission` resources deliberately grant principal `*`:

- `lambda:InvokeFunctionUrl`, restricted to URL auth type `NONE`.
- `lambda:InvokeFunction`, restricted by `InvokedViaFunctionUrl: true`.

Both are necessary for newly created public Function URLs under the current Lambda permission model. Anyone with the URL can load the app and call its public APIs without AWS sign-in. There is no visitor account system. Saved accepted plans stay in that visitor’s browser. Plans sent to the hosted assistant go to Amazon Bedrock; forecast coordinates go to Open-Meteo.

The AWS Nova Lite console states that using the model accepts its applicable model terms/EULA. The account owner should approve those terms with the concrete deployment before the first model invocation. Seeing the model in the console does not establish successful inference or available account quota.

## What the daily limit does

`backend/cloud_budget.py` reserves one slot with a single conditional DynamoDB update immediately before an assistant invocation. Multiple Lambda instances share the same date key. A missing table configuration, invalid limit, unreachable table or unexpected response fails closed: the model is not invoked. Exhaustion returns HTTP 429; an unavailable counter returns 503. Failed model attempts still use their reserved slot. The allowance resets at midnight **Asia/Kolkata**; TTL only removes old counter rows.

The hosted template sets `HEATSHIFT_PUBLIC_HOSTED=1`, so accidentally omitting the table cannot silently disable the guard. The normal local configuration leaves those cloud settings unset and makes no DynamoDB call.

**This is an agent-attempt limit, not a dollar limit or a cap on all hosting traffic.** An admitted agent can use multiple model turns. Unsuccessful requests, static-file requests, weather requests, logs, data transfer and conditional-counter checks can still use AWS resources. Per-process request throttles and the table’s five-unit-per-second read/write ceilings reduce bursts but do not establish a total spending ceiling. Other uses of the same AWS account can also consume its credits.

Reserved Lambda concurrency is omitted by default. Small new-account quotas can be below the amount needed to reserve concurrency while leaving AWS’s required 100 unreserved units. Only set a positive `ReservedConcurrencyLimit` after verifying the actual account quota. Setting it to `0` intentionally disables all function execution, including the website.

## Costs to compare with the account’s credits

Published US East (N. Virginia) on-demand list prices verified 11 October 2026, before credits, free-tier allocations, taxes and other account usage:

| Item | Rate |
| --- | --- |
| Nova Lite input | $0.06 per million input tokens |
| Nova Lite output | $0.24 per million output tokens |
| ARM Lambda, first duration tier | $0.0000133334 per GB-second |
| Lambda requests | $0.20 per million requests |
| DynamoDB on-demand writes | $0.625 per million write request units |
| DynamoDB on-demand reads | $0.125 per million read request units |

For a transparent example, **60,000 input and 10,000 output tokens across an entire assistant attempt** would cost $0.006 in Nova Lite usage. At 25 such attempts a day for 30 days, model usage would be $4.50. These are illustrative token counts, not a promise that an attempt will use them or a hard billing bound; retries and model-loop behavior affect actual usage.

At the configured 1 GB memory, a 110-second Lambda execution would cost about $0.001467 before the account’s allocations; 750 such executions would be about $1.10. The same 750 successful daily-counter writes would cost about $0.000469. Website traffic, failed checks, cold-start duration, logs, package storage and transfer are additional. The small deployment package and seven-day log retention keep ordinary demo storage modest, but no fixed monthly total is guaranteed.

AWS’s price-list feeds used for these rates: [Bedrock](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json), [Lambda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSLambda/current/us-east-1/index.json), [DynamoDB](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonDynamoDB/current/us-east-1/index.json). The first two published 10 and 9 October 2026 respectively; the DynamoDB feed published 11 September 2026. Actual account billing and credit eligibility remain authoritative.

## Package and create a reviewable change set

1. Build locally from the repository root:

   ```sh
   ./scripts/package_aws.sh
   ```

   This installs front-end dependencies, builds React, and installs binary-only Python 3.13 Linux ARM64 dependency wheels. It does not contact AWS. It copies only backend source and `dist`, verifies every packaged shared library is a Linux ARM64 ELF binary, and rejects an uncompressed package at or above Lambda’s 250 MiB limit. Output: `.lambda/heatshift-lambda.zip` and `.lambda/package-manifest.json`. An optional first argument chooses another build directory. Set `PYTHON_BIN` if your Python environment uses another executable.

2. Use an existing **private S3 bucket in us-east-1**, or review [`infra/aws-artifact-bucket.yaml`](../infra/aws-artifact-bucket.yaml) to create one. Its public access is blocked, objects use S3 encryption, and deployment packages expire after 30 days. It retains the bucket if its bootstrap stack is deleted, so cleanup requires emptying and deleting that bucket separately. Do not put credentials in it.

3. Preview the app deployment locally; this does not make AWS requests:

   ```sh
   ./scripts/prepare_aws_change_set.sh --bucket YOUR_PRIVATE_BUCKET
   ```

4. Only after authorization for the upload and change-set preparation, use the same command with `--create-change-set`. This requires AWS CLI v2 and an already authenticated account session. It uploads the ZIP under a content-hash key and creates a CloudFormation change set. **It never executes the change set.** Add `--package PATH` when using another build directory; use `--update` only for an existing app stack.

5. Review the saved `cloudformation-change-set.json`, the template, IAM scope, public URL and model terms. The final deployment action is **Execute change set** in the CloudFormation console. No execution command is hidden in the script. The resulting stack’s `ApplicationUrl` output is the public app address.

The same files work through the AWS console without installing the CLI: upload the ZIP to the private bucket, create a CloudFormation stack by uploading `aws-template.yaml`, and enter `ArtifactBucket` and `ArtifactKey`. Keep other parameters at their defaults, acknowledge the displayed IAM role creation, review, then create only after approval. Use unique stack/function names if `heatshift-demo` already exists.

## Verify after an approved deployment

- Load the public page, `/api/health` and `/api/demo`; check that React assets load and provider is `bedrock`. Health confirms configured credentials, not successful inference.
- Run the deterministic planner and confirm real forecast provenance and preserved work constraints.
- Send one supported request: “Garden maintenance can only start after 13:00. Replan the other jobs.” Verify actual Strands tool entries, a correct proposal, and review/apply behavior. This is a real metered model call and consumes one shared daily slot.
- Confirm the counter row advanced and no secrets or raw plan/model content appear in logs. Verify controlled cap behavior in tests rather than spending all 25 production attempts.

The Function URL uses buffered responses and Lambda’s configured 180-second timeout; the app’s assistant timeout is shorter. This avoids an API Gateway integration timeout. Buffered payloads must remain within Lambda’s 6 MB limit. The package includes all front-end assets and requires no separate web host. There is no custom domain or global CDN; first visits can include a cold start.

Direct Nova Lite support, account model entitlement, region quotas, Free Plan service availability, and live ARM Lambda execution still require verification in the owner’s account. If direct regional inference is unavailable, stop and review the exact model/profile and additional IAM scope before changing the deployment; do not silently enable a cross-region profile or paid capacity.

## Remove the optional hosting

Delete the app’s Function URL to stop new public access, then delete the app CloudFormation stack to remove its function, role, table and seven-day log group. Deleting the budget table destroys its counter, so redeploying starts a fresh allowance. Empty and delete the private package bucket separately, including its bootstrap stack if used. Deleting deployment ZIPs alone does not stop an already deployed Lambda.

References: [Function URL permissions](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html), [Lambda quotas and ZIP limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [reserved concurrency rules](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html), [Nova Lite model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html).
