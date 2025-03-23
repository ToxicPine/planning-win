#!/bin/bash

# Exit on error
set -e

# Create the IAM role with trust relationship
echo "Creating IAM role..."
aws iam create-role \
    --role-name ZappaLambdaRole \
    --assume-role-policy-document file://api/iam_policy.json

# Attach basic Lambda execution policy
echo "Attaching Lambda execution policy..."
aws iam attach-role-policy \
    --role-name ZappaLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Attach additional policies for S3 and CloudFront
echo "Creating and attaching S3 and CloudFront policies..."
aws iam put-role-policy \
    --role-name ZappaLambdaRole \
    --policy-name S3AndCloudFrontAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": "arn:aws:s3:::*/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudfront:CreateSignedUrl"
                ],
                "Resource": "*"
            }
        ]
    }'

echo "IAM role setup complete!" 