#!/bin/bash
set -ex

LAMBDA_NAME="BedrockSummarizer"
PROJECT_DIR=$(pwd)
BUILD_DIR="$PROJECT_DIR/build"
ZIP_FILE="$PROJECT_DIR/function.zip"

echo "🧹 Cleaning previous build..."
rm -rf $BUILD_DIR $ZIP_FILE
mkdir -p $BUILD_DIR

echo "📦 Installing dependencies..."
REQ_FILE="$PROJECT_DIR/lambda/requirements.txt"
if [ -f "$REQ_FILE" ]; then
    grep -vE "^(boto3|botocore)" "$REQ_FILE" > /tmp/filtered-reqs.txt
    if [ -s /tmp/filtered-reqs.txt ]; then
        python3 -m pip install -r /tmp/filtered-reqs.txt -t $BUILD_DIR
    else
        echo "⚠️ No external dependencies to install, skipping"
    fi
else
    echo "⚠️ No requirements.txt found, skipping dependencies"
fi

echo "📄 Copying Lambda code..."
cp lambda/bedrock_lambda.py $BUILD_DIR/
ls -lh $BUILD_DIR

echo "🗜️ Creating deployment package..."
cd $BUILD_DIR
zip -r ../function.zip .
cd $PROJECT_DIR

echo "🚀 Updating Lambda function: $LAMBDA_NAME ..."
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb://function.zip \
    --region us-east-1

echo "✅ Deployment complete!"
rm -rf $BUILD_DIR
