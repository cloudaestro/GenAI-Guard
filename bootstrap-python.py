#!/usr/bin/env python3
"""
GenAI Guardian Bootstrap Script (Python version)
Creates OIDC provider and IAM role for GitHub Actions
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError

def main():
    print("🚀 GenAI Guardian Bootstrap - Python Version")
    print("Creating GitHub OIDC Provider and IAM Role")
    
    try:
        # Initialize AWS clients
        iam = boto3.client('iam')
        sts = boto3.client('sts')
        
        # Get account ID
        account_info = sts.get_caller_identity()
        account_id = account_info['Account']
        print(f"✅ AWS credentials configured")
        print(f"📋 AWS Account ID: {account_id}")
        
        # Create OIDC Provider
        print("🔧 Creating GitHub OIDC Provider...")
        oidc_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
        
        try:
            iam.create_open_id_connect_provider(
                Url='https://token.actions.githubusercontent.com',
                ClientIDList=['sts.amazonaws.com'],
                ThumbprintList=[
                    '6938fd4d98bab03faadb97b34396831e3780aea1',
                    '1c58a3a8518e8759bf075b76b750d4f2df264fcd'
                ],
                Tags=[
                    {'Key': 'Name', 'Value': 'my-bedrock-proxy-github-oidc'},
                    {'Key': 'Environment', 'Value': 'dev'}
                ]
            )
            print("✅ OIDC Provider created successfully")
        except ClientError as e:
            if 'already exists' in str(e):
                print("✅ OIDC Provider already exists (this is fine)")
            else:
                raise
        
        # Create IAM Role Trust Policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": oidc_arn
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                        },
                        "StringLike": {
                            "token.actions.githubusercontent.com:sub": "repo:cloudaestro/GenAI-Guard:*"
                        }
                    }
                }
            ]
        }
        
        # Create IAM Role
        print("📝 Creating IAM Role...")
        role_name = "my-bedrock-proxy-github-actions-role"
        
        try:
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for GitHub Actions to deploy GenAI Guardian",
                Tags=[
                    {'Key': 'Name', 'Value': role_name},
                    {'Key': 'Environment', 'Value': 'dev'}
                ]
            )
            print("✅ IAM Role created successfully")
        except ClientError as e:
            if 'already exists' in str(e):
                print("✅ IAM Role already exists (this is fine)")
            else:
                raise
        
        # Create and attach IAM Policy
        print("🔐 Attaching IAM Policy...")
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "apprunner:*",
                        "iam:PassRole",
                        "iam:CreateRole",
                        "iam:AttachRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:DeleteRole",
                        "iam:GetRole",
                        "iam:ListAttachedRolePolicies",
                        "iam:TagRole",
                        "iam:UntagRole",
                        "iam:CreatePolicy",
                        "iam:DeletePolicy",
                        "iam:GetPolicy",
                        "iam:ListPolicyVersions",
                        "iam:PutRolePolicy",
                        "iam:GetRolePolicy",
                        "iam:DeleteRolePolicy"
                    ],
                    "Resource": "*"
                },
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
                RoleName=role_name,
                PolicyName="my-bedrock-proxy-github-actions-policy",
                PolicyDocument=json.dumps(policy_document)
            )
            print("✅ IAM Policy attached successfully")
        except ClientError as e:
            print(f"⚠️  Policy attachment issue: {e}")
            
        print()
        print("✅ Bootstrap Complete!")
        print(f"🎯 GitHub Actions Role ARN: arn:aws:iam::{account_id}:role/{role_name}")
        print()
        print("🚀 Now GitHub Actions should work! Go to:")
        print("   https://github.com/cloudaestro/GenAI-Guard/actions")
        print("   Run 'Test OIDC Connection' workflow to verify")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure you have:")
        print("1. AWS credentials configured (aws configure)")
        print("2. Sufficient IAM permissions")
        print("3. boto3 installed (pip install boto3)")
        sys.exit(1)

if __name__ == "__main__":
    main()