Architecture and Interview Notes — Healthcare AI on AWS

Purpose
-------
This document explains the architecture choices made in this project and provides concise, high-value talking points you can use in interviews. Use these notes to explain why each AWS service and pattern was chosen, trade-offs considered, and operational concerns.

High-level architecture
-----------------------
- API Gateway (REST) exposes a `/summarize` endpoint to accept text or report references from a frontend.
- Lambda (`BedrockSummarizer`) is the compute layer that calls Amazon Bedrock models to produce summaries and writes metadata/results to DynamoDB.
- DynamoDB (`PatientReports`) stores report metadata and summary outputs.
- Amazon Bedrock is used for model inference (text summarization) — the Lambda acts as the adaptor between the API and Bedrock.
- CI/CD: GitHub Actions workflow performs `sam build` and `sam deploy` in a clean runner to produce repeatable deployments.
- IAM: Lambda uses a dedicated IAM role with a least-privilege inline policy (CloudWatch Logs, DynamoDB access limited to the table, Bedrock invoke actions). The SAM template is parameterized for demo-friendly naming.

Why these AWS services (short answers for interviews)
----------------------------------------------------
- API Gateway: "Serverless" HTTP front door with native Lambda integration, built-in throttling, stages, and ability to configure CORS and usage plans.
- AWS Lambda: event-driven compute that scales automatically, low operational overhead, integrates with CloudWatch and IAM. Fits well for short Bedrock calls.
- Amazon Bedrock: managed endpoint for large language models — avoids managing model infra and lets us call high-quality models via API.
- DynamoDB: single-digit millisecond latency, serverless scaling, and a simple schema for small documents and summaries. `PAY_PER_REQUEST` (on-demand) simplifies billing for demos.
- AWS SAM: simplifies packaging and deployment of serverless apps, supports local testing and integrates with CI pipelines.
- GitHub Actions: reproducible CI/CD in a clean runner — avoids local developer machine issues and demonstrates professional deployment practices for interviews.

Design trade-offs and alternatives (what to say if asked)
--------------------------------------------------------
- Why not EC2/ECS/EKS? Using serverless reduces operational burden and is cost-effective for intermittent workloads. If you required long-running model inference or heavy preprocessing, consider ECS/EKS for custom runtimes.
- Why DynamoDB not RDS? DynamoDB offers low ops and scales for key-value access; RDS would be appropriate if you required complex relational queries or joins.
- Why Bedrock not a self-hosted model? Bedrock removes the need to manage GPUs, scaling, ModelOps, and simplifies compliance when using managed model services.
- Why SAM vs Terraform/CloudFormation? SAM is tailored for serverless apps and speeds up iteration. Terraform is fine if you have multi-cloud or advanced infra features; I used SAM here because it's the idiomatic AWS serverless tool.

Security & Compliance talking points
-----------------------------------
- Principle of least privilege: Lambda uses a dedicated role with narrow permissions (DynamoDB table, logging, Bedrock invoke actions). In production, tighten Bedrock permissions and use VPC endpoints or private networking where possible.
- Secrets & CI: store AWS credentials or use OIDC role assumption in GitHub Actions. `docs/SECRETS.md` outlines recommended repository secrets.
- Data residency: choose region(s) that meet regulatory needs. Bedrock regional availability may vary — verify model availability in your target region.

Operational readiness & reliability
----------------------------------
- Observability: CloudWatch Logs are enabled; consider adding CloudWatch Metrics, Alarms, and X-Ray tracing for distributed tracing. (SAM template can enable `Tracing: Active` for Lambda.)
- Idempotency & retries: When integrating with external model services, handle timeouts and retries in Lambda; consider an asynchronous pattern (SQS + Lambda) for long jobs.
- Scaling: Lambda auto-scales; API Gateway throttling and usage plans protect backend. DynamoDB on-demand handles traffic surges without capacity planning.

Cost considerations
-------------------
- Bedrock model calls are charged per request/compute; for a portfolio/demo, limit input size and request frequency.
- Lambda and API Gateway costs are small at low scale; DynamoDB `PAY_PER_REQUEST` is convenient for demos but may be more expensive at very high sustained read/write rates.

Edge cases & questions interviewers love
---------------------------------------
- How do you handle very large documents? Answer: chunking + streaming to Bedrock, or use asynchronous processing with S3 triggers and SQS.
- What about PII/PHI? Answer: minimize storage of raw PHI, encrypt data at rest (DynamoDB SSE), enforce access controls, and consider data masking before model calls.
- How to scale for many concurrent users? Answer: tune Lambda concurrency, use provisioned concurrency for cold-start-sensitive workloads, and use API Gateway throttling and caching.

Short Q&A (copyable one-liners)
-------------------------------
- "Why SAM?" — "SAM simplifies packaging and deploying serverless apps and integrates well with AWS native features; it's the recommended approach for Lambda+API Gateway stacks."
- "Why DynamoDB?" — "Serverless, low-latency, scales automatically — ideal for storing metadata and summary outputs without managing database servers."
- "How do you secure model calls?" — "Use IAM roles with least privilege, restrict network access as needed, and store sensitive keys in Secrets Manager or use environment variables with restricted KMS encryption."

Files & locations to reference in the repo
-----------------------------------------
- `infra/sam-template.yaml` — SAM template used to deploy API, Lambda, DynamoDB, and IAM role
- `.github/workflows/sam-deploy.yml` — CI workflow to build & deploy
- `infra/iam/bedrock_lambda_policy.json` — example inline policy for IAM reviewers
- `docs/SECRETS.md` — instructions for GitHub secrets and recommended permissions

Next steps you can mention in interviews
---------------------------------------
- Add X-Ray tracing and CloudWatch Alarms for operational monitoring.
- Harden IAM policies further and enable VPC endpoints for Bedrock if required by compliance.
- Add input validation and PII detection before model calls.
- Add a small frontend hosted on S3 + CloudFront for portfolio display.

If you want, I can generate a short slide (3–4 bullets per slide) with these talking points for interview prep.
