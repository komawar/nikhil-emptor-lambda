import re
import uuid

import boto3
from botocore.vendored import requests


s3_client = boto3.client('s3', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')

table_name = 'version2'


def create_table():
    try:
        return dynamodb_client.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'title',
                    'AttributeType': 'S'
                },
            ],
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'title',
                    'KeyType': 'HASH'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )
    except dynamodb_client.exceptions.ResourceInUseException as e:
        print ("Skipping table creation, already exists" + str(e))
        return None


def extract_title(r):
    return re.search(
        '(?<=<title>).+?(?=</title>)',
        r.text,
        re.DOTALL
    ).group().strip()


def store_to_s3(r):
    bucket = 'patronemptor-version2'
    s3_client.create_bucket(Bucket=bucket)
    obj = str(uuid.uuid4())

    s3_client.put_object(Body=r.text, Bucket=bucket, Key=obj)
    obj_url = 'https://%s.s3.amazonaws.com/%s' % (bucket, obj)

    return obj_url


def store_to_dynamodb(title):
    create_table()
    table = dynamodb.Table(table_name)

    table.put_item(
        Item={
            'title': title
        }
    )


def url_parser(event, context):
    url = event

    r = requests.get(url)

    title = extract_title(r)

    obj_url = store_to_s3(r)

    store_to_dynamodb(title)

    return {
        "title": title,
        "S3-URL": obj_url
    }
