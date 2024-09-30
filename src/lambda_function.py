import json
import os
import re
import boto3
import requests
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics()

def load_config():
    s3 = boto3.client('s3')
    config_bucket = os.environ['CONFIG_BUCKET']
    config_key = os.environ['CONFIG_KEY']
    
    try:
        response = s3.get_object(Bucket=config_bucket, Key=config_key)
        config = json.loads(response['Body'].read().decode('utf-8'))
        return config
    except ClientError as e:
        logger.error(f"Error loading config: {e}")
        return None

def get_airflow_auth_token():
    secret_name = os.environ['AIRFLOW_SECRET_NAME']
    region_name = os.environ['AWS_REGION']

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Error retrieving Airflow secret: {e}")
        raise e

    secret = json.loads(get_secret_value_response['SecretString'])
    return secret['auth_token']

def match_trigger_file(file_key, config):
    for path, settings in config.items():
        if file_key.startswith(path):
            pattern = settings['trigger_pattern']
            if re.match(pattern, os.path.basename(file_key)):
                return settings['api_url']
    return None

@logger.inject_lambda_context
@metrics.log_metrics
def lambda_handler(event, context):
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        metrics.add_metric(name="ConfigLoadFailure", unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to load configuration')
        }

    auth_token = get_airflow_auth_token()

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        file_key = record['s3']['object']['key']
        
        api_url = match_trigger_file(file_key, config)
        if api_url:
            try:
                headers = {
                    'Authorization': f'Bearer {auth_token}',
                    'Content-Type': 'application/json'
                }
                payload = json.dumps({'file': file_key, 'bucket': bucket})
                response = requests.post(api_url, headers=headers, data=payload)
                response.raise_for_status()
                logger.info(f"Successfully invoked Airflow API for {file_key}")
                metrics.add_metric(name="SuccessfulAPIInvocation", unit=MetricUnit.Count, value=1)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error invoking Airflow API: {e}")
                metrics.add_metric(name="FailedAPIInvocation", unit=MetricUnit.Count, value=1)
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Error invoking Airflow API: {str(e)}')
                }
        else:
            logger.warning(f"No matching trigger pattern found for {file_key}")
            metrics.add_metric(name="NoTriggerMatch", unit=MetricUnit.Count, value=1)

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }