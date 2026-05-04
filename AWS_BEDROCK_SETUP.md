# AWS Bedrock Integration Guide

## Overview

The Susanoo verification system now uses **AWS Bedrock** for AI-powered identity verification:

- **Face Recognition:** AWS Claude 3.5 Vision model compares selfies against government IDs
- **Document OCR:** AWS Claude 3.5 extracts fields from government ID documents
- **No local ML models needed:** All processing runs on AWS managed infrastructure

## Prerequisites

### 1. AWS Account Setup

You'll need:
- Active AWS Account
- AWS Access Key ID
- AWS Secret Access Key
- IAM permissions for `bedrock:InvokeModel`

### 2. Enable Bedrock Models

1. Go to **AWS Console** → **Amazon Bedrock** → **Model access**
2. Click **Manage model access**
3. Search for **Claude 3.5 Sonnet**
4. Click **Request access** if not already enabled
5. Wait for approval (usually instant)

## Configuration

### Option A: Environment Variables (Recommended for Development)

Create a `.env` file in the `backend/` directory:

```env
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION=us-east-1

# Optional: Set specific AWS profile
AWS_PROFILE=default
```

### Option B: IAM Role (Recommended for Production)

If running on AWS EC2, Lambda, or ECS:

1. Create an IAM role with `AmazonBedrockFullAccess` policy
2. Attach role to your compute resource
3. No environment variables needed - boto3 will use the role

### Option C: AWS Configuration Files

Place credentials in `~/.aws/credentials`:

```
[default]
aws_access_key_id = your_access_key_here
aws_secret_access_key = your_secret_access_key_here

[susanoo]
aws_access_key_id = your_access_key_here
aws_secret_access_key = your_secret_access_key_here
```

And `~/.aws/config`:

```
[default]
region = us-east-1

[profile susanoo]
region = us-east-1
```

## Installation

### 1. Install AWS SDK

```bash
pip install boto3 botocore
```

Or update from requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import boto3; print(f'boto3 version: {boto3.__version__}')"
```

### 3. Test Bedrock Connection

```bash
python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
print('✓ Bedrock client connected successfully!')
"
```

## API Usage

### Face Recognition Verification

```python
from app.services.bedrock_service import BedrockAIService

bedrock = BedrockAIService(region_name='us-east-1')

# Verify selfie against ID
result = bedrock.verify_selfie_with_id(
    selfie_image_data=selfie_bytes,
    id_image_data=id_bytes,
    is_base64=False
)

print(f"Face Match: {result['verified']}")
print(f"Confidence: {result['confidence']}%")
print(f"Liveness Score: {result['liveness_score']}")
```

### Government ID OCR

```python
# Extract fields from government ID
result = bedrock.extract_govt_id_fields(
    id_image_data=id_bytes,
    id_type="DRIVING_LICENSE",
    is_base64=False
)

print(f"Name: {result['extracted_fields'].get('name')}")
print(f"ID Number: {result['extracted_fields'].get('id_number')}")
print(f"Confidence: {result['confidence']}%")
```

## Cost Estimation

### Bedrock Pricing (as of May 2026)

**Claude 3.5 Sonnet Vision Model:**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Typical verification flow:**
- Face comparison: ~500 input tokens, ~200 output tokens
- OCR extraction: ~300 input tokens, ~150 output tokens
- **Total per verification:** ~0.01-0.02 USD

**For 1000 verifications/day:**
- ~$10-20/day
- ~$300-600/month
- **vs. Local ML models:** Server costs, GPU rentals, maintenance overhead

## Error Handling

### Common Issues

#### 1. Access Denied

```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the InvokeModel operation
```

**Solution:**
- Verify AWS credentials are correct
- Check IAM user/role has `bedrock:InvokeModel` permissions
- Ensure region is correct

#### 2. Model Not Accessible

```
botocore.exceptions.ClientError: ValidationException: Could not validate the request body.
```

**Solution:**
- Enable Claude 3.5 Sonnet in Model access
- Wait for model access approval
- Check region supports the model

#### 3. Image Format Error

```
botocore.exceptions.ClientError: ValidationException: Invalid media type for image
```

**Solution:**
- Ensure images are JPEG or PNG
- Check image is base64 encoded if required
- Verify image size < 20MB

### Retry Logic

The service automatically includes retry logic for transient errors:

```python
# Bedrock service retries up to 3 times on transient errors
# Exponential backoff: 1s, 2s, 4s delays
result = bedrock.verify_selfie_with_id(selfie_bytes, id_bytes)
```

## Monitoring & Logging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show all boto3 API calls
```

### CloudWatch Monitoring

Set up CloudWatch alarms for:

1. **Bedrock API Errors**
   - Track `ClientError` exceptions
   - Monitor for rate limiting (4xx errors)

2. **Verification Accuracy**
   - Track `verified=True` vs `verified=False` ratio
   - Monitor average confidence scores

3. **Cost Tracking**
   - Set up cost alerts for monthly budget

## Production Deployment

### AWS Lambda (Recommended)

1. Create Lambda function with Bedrock permissions
2. Deploy verification endpoints as Lambda handlers
3. Use API Gateway for HTTP endpoints

### ECS/Fargate

1. Create task role with Bedrock permissions
2. Attach role to ECS task definition
3. Deploy FastAPI container

### On-Premises

1. Use IAM user access keys
2. Ensure outbound HTTPS connectivity to AWS Bedrock endpoints
3. Implement request signing with boto3

## Cost Optimization

### 1. Batch Processing

For multiple verifications, batch requests:

```python
results = []
for selfie, id_doc in verification_batch:
    result = bedrock.verify_selfie_with_id(selfie, id_doc)
    results.append(result)
```

### 2. Caching

Store verification results for 24 hours:

```python
# Cache successful verifications in Redis
if result['verified']:
    redis_client.setex(f"verified_{worker_id}", 86400, json.dumps(result))
```

### 3. Model Selection

Claude 3.5 Sonnet is optimal for:
- Best accuracy/cost ratio
- Fast inference (< 5s per request)
- Supports vision/multimodal tasks

## Troubleshooting

### Step 1: Verify AWS Credentials

```bash
aws sts get-caller-identity
```

### Step 2: Check Bedrock Availability

```bash
aws bedrock list-foundation-models --region us-east-1
```

### Step 3: Test Direct API Call

```python
import boto3
import json

client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022',
    contentType='application/json',
    accept='application/json',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-06-01",
        "max_tokens": 100,
        "messages": [{
            "role": "user",
            "content": "Hello, are you working?"
        }]
    })
)
print(response['body'].read())
```

## Migration from Local Models

### Before (Local FaceNet + Tesseract)

- Complex setup: MTCNN, face_recognition, tesseract-ocr
- GPU requirements: 6GB+ VRAM
- Maintenance: Regular model updates, bug fixes
- **Cost:** Infrastructure + maintenance

### After (AWS Bedrock Claude Vision)

- Simple setup: `pip install boto3`
- No GPU needed: Runs on serverless AWS infrastructure
- No maintenance: AWS manages model updates
- **Cost:** Per-API-call pricing (~$0.01-0.02 per verification)

## Support

For issues:
1. Check AWS Bedrock documentation: https://docs.aws.amazon.com/bedrock/
2. Review boto3 documentation: https://boto3.amazonaws.com/v1/documentation/
3. Check logs in CloudWatch: https://console.aws.amazon.com/cloudwatch/

---

**Status:** ✅ Bedrock integration complete and ready for deployment
**Last Updated:** May 4, 2026
