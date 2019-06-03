import json
import uuid

import boto3


lambda_client = boto3.client('lambda')

dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

table_name = 'version3'
table = dynamodb.Table(table_name)


def get_table_arn():
    resp = dynamodb_client.describe_table(
        TableName=table_name
    )
    return resp['Table']['TableArn']


def create_table():
    try:
        return dynamodb_client.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'req_id',
                    'AttributeType': 'S'
                }
            ],
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'req_id',
                    'KeyType': 'HASH'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )
    except dynamodb_client.exceptions.ResourceInUseException as e:
        print ("WARN: Skipping table creation, already exists. "
               "Exception: " + str(e))
        return True
    except Exception as e:
        print ("ERROR: table creation failure. Exception: " + str(e))
        return False


def create_id_and_store(url):
    req_id = str(uuid.uuid4())

    if create_table():
        try:
            table.put_item(
                Item={
                    'req_id': req_id,
                    'url': url,
                    'recordstate': 'PENDING'
                }
            )
            return req_id
        except Exception as e:
            print ("Exception %s raised while creating Item with ID %s in the "
                   "database table %s" % (str(e), req_id, get_table_arn()))
    else:
        print ("ERROR: Error creating table or record. Aborting.")
        return None


def processor(event, context):
    if event:
        req_id = create_id_and_store(event)

        if req_id:
            async_param = {
                "req_id": req_id
            }

            lambda_client.invoke_async(
                FunctionName='patronemptor-dev-weblambda',
                InvokeArgs=json.dumps(async_param)
                )

            return {
                    "status": 200,
                    "message": "successfully processed the request",
                    'processing_id': req_id
            }

    return {
        "status": 404,
        "message": "Bad request, invalid input",
    }
