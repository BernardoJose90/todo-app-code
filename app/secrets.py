import json
import boto3
from botocore.exceptions import ClientError

def get_secret():
    """
    Fetches database credentials from AWS Secrets Manager
    and returns them in the same format as secrets_local.py
    """
    secret_name = "todo-db-secret"
    region_name = "eu-west-2"

    # Create a Secrets Manager client.
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Parse the secret JSON string from AWS
    secret = json.loads(get_secret_value_response['SecretString'])

    # Ensure it matches the local format
    return {
        "username": secret.get("username"),
        "password": secret.get("password"),
        "host": secret.get("host"),
        "dbname": secret.get("dbname")
    }
