#!/bin/bash
set -e

TABLE_NAME="PatientReports"

echo "📌 Creating DynamoDB table: $TABLE_NAME ..."

aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions \
      AttributeName=PatientID,AttributeType=S \
      AttributeName=ReportID,AttributeType=S \
  --key-schema \
      AttributeName=PatientID,KeyType=HASH \
      AttributeName=ReportID,KeyType=RANGE \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region eu-west-2

echo "⏳ Waiting for table to be active..."
aws dynamodb wait table-exists --table-name $TABLE_NAME --region eu-west-2

echo "✅ DynamoDB table $TABLE_NAME created successfully."
