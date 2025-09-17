#!/usr/bin/env bash
set -euo pipefail

# Deploy API Gateway REST API integration to an existing Lambda
# Expects these env vars or arguments:
#   API_ID - existing RestApi id (e.g., zz6ukqzkoe)
#   RESOURCE_ID - resource id for /summarize (e.g., fs7hm4)
#   LAMBDA_NAME - existing Lambda name (e.g., BedrockSummarizer)
#   REGION - AWS region where API and Lambda live (default: us-east-1)

API_ID=${API_ID:-$1}
RESOURCE_ID=${RESOURCE_ID:-$2}
LAMBDA_NAME=${LAMBDA_NAME:-$3}
REGION=${REGION:-us-east-1}

if [[ -z "$API_ID" || -z "$RESOURCE_ID" || -z "$LAMBDA_NAME" ]]; then
  echo "Usage: $0 <API_ID> <RESOURCE_ID> <LAMBDA_NAME> [region]"
  echo "Example: $0 zz6ukqzkoe fs7hm4 BedrockSummarizer us-east-1"
  exit 2
fi

echo "Using API_ID=$API_ID RESOURCE_ID=$RESOURCE_ID LAMBDA_NAME=$LAMBDA_NAME REGION=$REGION"

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)
if [[ -z "$LAMBDA_ARN" ]]; then
  echo "Failed to locate Lambda $LAMBDA_NAME in $REGION"
  exit 3
fi

# Put integration (AWS_PROXY)
aws apigateway put-integration \
  --rest-api-id "$API_ID" \
  --resource-id "$RESOURCE_ID" \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region "$REGION"

# Add permission for API Gateway to invoke Lambda (idempotent)
STATEMENT_ID="apigateway-invoke-${API_ID}-${RESOURCE_ID}"
set +e
aws lambda add-permission --function-name "$LAMBDA_NAME" \
  --statement-id "$STATEMENT_ID" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/POST/summarize" \
  --region "$REGION" 2>/dev/null
RC=$?
set -e
if [[ $RC -eq 0 ]]; then
  echo "Added lambda permission $STATEMENT_ID"
else
  echo "Lambda permission may already exist (or failed to add). Continuing..."
fi

# Add CORS (OPTIONS) - idempotent-ish
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --http-method OPTIONS --authorization-type NONE --region "$REGION" || true
aws apigateway put-integration --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --http-method OPTIONS --type MOCK --request-templates '{"application/json":"{\"statusCode\":200}"}' --region "$REGION" || true
aws apigateway put-method-response --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true}' --region "$REGION" || true
read -r -d '' RESPONSE_PARAMETERS <<'JSON' || true
{
  "method.response.header.Access-Control-Allow-Origin": "'*'",
  "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization'",
  "method.response.header.Access-Control-Allow-Methods": "'POST,OPTIONS'"
}
JSON
aws apigateway put-integration-response \
  --rest-api-id "$API_ID" \
  --resource-id "$RESOURCE_ID" \
  --http-method OPTIONS \
  --status-code 200 \
  --selection-pattern '' \
  --response-templates '{"application/json":""}' \
  --response-parameters "$RESPONSE_PARAMETERS" \
  --region "$REGION" || true

# Deploy
aws apigateway create-deployment --rest-api-id "$API_ID" --stage-name dev --description "deployed via infra/deploy-api.sh" --region "$REGION"

echo "API deployed. Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/summarize"
