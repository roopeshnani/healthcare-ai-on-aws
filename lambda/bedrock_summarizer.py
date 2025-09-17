import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

# Config
REGION = os.environ.get("AWS_REGION", "eu-west-2")  # match your bucket region
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.titan-text-express-v1")
DDB_TABLE = os.environ.get("DYNAMODB_TABLE", "PatientReports")

# Clients
s3 = boto3.client("s3", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(DDB_TABLE)

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    try:
        # Handle S3 event
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Download file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        text_data = response["Body"].read().decode("utf-8")

        print(f"Downloaded file {key} from {bucket}")

        # Call Bedrock
        call_body = {
            "inputText": text_data,
            "textGenerationConfig": {
                "maxTokenCount": 512,
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        bedrock_response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(call_body)
        )

        raw = bedrock_response["body"].read().decode("utf-8")
        result_json = json.loads(raw)
        summary = result_json.get("results", [{}])[0].get("outputText", "No summary")

        # Store in DynamoDB
        report_id = key
        patient_id = key.split("_")[0] if "_" in key else "unknown"

        item = {
            "PatientID": patient_id,
            "ReportID": report_id,
            "FileName": key,
            "S3Path": f"s3://{bucket}/{key}",
            "OriginalText": text_data,
            "Summary": summary,
            "UploadDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        table.put_item(Item=item)
        print("Saved summarized report to DynamoDB:", item)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Summary stored", "summary": summary})
        }

    except ClientError as e:
        print("AWS ClientError:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    except Exception as e:
        print("General error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
