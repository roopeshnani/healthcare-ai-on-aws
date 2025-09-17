Secrets and GitHub Actions setup

This project uses GitHub Actions to build and deploy the SAM stack. Before running the workflow, add the following repository secrets in GitHub (Settings → Secrets → Actions):

- `AWS_ACCESS_KEY_ID` — IAM access key with permissions to deploy CloudFormation stacks and create resources.
- `AWS_SECRET_ACCESS_KEY` — Secret key for the above access key.
- `AWS_REGION` — e.g. `us-east-1`.
- `SAM_PACKAGE_BUCKET` — existing S3 bucket name (must be in the same region) for SAM packaging or leave blank to make the workflow create a temp bucket.
- `SAM_STACK_NAME` — the CloudFormation stack name to deploy, e.g. `healthcare-ai-on-aws`.
 - `SAM_NAME_PREFIX` — optional prefix used to avoid naming collisions (e.g. your-github-handle or `demo`). If set, resources will be created with this prefix.

Example (I created a packaging bucket for you in `us-east-1` during this session):

- `SAM_PACKAGE_BUCKET`: `healthcare-ai-portfolio-sam-package-1758082430`
- `SAM_STACK_NAME`: `healthcare-ai-portfolio`
- `SAM_NAME_PREFIX`: `roopesh-demo`

Recommended IAM permissions for the deploy key (least privileges):
- `cloudformation:*` on the stack and necessary resource ARNs
- `s3:PutObject`, `s3:GetObject`, `s3:CreateBucket` on the packaging bucket
- `lambda:*` (or limited to Create/Update/Invoke) on the function
- `apigateway:*` on the API resources
- `dynamodb:*` on the table resource
- `iam:PassRole` for roles used by the Lambda

If you don't want to grant broad permissions to your deploy key, consider using an OIDC role-to-assume pattern via `aws-actions/configure-aws-credentials` and set `AWS_ROLE_TO_ASSUME` in the workflow.
