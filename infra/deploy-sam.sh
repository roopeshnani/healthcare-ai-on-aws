#!/usr/bin/env bash
set -euo pipefail

STACK_NAME=${STACK_NAME:-healthcare-ai-on-aws}
S3_BUCKET=${S3_BUCKET:-}
REGION=${REGION:-us-east-1}

if ! command -v sam >/dev/null 2>&1; then
  echo "AWS SAM CLI is required. Install from https://aws.amazon.com/serverless/sam/"
  exit 1
fi

if [[ -z "$S3_BUCKET" ]]; then
  # create a temporary bucket for sam package
  S3_BUCKET="${STACK_NAME}-sam-package-$(date +%s)"
  aws s3 mb s3://$S3_BUCKET --region "$REGION"
  echo "Created temporary S3 bucket: $S3_BUCKET"
fi

echo "Building SAM application..."
pushd infra >/dev/null
sam build --use-container

echo "Packaging SAM application..."
sam package --template-file .aws-sam/build/template.yaml --output-template-file packaged.yaml --s3-bucket $S3_BUCKET --region $REGION

echo "Deploying SAM stack $STACK_NAME..."
sam deploy --template-file packaged.yaml --stack-name $STACK_NAME --capabilities CAPABILITY_IAM --region $REGION --no-confirm-changeset --no-fail-on-empty-changeset

popd >/dev/null

echo "Deployment finished. Run 'aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION' to inspect outputs."
