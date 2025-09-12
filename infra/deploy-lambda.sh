#!/bin/bash
set -e

# Configuration
FUNCTION_NAME="ProcessS3ToDynamoDB"
ROLE_ARN="arn:aws:iam::838559288637:role/healthcareonaws-lambda-role"  # Replace with your role ARN
ZIP_FILE="lambda_package.zip"
TABLE_NAME="PatientReports"
REGION="eu-west-2"
HANDLER="lambda_function.lambda_handler"
RUNTIME="python3.11"

# Step 1: Package the Lambda function
echo "📦 Packaging Lambda function..."
SCRIPT_DIR=$(dirname "$0")
LAMBDA_DIR="$SCRIPT_DIR/../lambda"

zip -r "$SCRIPT_DIR/$ZIP_FILE" "$LAMBDA_DIR"

# Step 2: Create the Lambda function
echo "🚀 Deploying Lambda function..."
aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime $RUNTIME \
  --role $ROLE_ARN \
  --handler $HANDLER \
  --zip-file fileb://"$SCRIPT_DIR/$ZIP_FILE" \
  --environment Variables="{DYNAMODB_TABLE=$TABLE_NAME}" \
  --timeout 15 \
  --memory-size 128 \
  --region $REGION

echo "✅ Lambda function $FUNCTION_NAME deployed successfully!"
