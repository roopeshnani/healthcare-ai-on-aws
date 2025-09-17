import json

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))  # Debug log

    text = None

    # Case 1: API Gateway proxy (body is JSON string)
    if "body" in event and event["body"]:
        try:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
            text = body.get("text")
        except Exception as e:
            print("Error parsing body:", e)

    # Case 2: Direct invoke with {"text": "..."}
    elif "text" in event:
        text = event["text"]

    if not text:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": "No text provided in payload"})
        }

    # Mock Bedrock summarization
    summary = f"Summary of: {text[:100]}..."

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({"summary": summary})
    }
