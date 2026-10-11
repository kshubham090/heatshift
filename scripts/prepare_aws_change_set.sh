#!/usr/bin/env bash
# Defaults to local preview. Explicit --create-change-set uploads code and
# creates a REVIEWABLE CloudFormation change set, but NEVER executes it.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION=us-east-1
STACK=heatshift-demo
BUCKET=
PACKAGE="${PROJECT_DIR}/.lambda/heatshift-lambda.zip"
CHANGE_TYPE=CREATE
CREATE_CHANGE_SET=0

usage() {
  cat <<'HELP'
Usage: prepare_aws_change_set.sh --bucket PRIVATE_BUCKET [options]
  --package PATH          Built Lambda ZIP (default .lambda/heatshift-lambda.zip)
  --stack NAME            Stack and Lambda name (default heatshift-demo)
  --region REGION         Default us-east-1; verify direct Nova Lite availability first
  --update                Prepare an UPDATE instead of the first CREATE
  --create-change-set     Upload package and create change set, never execute it
Without --create-change-set this only prints a local preview.
HELP
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bucket) BUCKET="${2:?Missing bucket}"; shift 2 ;;
    --package) PACKAGE="${2:?Missing package path}"; shift 2 ;;
    --stack) STACK="${2:?Missing stack name}"; shift 2 ;;
    --region) REGION="${2:?Missing region}"; shift 2 ;;
    --update) CHANGE_TYPE=UPDATE; shift ;;
    --create-change-set) CREATE_CHANGE_SET=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ -n "$BUCKET" ]] || { usage >&2; exit 2; }
[[ "$STACK" =~ ^[a-zA-Z][a-zA-Z0-9-]{0,63}$ ]] || { echo 'Use a stack name of 1–64 letters, digits or hyphens, beginning with a letter.' >&2; exit 2; }
[[ -f "$PACKAGE" ]] || { echo "Package not found: $PACKAGE. Run package_aws.sh first." >&2; exit 2; }
SHA="$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$PACKAGE")"
KEY="heatshift/${SHA}.zip"
cat <<INFO
Review-only AWS plan
  Region: $REGION
  Stack/function: $STACK
  Private package: s3://$BUCKET/$KEY
  Change: $CHANGE_TYPE
  Model: amazon.nova-lite-v1:0 (direct, same region)
  Shared assistant cap: 25 admitted attempts/day, midnight IST reset
  Access: PUBLIC Lambda Function URL; visitors need no AWS login
  IAM: new Lambda execution role; one model, one budget table, own logs
  Reserved concurrency: omitted for small new-account quotas
  Billing: metered resources; cap does not cap all hosting traffic or charges
INFO
if [[ "$CREATE_CHANGE_SET" != 1 ]]; then
  echo 'Preview only. No AWS requests made. Read docs/AWS_HOSTING_REVIEW.md before enabling the upload/change-set step.'
  exit 0
fi
command -v aws >/dev/null || { echo 'AWS CLI v2 is required for change-set creation.' >&2; exit 2; }
CHANGE_NAME="review-$(date -u +%Y%m%dT%H%M%SZ)"
aws s3 cp "$PACKAGE" "s3://${BUCKET}/${KEY}" --sse AES256 --only-show-errors --region "$REGION"
CHANGE_ARN="$(aws cloudformation create-change-set \
  --region "$REGION" --stack-name "$STACK" \
  --change-set-name "$CHANGE_NAME" --change-set-type "$CHANGE_TYPE" \
  --template-body "file://${PROJECT_DIR}/infra/aws-template.yaml" \
  --description 'HeatShift optional public demo: review IAM, public access and credit plan before execution.' \
  --capabilities CAPABILITY_IAM \
  --parameters \
    "ParameterKey=ArtifactBucket,ParameterValue=${BUCKET}" \
    "ParameterKey=ArtifactKey,ParameterValue=${KEY}" \
    "ParameterKey=FunctionName,ParameterValue=${STACK}" \
    'ParameterKey=DailyAgentLimit,ParameterValue=25' \
    'ParameterKey=ReservedConcurrencyLimit,ParameterValue=-1' \
  --query Id --output text)"
aws cloudformation wait change-set-create-complete --region "$REGION" --change-set-name "$CHANGE_ARN"
REVIEW_FILE="$(dirname "$PACKAGE")/cloudformation-change-set.json"
aws cloudformation describe-change-set --region "$REGION" --change-set-name "$CHANGE_ARN" --output json > "$REVIEW_FILE"
printf '\nChange set ready for review: %s\nSaved review: %s\n' "$CHANGE_ARN" "$REVIEW_FILE"
echo 'No change set was executed. Inspect the saved changes and use the CloudFormation console Execute button only after user approval.'
