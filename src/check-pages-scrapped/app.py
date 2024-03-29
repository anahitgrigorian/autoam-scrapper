import boto3
import botocore

def lambda_handler(event, context):
    ssm = boto3.client('ssm')
    parameter_name = '/auto.am/pages-scrapped'

    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        parameter_value = response['Parameter']['Value']

        if parameter_value == 'true':
            result = 'scrapped'
        else:
            result = 'not_scrapped'

        return result

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            return 'not_scrapped'
        else:
            return str(e)
