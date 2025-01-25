import boto3
from botocore.exceptions import ClientError
import json
import os
from typing import Optional, Any, Dict
from app.core.logging import LoggerMixin

class SecretsManagerClient(LoggerMixin):
    def __init__(self):
        self.session = boto3.session.Session()
        self.client = self.session.client(
            service_name='secretsmanager',
            region_name=os.getenv('AWS_REGION', 'eu-central-1')
        )
        self.logger.info("Initialized AWS Secrets Manager client")

    def get_secret_value(self, secret_arn: str) -> Optional[str]:
        """
        Retrieve a secret value from AWS Secrets Manager using its ARN
        
        Args:
            secret_arn: The ARN of the secret to retrieve
            
        Returns:
            The secret string value if successful, None otherwise
        """
        try:
            self.logger.info(f"Attempting to retrieve secret: {secret_arn}")
            response = self.client.get_secret_value(SecretId=secret_arn)
            
            if 'SecretString' in response:
                self.logger.info(f"Successfully retrieved secret: {secret_arn}")
                return response['SecretString']
            else:
                self.logger.error(f"Secret {secret_arn} does not contain a string value")
                return None
                
        except ClientError as e:
            self.logger.error(f"Failed to retrieve secret {secret_arn}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving secret {secret_arn}: {str(e)}")
            return None

    def get_json_secret(self, secret_arn: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and parse a JSON secret from AWS Secrets Manager
        
        Args:
            secret_arn: The ARN of the secret to retrieve
            
        Returns:
            The parsed JSON object if successful, None otherwise
        """
        try:
            secret_value = self.get_secret_value(secret_arn)
            if not secret_value:
                return None
                
            return json.loads(secret_value)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse secret {secret_arn} as JSON: {str(e)}")
            return None 