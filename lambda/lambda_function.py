import json
import boto3
import os
from datetime import datetime

# DynamoDB table name
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'PatientReports')

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    for record in event['Records']:
        s3_bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']

        # Create a simple ReportID based on timestamp
        report_id = s3_key.replace("/", "_")
        patient_id = s3_key.split("_")[0] if "_" in s3_key else "unknown"

        item = {
            'PatientID': patient_id,
            'ReportID': report_id,
            'FileName': s3_key,
            'UploadDate': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'S3Path': f"s3://{s3_bucket}/{s3_key}"
        }

        # Insert into DynamoDB
        table.put_item(Item=item)
        print(f"Inserted item: {item}")

    return {
        'statusCode': 200,
        'body': json.dumps('DynamoDB insert successful!')
    }
