import boto3
import json

def lambda_handler(event, context):
    ssm = boto3.client('ssm')
    parameter_name = '/auto.am/pages-scrapped'

    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        parameter_value = response['Parameter']['Value']

        # Customize the logic based on the retrieved parameter value
        if parameter_value == 'true':
            result = 'scrapped'
        else:
            result = 'not_scrapped'

        return {
            'statusCode': 200,
            'body': json.dumps({'result': result}),
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
