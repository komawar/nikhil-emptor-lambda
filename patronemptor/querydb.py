import boto3


dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

table_name = 'version3'


def processor(event, context):
    """A method to get DynamoDB record in table *version3* for a specified ID.

    This method expects a uuid to fetch DynamoDB table **version3** Item and
    returns the dictionary with the record details.

    Parameters
    ----------
    event: str
        A uuid string that represents a Key in the DynamoDB table named
        **version3**. Used to fetch the table Item record.
    context: AWS Lambda Context Object
        A general AWS Lambda Context Object that contains lambda function
        specific information. Unused in this function, however a mandatory
        Lambda function parameter.

    Returns
    -------
    dict
        A dictionary containing status_code, message and optionally record.
        If a record is found in the table, status_code of 200 is returned along
        with the record as a part of the dictionary else status_code of 404 is
        returned, both containing a message.
    """
    req_id = event

    response = dynamodb_client.get_item(
        TableName=table_name,
        Key={
            'req_id': {
                'S': req_id
            }
        }
    )
    if response.get('Item'):
        record = {
            'req_id': response['Item']['req_id']['S'],
            'url': response['Item']['url']['S'],
            'recordstate': response['Item']['recordstate']['S'],
        }
        if 's3_url' in response['Item']:
            record['s3_url'] = response['Item']['s3_url']['S']
        if 'title' in response['Item']:
            record['title'] = response['Item']['title']['S']

        return {
            "status_code": 200,
            "message": "successfully found record",
            "record": record
        }
    else:
        return {
            "status_code": 404,
            "message": "record not found"
        }
