#! /bin/bash
# Script to create a secure s3 bucket 

BUCKET_NAME="med-reports-2025"
REGION="eu-west-2"


#Creating bucket
aws s3api create-bucket \
   --bucket $BUCKET_NAME \
   --region $REGION \
   --create-bucket-configuration LocationConstraint=$REGION

#Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'

# Enabling encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]
  }'

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

echo "✅ S3 bucket $BUCKET_NAME created and secured."
