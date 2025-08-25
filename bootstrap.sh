#!/bin/bash
set -e

echo "🚀 GenAI Guardian Bootstrap Script"
echo "This script sets up the initial AWS infrastructure needed for GitHub Actions"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI is configured"

# Check if Terraform is available
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform first."
    exit 1
fi

echo "✅ Terraform is available"

# Navigate to infrastructure directory
cd infra

echo "🔧 Initializing Terraform..."
terraform init

echo "🔍 Planning Terraform deployment..."
terraform plan -out=bootstrap.tfplan

echo "🚀 Applying Terraform (this will create AWS resources)..."
terraform apply -auto-approve bootstrap.tfplan

echo "📋 Getting outputs..."
echo ""
echo "🎉 Bootstrap complete! Here are your resources:"
echo "• App Runner URL: $(terraform output -raw app_runner_url)"
echo "• GitHub Actions Role: $(terraform output -raw github_actions_role_arn)"
echo "• Dashboard URL: $(terraform output -raw dashboard_url)"
echo ""
echo "✅ GitHub Actions should now work successfully!"
echo "Push any commit to main branch to trigger deployment."