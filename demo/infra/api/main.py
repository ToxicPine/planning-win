from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from botocore.config import Config
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/signed-url', methods=['POST'])
def generate_signed_url():
    try:
        data = request.get_json()
        if not data or 'key' not in data:
            return jsonify({"error": "Missing key parameter"}), 400

        key = data['key']
        operation = data.get('operation', 'download')
        expires_in = int(data.get('expires_in', 3600))  # Default 1 hour

        # Create S3 client with explicit region and endpoint URL
        s3 = boto3.client(
            's3',
            region_name='eu-west-2',
            endpoint_url='https://s3.eu-west-2.amazonaws.com',
            config=Config(
                signature_version='s3v4',
                region_name='eu-west-2'
            )
        )
        
        # Generate signed URL based on operation
        if operation == 'upload':
            signed_url = s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': os.environ['S3_BUCKET'],
                    'Key': key
                },
                ExpiresIn=expires_in
            )
        elif operation == 'download':
            signed_url = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': os.environ['S3_BUCKET'],
                    'Key': key
                },
                ExpiresIn=expires_in
            )
        elif operation == 'delete':
            signed_url = s3.generate_presigned_url(
                'delete_object',
                Params={
                    'Bucket': os.environ['S3_BUCKET'],
                    'Key': key
                },
                ExpiresIn=expires_in
            )
        else:
            return jsonify({"error": "Invalid operation"}), 400
        
        return jsonify({"signed_url": signed_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    with app.app_context():
        return app.handle_request(event) 