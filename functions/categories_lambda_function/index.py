import os
import json
import boto3
from datetime import datetime
import re


dynamodb = boto3.resource('dynamodb')
categories_table = dynamodb.Table(os.environ.get('CATEGORIES_TABLE_NAME', 'Categories'))

def create_category(event, context):
    try:
        # Parse request body
        category_data = json.loads(event['body'])

        # Create a new category
        category_id = str(datetime.now().timestamp())
        created_at = datetime.utcnow().isoformat()

        item = {
            'id': category_id,
            'title': category_data['title'],
            'created_at': created_at,
            'slug': generate_slug(category_data['title'])
        }

        categories_table.put_item(Item=item)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Category created successfully', 'category_id': category_id})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_category(event, context):
    try:
        category_id = event['pathParameters']['categoryId']

        # Get category by ID
        response = categories_table.get_item(Key={'id': category_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Category not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'category': response['Item']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_all_categories(event, context):
    try:
        # Scan the entire table to get all categories
        response = categories_table.scan()

        if 'Items' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No categories found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'categories': response['Items']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def update_category(event, context):
    try:
        category_id = event['pathParameters']['categoryId']

        # Parse request body
        update_data = json.loads(event['body'])

        # Get the existing category data
        response = categories_table.get_item(Key={'id': category_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Category not found'})
            }

        existing_category = response['Item']

        # Update category fields
        updated_at = datetime.utcnow().isoformat()

        updated_category = {
            'title': update_data.get('title', existing_category['title']),
            'created_at': existing_category['created_at'],
            'slug': generate_slug(update_data.get('title', existing_category['title']))
        }

        # Update category by ID
        categories_table.update_item(
            Key={'id': category_id},
            UpdateExpression='SET title = :title, created_at = :created_at, slug = :slug',
            ExpressionAttributeValues={
                ':title': updated_category['title'],
                ':created_at': updated_category['created_at'],
                ':slug': updated_category['slug']
            },
            ReturnValues='ALL_NEW'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Category updated successfully', 'category': updated_category})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def delete_category(event, context):
    try:
        category_id = event['pathParameters']['categoryId']

        # Delete category by ID
        categories_table.delete_item(Key={'id': category_id})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Category deleted successfully'})
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
