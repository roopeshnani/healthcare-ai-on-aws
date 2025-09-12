import json
import boto3

# Bedrock model
MODEL_ID = "amazon.titan-text-express-v1"

# Use the Bedrock Runtime client
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def lambda_handler(event, context):
    try:
        # Extract text from event
        input_text = event.get("text", "")
        if not input_text:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No text provided in payload"})
            }

        # Call Bedrock model
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": input_text,
                "textGenerationConfig": {
                    "maxTokenCount": 256,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            })
        )

        # Parse model response
        result = json.loads(response["body"].read())
        result_text = result["results"][0]["outputText"]

        # Always return clean JSON
        return {
            "statusCode": 200,
            "body": json.dumps({"summary": result_text})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
