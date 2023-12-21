import os
import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
profiles_table = dynamodb.Table(os.environ.get('PROFILES_TABLE_NAME', 'Profiles'))
s3 = boto3.client('s3')
bucket_name = os.environ.get('AVATAR_IMAGE_BUCKET_NAME', 'your-avatar-image-bucket-name')

def create_profile(event, context):
    try:
        # Parse request body
        profile_data = json.loads(event['body'])

        # Create a new profile
        profile_id = str(datetime.now().timestamp())
        updated_at = datetime.utcnow().isoformat()

        # Upload avatar image to S3
        avatar_url = upload_avatar_to_s3(profile_id, profile_data.get('avatar_data', ''))

        item = {
            'id': profile_id,
            'updated_at': updated_at,
            'username': profile_data['username'],
            'full_name': profile_data['full_name'],
            'avatar_url': avatar_url
        }

        profiles_table.put_item(Item=item)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Profile created successfully', 'profile_id': profile_id})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_profile(event, context):
    try:
        profile_id = event['pathParameters']['profileId']

        # Get profile by ID
        response = profiles_table.get_item(Key={'id': profile_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Profile not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'profile': response['Item']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_all_profiles(event, context):
    try:
        # Scan the entire table to get all profiles
        response = profiles_table.scan()

        if 'Items' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No profiles found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'profiles': response['Items']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def update_profile(event, context):
    try:
        profile_id = event['pathParameters']['profileId']

        # Parse request body
        update_data = json.loads(event['body'])

        # Get the existing profile data
        response = profiles_table.get_item(Key={'id': profile_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Profile not found'})
            }

        existing_profile = response['Item']

        # Upload new avatar image to S3 if provided
        avatar_url = existing_profile['avatar_url']
        if 'avatar_data' in update_data:
            avatar_url = upload_avatar_to_s3(profile_id, update_data['avatar_data'])

        # Update profile fields
        updated_at = datetime.utcnow().isoformat()

        updated_profile = {
            'username': update_data.get('username', existing_profile['username']),
            'full_name': update_data.get('full_name', existing_profile['full_name']),
            'avatar_url': avatar_url,
            'updated_at': updated_at
        }

        # Update profile by ID
        profiles_table.update_item(
            Key={'id': profile_id},
            UpdateExpression='SET username = :username, full_name = :full_name, avatar_url = :avatar_url, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':username': updated_profile['username'],
                ':full_name': updated_profile['full_name'],
                ':avatar_url': updated_profile['avatar_url'],
                ':updated_at': updated_profile['updated_at']
            },
            ReturnValues='ALL_NEW'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Profile updated successfully', 'profile': updated_profile})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def delete_profile(event, context):
    try:
        profile_id = event['pathParameters']['profileId']

        # Delete profile by ID
        profiles_table.delete_item(Key={'id': profile_id})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Profile deleted successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def upload_avatar_to_s3(profile_id, avatar_data):
    try:
        # Decode base64 avatar data
        decoded_data = base64.b64decode(avatar_data)

        # Upload avatar image to S3
        avatar_key = f'avatars/{profile_id}.png'  # Assuming PNG format, adjust as needed
        s3.put_object(Body=decoded_data, Bucket=bucket_name, Key=avatar_key, ContentType='image/png')

        # Get the S3 URL
        avatar_url = f'https://{bucket_name}.s3.amazonaws.com/{avatar_key}'
        return avatar_url
    except Exception as e:
        raise Exception(f'Error uploading avatar to S3: {str(e)}')
