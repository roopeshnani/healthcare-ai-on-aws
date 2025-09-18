import json
import sys
import types
from pathlib import Path


class DummyBedrockRefusalClient:
    def invoke_model(self, *args, **kwargs):
        # Simulate a model refusal body string
        payload = {"message": "Sorry - this model is unable to respond to this request."}
        return {"body": json.dumps(payload)}


def load_module_from_lambda(name: str):
    module_path = Path(__file__).resolve().parents[1] / 'lambda' / f"{name}.py"

    fake_boto3 = types.ModuleType("boto3")

    def fake_client(*args, **kwargs):
        return DummyBedrockRefusalClient()

    class FakeResource:
        def Table(self, name):
            class DummyTable:
                def put_item(self, Item):
                    raise AssertionError("DynamoDB put_item should not be called on refusal")
            return DummyTable()

    fake_boto3.client = fake_client
    fake_boto3.resource = lambda **kw: FakeResource()

    source = module_path.read_text()
    module = types.ModuleType(name)

    real_boto3 = sys.modules.get('boto3')
    sys.modules['boto3'] = fake_boto3
    try:
        module.__dict__.update({'os': __import__('os'), 'json': __import__('json'), 'datetime': __import__('datetime'), 'base64': __import__('base64'), 'botocore': __import__('botocore')})
        exec(compile(source, str(module_path), 'exec'), module.__dict__)
    finally:
        if real_boto3 is not None:
            sys.modules['boto3'] = real_boto3
        else:
            del sys.modules['boto3']

    return module


def test_bedrock_refusal_returns_502():
    mod = load_module_from_lambda('bedrock_lambda')
    event = {"httpMethod": "POST", "body": json.dumps({"text": "Some patient report text"})}
    resp = mod.lambda_handler(event, {})
    assert resp['statusCode'] == 502
    body = json.loads(resp['body'])
    assert 'error' in body and body['error'].startswith('Model unable')
    assert 'raw' in body
