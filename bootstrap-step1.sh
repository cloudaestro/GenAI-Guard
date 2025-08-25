#!/bin/bash
set -e

echo "🚀 GenAI Guardian Bootstrap - Step 1"
echo "Creating GitHub OIDC Provider and IAM Role"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI is configured"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $ACCOUNT_ID"

# Create GitHub OIDC Provider
echo "🔧 Creating GitHub OIDC Provider..."
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 1c58a3a8518e8759bf075b76b750d4f2df264fcd \
    --tags Key=Name,Value=my-bedrock-proxy-github-oidc Key=Environment,Value=dev \
    || echo "OIDC Provider already exists (this is fine)"

# Create IAM Role Trust Policy
echo "📝 Creating IAM Role..."
cat > /tmp/github-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
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
EOF

# Create the IAM Role
aws iam create-role \
    --role-name my-bedrock-proxy-github-actions-role \
    --assume-role-policy-document file:///tmp/github-trust-policy.json \
    --description "Role for GitHub Actions to deploy GenAI Guardian" \
    --tags Key=Name,Value=my-bedrock-proxy-github-actions-role Key=Environment,Value=dev \
    || echo "IAM Role already exists (this is fine)"

# Create IAM Policy for the role
cat > /tmp/github-actions-policy.json << EOF
{
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
        "iam:ListPolicyVersions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach policy to role
aws iam put-role-policy \
    --role-name my-bedrock-proxy-github-actions-role \
    --policy-name my-bedrock-proxy-github-actions-policy \
    --policy-document file:///tmp/github-actions-policy.json

# Clean up temp files
rm -f /tmp/github-trust-policy.json /tmp/github-actions-policy.json

echo ""
echo "✅ Bootstrap Step 1 Complete!"
echo "🎯 GitHub Actions Role ARN: arn:aws:iam::$ACCOUNT_ID:role/my-bedrock-proxy-github-actions-role"
echo ""
echo "🚀 Now GitHub Actions should work! Push a commit to test deployment."