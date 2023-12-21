import os
import json
import boto3
from datetime import datetime
import base64
import re

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
posts_table = dynamodb.Table(os.environ.get('POSTS_TABLE_NAME', 'Posts'))
bucket_name = os.environ.get('POST_IMAGE_BUCKET_NAME', 'your-post-image-bucket-name')

def create_post(event, context):
    try:
        # Parse request body
        post_data = json.loads(event['body'])

        # Create a new post
        post_id = str(datetime.now().timestamp())
        created_at = datetime.utcnow().isoformat()

        # Upload image to S3
        image_url = upload_image_to_s3(post_id, post_data.get('image_data', ''))

        item = {
            'id': post_id,
            'category_id': post_data['category_id'],
            'title': post_data['title'],
            'image': image_url,
            'description': post_data['description'],
            'content': post_data['content'],
            'created_at': created_at,
            'updated_at': created_at,
            'slug': generate_slug(post_data['title']),
            'author_id': post_data['author_id'],
            'published': False  # Default value
        }

        posts_table.put_item(Item=item)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Post created successfully', 'post_id': post_id})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_post(event, context):
    try:
        post_id = event['pathParameters']['postId']

        # Get post by ID
        response = posts_table.get_item(Key={'id': post_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Post not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'post': response['Item']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_all_posts(event, context):
    try:
        # Scan the entire table to get all posts
        response = posts_table.scan()

        if 'Items' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No posts found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'posts': response['Items']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def update_post(event, context):
    try:
        post_id = event['pathParameters']['postId']

        # Parse request body
        update_data = json.loads(event['body'])

        # Get the existing post data
        response = posts_table.get_item(Key={'id': post_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Post not found'})
            }

        existing_post = response['Item']

        # Upload new image to S3 if provided
        image_url = existing_post['image']
        if 'image_data' in update_data:
            image_url = upload_image_to_s3(post_id, update_data['image_data'])

        # Update post fields
        updated_at = datetime.utcnow().isoformat()

        updated_post = {
            'category_id': update_data.get('category_id', existing_post['category_id']),
            'title': update_data.get('title', existing_post['title']),
            'image': image_url,
            'description': update_data.get('description', existing_post['description']),
            'content': update_data.get('content', existing_post['content']),
            'created_at': existing_post['created_at'],
            'updated_at': updated_at,
            'slug': generate_slug(update_data.get('title', existing_post['title'])),
            'author_id': existing_post['author_id'],
            'published': existing_post['published']
        }

        # Update post by ID
        posts_table.update_item(
            Key={'id': post_id},
            UpdateExpression='SET category_id = :category_id, title = :title, image = :image, description = :description, content = :content, created_at = :created_at, updated_at = :updated_at, slug = :slug, published = :published',
            ExpressionAttributeValues={
                ':category_id': updated_post['category_id'],
                ':title': updated_post['title'],
                ':image': updated_post['image'],
                ':description': updated_post['description'],
                ':content': updated_post['content'],
                ':created_at': updated_post['created_at'],
                ':updated_at': updated_post['updated_at'],
                ':slug': updated_post['slug'],
                ':published': updated_post['published']
            },
            ReturnValues='ALL_NEW'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Post updated successfully', 'post': updated_post})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def delete_post(event, context):
    try:
        post_id = event['pathParameters']['postId']

        # Delete post by ID
        posts_table.delete_item(Key={'id': post_id})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Post deleted successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def generate_slug(title):
    # Remove special characters and spaces, replace spaces with hyphens
    title_cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', title).strip().lower()
    return re.sub(r'\s+', '-', title_cleaned)

def upload_image_to_s3(post_id, image_data):
    try:
        # Decode base64 image data
        decoded_data = base64.b64decode(image_data)

        # Upload image to S3
        image_key = f'images/{post_id}.png'  # Assuming PNG format, adjust as needed
        s3.put_object(Body=decoded_data, Bucket=bucket_name, Key=image_key, ContentType='image/png')

        # Get the S3 URL
        image_url = f'https://{bucket_name}.s3.amazonaws.com/{image_key}'
        return image_url
    except Exception as e:
        raise Exception(f'Error uploading image to S3: {str(e)}')
