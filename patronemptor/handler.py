import re
import uuid

import boto3
from botocore.vendored import requests


s3_client = boto3.client('s3', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')

table_name = 'version3'


def extract_title(r):
    return re.search(
        '(?<=<title>).+?(?=</title>)',
        r.text,
        re.DOTALL
    ).group().strip()


def store_to_s3(r):
    bucket = 'patronemptor-version2'
    obj = str(uuid.uuid4())
    try:
        s3_client.create_bucket(Bucket=bucket)
        s3_client.put_object(Body=r.text, Bucket=bucket, Key=obj)
        obj_url = 'https://%s.s3.amazonaws.com/%s' % (bucket, obj)
        return obj_url
    except Exception as e:
        print ("ERROR: Could not store object %s to s3 bucket %s. Exception"
               " %s" % (obj, bucket, str(e)))
        raise e


def store_to_dynamodb(record):
    try:
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
                'req_id': record['req_id']['S']
            },
            AttributeUpdates={
                'recordstate': {
                    'Value': record['recordstate'],
                },
                's3_url': {
                    'Value': record['s3_url'],
                },
                'title': {
                    'Value': record['title'],
                }
            },
            TableName=table_name,
        )
    except Exception as e:
        print ("ERROR: Could not store record with ID %s. Exception"
               " %s" % (record['req_id']['S'], str(e)))
        raise e


def read_from_db(req_id):
    response = dynamodb_client.get_item(
        TableName=table_name,
        Key={
            'req_id': {
                'S': req_id
            }
        }
    )
    if response.get('Item'):
        return {
            'req_id': response['Item']['req_id'],
            'url': response['Item']['url'],
            'recordstate': response['Item']['recordstate'],
        }
    else:
        return None


def url_parser(event, context):
    processing_id = event['req_id']
    record = read_from_db(processing_id)
    if record:
        r = requests.get(record['url']['S'])
        title = extract_title(r)
        obj_url = store_to_s3(r)

        new_record = {
            'req_id': record['req_id'],
            'recordstate': 'PROCESSED',
            's3_url': obj_url,
            'title': title
        }
        store_to_dynamodb(new_record)
    else:
        resp = dynamodb_client.describe_table(
            TableName=table_name
        )
        table_arn = resp['Table']['TableArn']
        print ("Bad request. Record with ID %s not found in Database"
               "table %s" % (processing_id, table_arn))
