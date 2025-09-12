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

---

## Current Progress  
- [x] S3 bucket created and secured  
- [x] DynamoDB setup  
- [ ] Lambda functions for file processing  
- [ ] Bedrock integration for AI insights  
- [ ] API Gateway for exposing endpoints  
- [ ] Frontend / dashboard (optional)  

---

## How to Run This Project Locally  
1. Clone the repository  
   ```bash
   git clone https://github.com/roopeshnani/healthcare-ai-on-aws.git
   cd healthcare-ai-on-aws

