import re
import uuid

import boto3
from botocore.vendored import requests


s3_client = boto3.client('s3', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')

table_name = 'version3'


def extract_title(html_doc):
    """A method to process a HTML document to extract the *title*.

    Parameters
    ----------
    html_doc:
        HTML document to be processed.

    Returns
    -------
    str
        The title extracted from the HTML document
    """
    return re.search(
        '(?<=<title>).+?(?=</title>)',
        html_doc,
        re.DOTALL
    ).group().strip()


def store_to_s3(html_doc):
    """A method to store the HTML document in *patronemptor-version2* bucket.

    This method takes a HTML document to be stored as input. Creates a uuid obj
    name for the same. It tries to create the S3 bucket and as the
    *s3_client.create_bucket* operation is idempotent, this will create the
    bucket if non-existent and no-op if exists. It stores the HTML document in
    the bucket, creates the object url as per AWS specification and returns the
    object URL.

    Parameters
    ----------
    html_doc: HTML document
        HTML document to be stored.

    Returns
    -------
    obj_url : str
        A url *https* string representing the S3 objects location.
    """
    bucket = 'patronemptor-version2'
    obj = str(uuid.uuid4())
    try:
        s3_client.create_bucket(Bucket=bucket)
        s3_client.put_object(Body=html_doc, Bucket=bucket, Key=obj)
        obj_url = 'https://%s.s3.amazonaws.com/%s' % (bucket, obj)
        return obj_url
    except Exception as e:
        print ("ERROR: Could not store object %s to s3 bucket %s. Exception"
               " %s" % (obj, bucket, str(e)))
        raise e


def store_to_dynamodb(record):
    """A method to store given record in DynamoDB table.

    This method takes a dictionary as input, processes it and stores the Item in
    DynamoDB table *version3*.

    Parameters
    ----------
    record: dict
        A dictionary that has values for req_id, recordstate, s3_url, title for
        the corresponding DynamoDB table to be updated.
    """
    try:
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
                'req_id': record['req_id']
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
    """A method to get an Item from the DynamoDB table.

    Parameters
    ----------
    req_id: string
        A uuid string representing the Key in DynamoDB table *version3*.

    Returns
    -------
    dict
        A dictionary containing req_id, url and recordstate if record is found,
        else an empty dictionary.
    """
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
        return {}


def url_parser(event, context):
    """A method to process record in DynamoDB table using given uuid of the Key.

    This method takes an input of dictionary with req_id (uuid) dictionary key.
    DynamoDB table *version3* is queried for this Key. Processes the HTML
    document url stored in the DynamoDB and updates the DynamoDB. This method is
    intended to be called asynchronously hence, no return value.

    Parameters
    ----------
    event: dict
        A dictionary containing the req_id uuid corresponding to the DynamoDB
        table *version3* record.
    context: AWS Lambda Context Object
        A general AWS Lambda Context Object that contains lambda function
        specific information. Unused in this function, however a mandatory
        Lambda function parameter.
    """
    processing_id = event['req_id']
    record = read_from_db(processing_id)
    if record:
        r = requests.get(record['url']['S'])
        title = extract_title(r.text)
        obj_url = store_to_s3(r.text)

        new_record = {
            'req_id': record['req_id']['S'],
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
