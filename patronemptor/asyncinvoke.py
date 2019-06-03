import json
import uuid

import boto3


lambda_client = boto3.client('lambda')

dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

table_name = 'version3'
table = dynamodb.Table(table_name)


def get_table_arn():
    """A method to get the DynamoDB table ARN string.

    Returns
    -------
    str
        AWS ARN string for the table.
    """
    resp = dynamodb_client.describe_table(
        TableName=table_name
    )
    return resp['Table']['TableArn']


def create_table():
    """A method to create DynamoDB table named *version3*.

    This method attempts to create the DynamoDB table named *version3*. If
    existing, catches *ResourceInUseException* and returns True if table has
    been created or existing, False otherwise.

    Returns
    -------
    Boolean
        A True value if table has been created or existing, False otherwise.
    """
    try:
        dynamodb_client.create_table(
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
        return True
    except dynamodb_client.exceptions.ResourceInUseException as e:
        print ("WARN: Skipping table creation, already exists. "
               "Exception: " + str(e))
        return True
    except Exception as e:
        print ("ERROR: table creation failure. Exception: " + str(e))
        return False


def create_id_and_store(url):
    """A method to create a uuid Key corresponding to url specified and store in
    DynamoDB table *version3*

    This method takes a url as input, creates a uuid Key corresponding to the
    same and creates a record entry in the DynamoDB table. It returns the uuid,
    or None.

    Parameters
    ----------
    url: str
        A url string.

    Returns
    -------
    str
        A uuid string representing the Key Attribute for the record in DynamoDB
        table *version3*. Method will return None on unsuccessful processing.
    """
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
            return None
    else:
        print ("ERROR: Error creating table or record. Aborting.")
        return None


def processor(url, context):
    """A method to process a specified URL and invoke AWS lambda function
     asynchronously.

    This method takes a url as input to process it. An AWS lambda function is
    asynchronously invoked. A dictionary response is sent back to the client.

    Parameters
    ----------
    url: str
        A url *http(s)* string that is accessible publicly or its access has
        been permitted.
    context: AWS Lambda Context Object
        A general AWS Lambda Context Object that contains lambda function
        specific information. Unused in this function, however a mandatory
        Lambda function parameter.

    Returns
    -------
    dict
        A dictionary containing status_code, message and optionally
        processing_id. If a valid url is provided and processing of the same
        is successful, status_code of 200 is returned along with the
        processing_id as a part of the dictionary else status_code of 404 is
        returned, both containing a message.
    """
    if url:
        req_id = create_id_and_store(url)

        if req_id:
            async_param = {
                "req_id": req_id
            }

            lambda_client.invoke_async(
                FunctionName='patronemptor-dev-weblambda',
                InvokeArgs=json.dumps(async_param)
                )

            return {
                    "status_code": 200,
                    "message": "successfully processed the request",
                    'processing_id': req_id
            }

    return {
        "status_code": 404,
        "message": "Bad request, invalid input",
    }
