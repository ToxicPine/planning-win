# Secure Storage Infrastructure

This infrastructure provides secure access to S3 content through CloudFront using signed URLs. It includes:

- An S3 bucket for storing content
- A CloudFront distribution with Origin Access Control (OAC)
- A Lambda function to generate signed URLs
- An API Gateway endpoint to access the signed URL generator

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Node.js 18.x or later
3. AWS CDK CLI installed globally
4. A CloudFront key pair (for signed URLs)

## Setup

1. Create a CloudFront key pair in the AWS Console:
   - Go to Security Credentials
   - Create a new CloudFront key pair
   - Download the private key
   - Note the key pair ID

2. Update the Lambda environment variables in `lib/infra-stack.ts`:
   ```typescript
   environment: {
     CLOUDFRONT_URL: distribution.distributionDomainName,
     CLOUDFRONT_KEY_PAIR_ID: 'YOUR_KEY_PAIR_ID',
     CLOUDFRONT_PRIVATE_KEY: 'YOUR_PRIVATE_KEY',
   }
   ```

3. Install dependencies:
   ```bash
   npm install
   cd lambda
   npm install
   ```

4. Deploy the infrastructure:
   ```bash
   cdk deploy
   ```

## Usage

1. Upload files to the S3 bucket:
   ```bash
   aws s3 cp your-file.txt s3://YOUR_BUCKET_NAME/
   ```

2. Generate a signed URL:
   ```bash
   curl "https://YOUR_API_ENDPOINT/signed-url?key=your-file.txt&expiresIn=3600"
   ```

3. Access the file using the signed URL:
   ```bash
   curl "YOUR_SIGNED_URL"
   ```

## Security Considerations

- The S3 bucket is private and only accessible through CloudFront
- CloudFront uses Origin Access Control (OAC) to authenticate with S3
- All access to content requires a valid signed URL
- Signed URLs expire after the specified time (default: 1 hour)
- CORS is configured to allow access from any origin (customize as needed)

## Cleanup

To remove the infrastructure:

```bash
cdk destroy
```

Note: The S3 bucket will be retained by default to prevent accidental data loss. To delete it, you'll need to manually empty and delete the bucket.
