import boto3

dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

table_name = 'version3'


def processor(event, context):
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
            "status": 200,
            "message": "successfully found record",
            "record": record
        }
    else:
        return {
            "status": 404,
            "message": "record not found"
        }
