#!/usr/bin/env bash
set -euo pipefail

# Simple orchestrator: deploy Lambda (if provided) then API integration
# Usage: ./deploy-all.sh <API_ID> <RESOURCE_ID> <LAMBDA_NAME> [region]
API_ID=${1:-}
RESOURCE_ID=${2:-}
LAMBDA_NAME=${3:-}
REGION=${4:-us-east-1}

if [[ -z "$API_ID" || -z "$RESOURCE_ID" || -z "$LAMBDA_NAME" ]]; then
  echo "Usage: $0 <API_ID> <RESOURCE_ID> <LAMBDA_NAME> [region]"
  exit 2
fi

# If infra/deploy-lambda.sh exists, run it to update Lambda code (optional)
if [[ -x infra/deploy-lambda.sh ]]; then
  echo "Running infra/deploy-lambda.sh to update Lambda code (if configured)..."
  infra/deploy-lambda.sh "$LAMBDA_NAME" "$REGION" || true
else
  echo "No infra/deploy-lambda.sh found or not executable; skipping Lambda code update"
fi

# Deploy API (integration + CORS + redeploy)
chmod +x infra/deploy-api.sh
infra/deploy-api.sh "$API_ID" "$RESOURCE_ID" "$LAMBDA_NAME" "$REGION"

echo "All done. Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/summarize"
