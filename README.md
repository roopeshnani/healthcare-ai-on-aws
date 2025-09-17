#Healthcare AI on AWS Project  

This project demonstrates how to build a healthcare application using **AWS cloud services** combined with **AI (Amazon Bedrock)**.  
It is designed to showcase both **cloud architecture skills** and **AI/ML integration**, targeting real-world healthcare use cases.  

---

## Architecture Overview  
- **Amazon S3** → Stores patient reports (PDF, images, text files).  
- **Amazon DynamoDB** → Stores metadata (patient ID, report name, upload date).  
- **AWS Lambda** → Processes reports and metadata automatically.  
- **Amazon Bedrock** → Adds AI-powered insights (e.g., summarizing medical reports).  
- **IAM** → Secure role-based access.  

For interviewers: see `docs/ARCHITECTURE.md` for concise architecture rationales and suggested talking points.

---

## Current Progress  
- [x] S3 bucket created and secured  
- [x] DynamoDB setup  
- [x] Lambda functions for file processing  
- [x] Bedrock integration for AI insights  
- [ ] API Gateway for exposing endpoints  
- [ ] Frontend / dashboard (optional)  

---

## How to Run This Project Locally  
1. Clone the repository  
   ```bash
   git clone https://github.com/roopeshnani/healthcare-ai-on-aws.git
   cd healthcare-ai-on-aws
   ```

## API Gateway deployment

You already have a deployed REST API for the summarizer in `us-east-1`. To automate redeploys and add CORS, use the helper script:

```bash
# from repository root
chmod +x infra/deploy-api.sh
# Usage: infra/deploy-api.sh <API_ID> <RESOURCE_ID> <LAMBDA_NAME> [region]
infra/deploy-api.sh zz6ukqzkoe fs7hm4 BedrockSummarizer us-east-1
```

Optional: a CloudFormation template is provided at `infra/api-cloudformation.yml` as an example to create the API and integration via IaC.

Test the endpoint with curl:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"text":"Patient has fever and cough"}' https://zz6ukqzkoe.execute-api.us-east-1.amazonaws.com/dev/summarize
```

## Quick deploy (Lambda + API)

You can update the Lambda code and (re)deploy the API with one command from the repository root:

```bash
chmod +x deploy-all.sh infra/deploy-api.sh infra/deploy-lambda.sh
# Usage: ./deploy-all.sh <API_ID> <RESOURCE_ID> <LAMBDA_NAME> [region]
./deploy-all.sh zz6ukqzkoe fs7hm4 BedrockSummarizer us-east-1
```

## Minimal frontend demo

A tiny static HTML file is included at `web/index.html` to exercise the endpoint from a browser. Serve it locally:

```bash
cd web
python3 -m http.server 8000
# then open http://localhost:8000 in your browser
```

## Deploy with SAM (recommended)

This repository includes a SAM template (`infra/sam-template.yaml`) that deploys the Lambda, API Gateway, and DynamoDB table in one stack.

Requirements:
- AWS CLI configured with credentials
- AWS SAM CLI installed (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

Basic deploy (interactive):

```bash
# optional: set STACK_NAME and REGION
export STACK_NAME=healthcare-ai-on-aws
export REGION=us-east-1
infra/deploy-sam.sh
```

After deployment, get the API endpoint:

```bash
aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs' --output json
```

Notes:
- The SAM template uses `BedrockSummarizer` as the Lambda function name and attaches `AmazonBedrockFullAccess` managed policy to let the function call Bedrock. Review and restrict permissions as needed for production.
- The template sets `DYNAMODB_TABLE` environment variable to the created `PatientReports` table.

Local SAM deploy (recommended if you prefer local deploys)
-----------------------------------------------------

If you want to deploy from your machine using SAM, create an isolated Python virtual environment and install the SAM CLI to avoid system package conflicts:

```bash
python3 -m venv ~/.sam-venv
source ~/.sam-venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install aws-sam-cli
cd infra
sam build
sam deploy --guided
```

IAM policy template
-------------------

You can find a minimal IAM policy template for the Bedrock Lambda at `infra/iam/bedrock_lambda_policy.json`. This is a starting point — replace the `Resource` placeholders and adjust actions before applying in production.

CI/CD (GitHub Actions)
-----------------------

To avoid local environment issues and to make deployments repeatable, this repo includes a GitHub Actions workflow that runs `sam build` and `sam deploy` in a clean runner. Add the following repository secrets in your GitHub repository settings before using the workflow:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (e.g. `us-east-1`)
- `SAM_PACKAGE_BUCKET` (an S3 bucket name used to upload packaged artifacts)
- `SAM_STACK_NAME` (the CloudFormation / SAM stack name to deploy)

Trigger the workflow manually from the Actions tab or push to `main`. The workflow is defined at `.github/workflows/sam-deploy.yml` and will print the stack outputs after deploy.

