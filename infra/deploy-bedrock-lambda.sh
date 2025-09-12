#!/bin/bash
set -e

FUNCTION_NAME="BedrockSummarizer"
ROLE_ARN="arn:aws:iam::838559288637:role/healthcareonaws-lambda-role"
ZIP_FILE="bedrock_lambda_package.zip"

# Absolute paths
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
LAMBDA_DIR="$SCRIPT_DIR/../lambda"
ZIP_PATH="$SCRIPT_DIR/$ZIP_FILE"

echo "📦 Packaging Bedrock Lambda..."
cd "$LAMBDA_DIR"
zip -r "$ZIP_PATH" bedrock_lambda.py

echo "🚀 Deploying Bedrock Lambda in us-east-1..."
aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler bedrock_lambda.lambda_handler \
  --zip-file fileb://$ZIP_PATH \
  --region us-east-1 || \
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://$ZIP_PATH \
  --region us-east-1

echo "✅ Deployment complete!"
