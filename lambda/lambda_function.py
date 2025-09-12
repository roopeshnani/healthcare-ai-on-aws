import json
import boto3
import os
from datetime import datetime

# DynamoDB table name
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'PatientReports')

# Initialize clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)
bedrock = boto3.client("bedrock", region_name="us-east-1")

# Bedrock model
MODEL_ID = "amazon.nova-premier-v1:0"

def summarize_text(input_text):
    """Call Bedrock model and return summary."""
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"input_text": input_text})
    )
    result = json.loads(response["body"].read())
    summary_text = result.get("output_text") or str(result)
    return summary_text

def store_in_dynamodb(input_text, summary_text, report_id):
    """Insert summary into DynamoDB."""
    item = {
        "ReportID": report_id,
        "InputText": input_text,
        "Summary": summary_text,
        "CreatedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    table.put_item(Item=item)

def lambda_handler(event, context):
    summaries = []

    # Case 1: S3 event
    if 'Records' in event:
        for record in event['Records']:
            s3_bucket = record['s3']['bucket']['name']
            s3_key = record['s3']['object']['key']

            # Download the S3 object
            s3 = boto3.client('s3')
            obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
            input_text = obj['Body'].read().decode('utf-8')

            summary_text = summarize_text(input_text)
            report_id = f"{s3_key.replace('/', '_')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            store_in_dynamodb(input_text, summary_text, report_id)
            summaries.append({"ReportID": report_id, "summary": summary_text})

    # Case 2: Direct text input
    elif 'text' in event:
        input_text = event['text']
        summary_text = summarize_text(input_text)
        report_id = f"manual_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        store_in_dynamodb(input_text, summary_text, report_id)
        summaries.append({"ReportID": report_id, "summary": summary_text})

    else:
        return {"statusCode": 400, "body": "No input text or S3 records found."}

    return {"statusCode": 200, "body": json.dumps(summaries)}
