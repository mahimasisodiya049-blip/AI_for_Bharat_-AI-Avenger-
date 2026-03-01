# Error Handling Documentation

## Overview

The KiroFeed API implements comprehensive error handling to prevent server crashes and provide clear feedback to clients.

## Global Exception Handlers

### 1. AWS Credentials Error (500)
**Trigger:** Missing or invalid AWS credentials

**Response:**
```json
{
  "detail": "AWS credentials not found. Please check your environment variables.",
  "error_type": "AWS_CREDENTIALS_ERROR",
  "hint": "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file"
}
```

**Solution:**
- Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `backend/.env`
- Run `aws configure` to set up AWS CLI credentials

### 2. AWS Throttling Error (429)
**Trigger:** Too many requests to AWS services (Bedrock, S3, DynamoDB)

**Response:**
```json
{
  "detail": "AWS service rate limit exceeded. Please try again in a moment.",
  "error_type": "THROTTLING_ERROR"
}
```

**Solution:**
- Wait a few seconds and retry
- Implement exponential backoff in client
- Consider requesting higher service limits from AWS

### 3. AWS Access Denied (403)
**Trigger:** Insufficient IAM permissions

**Response:**
```json
{
  "detail": "Access denied to AWS service. Please check your IAM permissions.",
  "error_type": "ACCESS_DENIED",
  "hint": "Ensure your AWS user has permissions for Bedrock, S3, DynamoDB, and Cognito"
}
```

**Solution:**
- Attach required IAM policies to your AWS user:
  - `AmazonS3FullAccess`
  - `AmazonDynamoDBFullAccess`
  - `AmazonCognitoPowerUser`
  - `AmazonBedrockFullAccess`

### 4. AWS Resource Not Found (404)
**Trigger:** S3 bucket, DynamoDB table, or Cognito pool doesn't exist

**Response:**
```json
{
  "detail": "AWS resource not found. Please ensure all services are set up.",
  "error_type": "RESOURCE_NOT_FOUND",
  "hint": "Run 'python aws_setup.py' to create required AWS resources"
}
```

**Solution:**
```bash
cd backend
python aws_setup.py
```

## Endpoint-Specific Error Handling

### Document Upload Errors

#### Invalid File Type (400)
```json
{
  "detail": "Invalid file type. Only PDF files are allowed."
}
```

#### File Too Large (400)
```json
{
  "detail": "File size exceeds maximum allowed size of 50MB"
}
```

#### Empty File (400)
```json
{
  "detail": "File is empty"
}
```

### Translation Service Errors

#### Bhashini API Timeout (503)
```json
{
  "detail": "Translation service timeout. The service did not respond within 10 seconds."
}
```

**Handling:** The API automatically falls back to English if translation fails.

#### Bhashini API Unavailable (503)
```json
{
  "detail": "Translation service unavailable. Please check your internet connection."
}
```

#### Bhashini Rate Limit (503)
```json
{
  "detail": "Bhashini API rate limit exceeded. Please try again later."
}
```

### Authentication Errors

#### Invalid Credentials (401)
```json
{
  "detail": "Invalid email or password"
}
```

#### Expired Token (401)
```json
{
  "detail": "Invalid or expired token"
}
```

#### User Already Exists (400)
```json
{
  "detail": "User with this email already exists"
}
```

## Error Handling Best Practices

### Client-Side Handling

```javascript
try {
  const response = await fetch('/documents/upload', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    
    // Handle specific error types
    if (error.error_type === 'AWS_CREDENTIALS_ERROR') {
      alert('Server configuration error. Please contact support.');
    } else if (error.error_type === 'THROTTLING_ERROR') {
      // Retry with exponential backoff
      setTimeout(() => retryUpload(), 2000);
    } else {
      alert(error.detail);
    }
  }
} catch (error) {
  console.error('Network error:', error);
}
```

### Retry Logic

For transient errors (throttling, timeouts), implement exponential backoff:

```javascript
async function uploadWithRetry(file, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await uploadDocument(file);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## Logging

All errors are logged with appropriate context:

```
2026-02-28 11:23:57,104 - __main__ - ERROR - AWS credentials error: Unable to locate credentials
2026-02-28 11:24:15,234 - services.translation_service - ERROR - Bhashini API timeout after 10 seconds
```

Check logs for debugging:
- Console output when running locally
- CloudWatch Logs when deployed to AWS Lambda

## Testing Error Handling

### Test AWS Credentials Error
```bash
# Remove AWS credentials temporarily
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY

# Try to upload a document - should get 500 error with clear message
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.pdf" \
  -H "Authorization: Bearer <token>"
```

### Test File Validation
```bash
# Try to upload non-PDF file
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.txt" \
  -H "Authorization: Bearer <token>"
```

### Test Translation Timeout
```python
# In translation_service.py, set BHASHINI_TIMEOUT = 0.001
# This will trigger immediate timeout for testing
```

## Production Recommendations

1. **Enable CloudWatch Logging** for all Lambda functions
2. **Set up CloudWatch Alarms** for error rates
3. **Implement Circuit Breakers** for external API calls
4. **Use AWS X-Ray** for distributed tracing
5. **Monitor Bedrock Quotas** to avoid throttling
6. **Implement Request Queuing** for high-traffic scenarios
7. **Add Health Check Endpoints** that verify AWS connectivity

## Support

If you encounter errors not covered here:
1. Check the server logs for detailed error messages
2. Verify AWS credentials and permissions
3. Ensure all AWS resources are created (`python aws_setup.py`)
4. Check network connectivity to AWS services
5. Review the API documentation at `http://localhost:8000/docs`
