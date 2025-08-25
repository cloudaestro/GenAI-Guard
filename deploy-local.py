#!/usr/bin/env python3
"""
Local Deployment Script for GenAI Guardian
Deploys the app using AWS credentials without OIDC
"""

import boto3
import json
import time
import sys
from botocore.exceptions import ClientError

def main():
    print("🚀 GenAI Guardian - Local Deployment")
    print("Deploying FastAPI Bedrock proxy to AWS App Runner")
    
    try:
        # Initialize AWS clients
        app_runner = boto3.client('apprunner', region_name='us-east-1')
        iam = boto3.client('iam')
        sts = boto3.client('sts')
        
        # Get account info
        account_info = sts.get_caller_identity()
        account_id = account_info['Account']
        print(f"✅ AWS credentials configured")
        print(f"📋 AWS Account ID: {account_id}")
        
        # Create App Runner instance role
        print("🔧 Creating App Runner instance role...")
        
        instance_role_trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "tasks.apprunner.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        instance_role_name = "my-bedrock-proxy-app-runner-instance-role"
        
        try:
            iam.create_role(
                RoleName=instance_role_name,
                AssumeRolePolicyDocument=json.dumps(instance_role_trust_policy),
                Description="Role for App Runner to access Bedrock",
            )
            print("✅ Instance role created")
        except ClientError as e:
            if 'already exists' in str(e):
                print("✅ Instance role already exists")
            else:
                raise
        
        # Attach Bedrock policy to instance role
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:ListFoundationModels"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            iam.put_role_policy(
                RoleName=instance_role_name,
                PolicyName="bedrock-access-policy",
                PolicyDocument=json.dumps(bedrock_policy)
            )
            print("✅ Bedrock policy attached")
        except ClientError as e:
            print(f"⚠️  Policy attachment: {e}")
        
        # Create App Runner service
        print("🚀 Creating App Runner service...")
        
        service_configuration = {
            'ServiceName': 'my-bedrock-proxy',
            'SourceConfiguration': {
                'ImageRepository': {
                    'ImageIdentifier': 'public.ecr.aws/docker/library/python:3.11-slim',
                    'ImageConfiguration': {
                        'Port': '8080',
                        'RuntimeEnvironmentVariables': {
                            'BEDROCK_MODEL_ID': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                            'DD_API_KEY': '577c60349a1fda20d9a640459cb907a3',
                            'DD_APP_KEY': 'b1f533b6575381888d732563f525462278f10caf',
                            'DD_SITE': 'datadoghq.com',
                            'DD_ENV': 'dev',
                            'DD_SERVICE': 'my-bedrock-proxy',
                            'AWS_DEFAULT_REGION': 'us-east-1'
                        },
                        'StartCommand': 'pip install -r app/requirements.txt && ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port 8080'
                    },
                    'ImageRepositoryType': 'ECR_PUBLIC'
                }
            },
            'InstanceConfiguration': {
                'Cpu': '0.25 vCPU',
                'Memory': '0.5 GB',
                'InstanceRoleArn': f'arn:aws:iam::{account_id}:role/{instance_role_name}'
            },
            'HealthCheckConfiguration': {
                'Protocol': 'HTTP',
                'Path': '/health',
                'Interval': 10,
                'Timeout': 5,
                'HealthyThreshold': 1,
                'UnhealthyThreshold': 5
            }
        }
        
        try:
            response = app_runner.create_service(**service_configuration)
            service_arn = response['Service']['ServiceArn']
            print(f"✅ App Runner service created: {service_arn}")
            
            # Wait for service to be ready
            print("⏳ Waiting for service to be running...")
            waiter = app_runner.get_waiter('service_running')
            waiter.wait(ServiceArn=service_arn, WaiterConfig={'Delay': 30, 'MaxAttempts': 20})
            
            # Get service details
            service_details = app_runner.describe_service(ServiceArn=service_arn)
            service_url = service_details['Service']['ServiceUrl']
            
            print()
            print("🎉 Deployment Successful!")
            print(f"🌐 App Runner URL: https://{service_url}")
            print(f"📊 Health Check: https://{service_url}/health")
            print(f"📖 API Docs: https://{service_url}/docs")
            print()
            print("🔍 Test your deployment:")
            print(f"curl https://{service_url}/health")
            
        except ClientError as e:
            if 'already exists' in str(e):
                print("✅ Service already exists, getting details...")
                
                # List services to find ours
                services = app_runner.list_services()
                service_arn = None
                
                for service in services['ServiceSummaryList']:
                    if service['ServiceName'] == 'my-bedrock-proxy':
                        service_arn = service['ServiceArn']
                        break
                
                if service_arn:
                    service_details = app_runner.describe_service(ServiceArn=service_arn)
                    service_url = service_details['Service']['ServiceUrl']
                    status = service_details['Service']['Status']
                    
                    print(f"🌐 Existing App Runner URL: https://{service_url}")
                    print(f"📊 Status: {status}")
                    
                    if status != 'RUNNING':
                        print("⏳ Service is not running yet, please wait...")
                else:
                    print("❌ Could not find existing service")
            else:
                raise
        
    except Exception as e:
        print(f"❌ Deployment Error: {e}")
        print()
        print("Make sure you have:")
        print("1. AWS credentials configured")
        print("2. Permissions for App Runner and IAM")
        print("3. boto3 installed (pip install boto3)")
        sys.exit(1)

if __name__ == "__main__":
    main()