import boto3
import json

def lambda_handler(event, context):
    ssm = boto3.client('ssm')

    # Extract parameter details from the event or context
    parameter_name = '/auto.am/pages-scrapped'
    parameter_value = "true"

    try:
        # Write parameter to Parameter Store
        ssm.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type='String',
            Overwrite=True
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Parameter written successfully'}),
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
