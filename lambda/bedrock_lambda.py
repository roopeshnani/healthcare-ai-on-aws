import json
import base64
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Config (defaults)
REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.titan-text-express-v1")
DDB_TABLE = os.environ.get("DYNAMODB_TABLE")  # optional

# Clients
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION) if DDB_TABLE else None
table = dynamodb.Table(DDB_TABLE) if dynamodb else None

def _extract_text_from_bedrock_result(result):
    # handle multiple response shapes gracefully
    if isinstance(result, dict):
        if "results" in result and isinstance(result["results"], list):
            return result["results"][0].get("outputText") or result["results"][0].get("output")
        if "generatedText" in result:
            return result["generatedText"]
        if "outputText" in result:
            return result["outputText"]
    # fallback: stringify
    try:
        return str(result)
    except Exception:
        return ""

def _parse_event_body(event):
    """
    Returns a dict parsed from the incoming event, supporting:
      - API Gateway proxy: event['body'] (string or base64)
      - direct lambda invoke: event is already a dict with 'text'
      - S3 events (keeps original structure)
    """
    if not isinstance(event, dict):
        return {}

    # Direct invoke with payload JSON: {"text": "..."}
    if "text" in event:
        return event

    # API Gateway proxy: body may be a string or base64-encoded
    if "body" in event:
        body = event["body"]
        # If API Gateway set isBase64Encoded true, decode first
        if event.get("isBase64Encoded"):
            try:
                body_bytes = base64.b64decode(body)
                body = body_bytes.decode("utf-8")
            except Exception as e:
                print("Base64 decode failed:", e)
                return {}
        # if body is still string try to parse JSON
        if isinstance(body, str):
            try:
                return json.loads(body)
            except Exception as e:
                print("JSON parse of body failed:", e, "raw body:", body)
                return {}
        elif isinstance(body, dict):
            return body

    # S3-like event (Records)
    if "Records" in event:
        return event

    return {}

def lambda_handler(event, context):
    print("EVENT (raw):", json.dumps(event))
    try:
        payload = _parse_event_body(event)
        # If payload empty and event contains S3 Records, let that flow through
        if not payload and "Records" in event:
            payload = event

        text = None
        if isinstance(payload, dict):
            text = payload.get("text")

        # fallback for S3-style: we create a small descriptive text
        if not text and isinstance(payload, dict) and "Records" in payload:
            rec = payload["Records"][0]
            s3obj = rec.get("s3", {}).get("object", {}).get("key")
            s3bucket = rec.get("s3", {}).get("bucket", {}).get("name")
            text = f"New report uploaded: s3://{s3bucket}/{s3obj}"

        if not text:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization"
                },
                "body": json.dumps({"error": "No text provided in payload"})
            }

        # Call Bedrock model
        call_body = {
            "inputText": text,
            # tweak generation settings if desired
            "textGenerationConfig": {
                "maxTokenCount": 512,
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(call_body)
        )

        # response['body'] can be a streaming body
        raw = response.get("body")
        if hasattr(raw, "read"):
            raw_bytes = raw.read()
            if isinstance(raw_bytes, bytes):
                raw_text = raw_bytes.decode("utf-8")
            else:
                raw_text = str(raw_bytes)
        else:
            raw_text = json.dumps(raw) if not isinstance(raw, str) else raw

        try:
            result_json = json.loads(raw_text)
        except Exception:
            # if not JSON, keep raw_text
            result_json = {"raw": raw_text}

        summary = _extract_text_from_bedrock_result(result_json)

        # If the model returned an empty string or a refusal/error message, surface that clearly
        low = (summary or "").lower()
        refusal_signals = ["sorry - this model is unable to respond", "unable to respond", "cannot respond", "i'm unable to"]
        if not summary or any(sig in low for sig in refusal_signals):
            # Do not save to DynamoDB in this case — return a 502 with the raw response to aid debugging
            return {
                "statusCode": 502,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization"
                },
                "body": json.dumps({"error": "Model unable to generate a summary", "raw": result_json})
            }

        # store to DynamoDB if table configured
        if table:
            try:
                report_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                item = {
                    "PatientID": payload.get("patient_id", "unknown"),
                    "ReportID": report_id,
                    "OriginalText": text,
                    "Summary": summary,
                    "CreatedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                table.put_item(Item=item)
                print("Saved item to DynamoDB:", item)
            except ClientError as e:
                print("DynamoDB put_item failed:", e)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({"summary": summary})
        }

    except ClientError as e:
        print("AWS ClientError:", e)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({"error": str(e)})
        }

    except Exception as e:
        print("General error:", e)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({"error": str(e)})
        }
