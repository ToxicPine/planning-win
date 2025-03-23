import { CloudFrontClient, CreateSignedUrlCommand } from '@aws-sdk/client-cloudfront';
import { getSignedUrl } from '@aws-sdk/cloudfront-signer';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

const cloudFrontClient = new CloudFrontClient({});

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    if (!event.queryStringParameters?.key) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing key parameter' }),
      };
    }

    const key = event.queryStringParameters.key;
    const expiresIn = parseInt(event.queryStringParameters.expiresIn || '3600'); // Default 1 hour

    const signedUrl = getSignedUrl({
      url: `${process.env.CLOUDFRONT_URL}/${key}`,
      keyPairId: process.env.CLOUDFRONT_KEY_PAIR_ID!,
      privateKey: process.env.CLOUDFRONT_PRIVATE_KEY!,
      dateLessThan: new Date(Date.now() + expiresIn * 1000).toISOString(),
    });

    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true,
      },
      body: JSON.stringify({ signedUrl }),
    };
  } catch (error) {
    console.error('Error generating signed URL:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to generate signed URL' }),
    };
  }
}; 