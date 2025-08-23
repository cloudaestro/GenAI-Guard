# GenAI Guardian – App Runner Edition

A production-ready FastAPI service that proxies requests to Amazon Bedrock with comprehensive monitoring via Datadog. Deployed using AWS App Runner and Infrastructure as Code with Terraform.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───►│  App Runner      │───►│  Amazon Bedrock │
│                 │    │  (FastAPI)       │    │  (Claude Sonnet)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │     Datadog      │
                       │   (Metrics &     │
                       │    Traces)       │
                       └──────────────────┘
```

## ✨ Features

- **FastAPI Proxy**: High-performance async API for Bedrock model invocation
- **Monitoring**: DogStatsD metrics and ddtrace APM integration
- **Infrastructure as Code**: Complete Terraform setup for AWS App Runner
- **CI/CD**: GitHub Actions with OIDC authentication
- **Observability**: Pre-built Datadog dashboard and alerting monitors
- **Cost Tracking**: Real-time usage and cost metrics per request
- **Security**: IAM roles with least-privilege access

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.7
- Python 3.11+
- Datadog account with API/App keys

### 1. Clone and Setup

```bash
git clone <your-repo>
cd my-bedrock-proxy
pip install -r app/requirements.txt
```

### 2. Configure Infrastructure

```bash
cd infra
terraform init
terraform plan
terraform apply
```

### 3. Push to GitHub

The GitHub Actions workflow will automatically deploy on push to `main`:

```bash
git add .
git commit -m "Initial setup"
git push origin main
```

### 4. Test the Deployment

```bash
# Get the App Runner URL from Terraform outputs
export APP_URL=$(cd infra && terraform output -raw app_runner_url)

# Run smoke tests
pytest tests/test_smoke.py -v

# Or test manually
curl -X POST "$APP_URL/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "user_id": "test_user",
    "max_tokens": 100
  }'
```

## 📊 Monitoring & Observability

### Datadog Dashboard

Access your dashboard at: `https://app.datadoghq.com/dashboard/{dashboard_id}`

**Key Metrics:**
- Request rate and response times (p50, p95, p99)
- Error rates and success rates
- Token usage and cost tracking
- Top users by request volume

### Monitors & Alerts

Two critical monitors are automatically created:

1. **High Latency**: Alerts when p95 latency > 800ms for 5 minutes
2. **High Error Rate**: Alerts when error rate > 2% for 5 minutes

## 💰 Cost Estimation

**Claude 3.5 Sonnet Pricing:**
- Input tokens: $0.003 per 1M tokens
- Output tokens: $0.015 per 1M tokens

**AWS App Runner:**
- Provisioned resources: ~$0.007/hour (0.25 vCPU, 0.5 GB)
- Request charges: $0.0000025 per request

**Example monthly costs (1M requests, avg 200 tokens each):**
- Bedrock: ~$3.60
- App Runner: ~$7.60
- **Total: ~$11.20/month**

## 🔧 Configuration

### Environment Variables (App Runner)

| Variable | Description | Example |
|----------|-------------|---------|
| `BEDROCK_MODEL_ID` | Bedrock model identifier | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `DD_API_KEY` | Datadog API key | `577c60349a1fda20d9a640459cb907a3` |
| `DD_APP_KEY` | Datadog application key | `b1f533b6575381888d732563f525462278f10caf` |
| `DD_SITE` | Datadog site | `datadoghq.com` |
| `DD_ENV` | Environment name | `dev` |
| `DD_SERVICE` | Service name | `my-bedrock-proxy` |

### Terraform Variables

Update `infra/variables.tf` or use `.tfvars` file:

```hcl
aws_region         = "us-east-1"
aws_account_id     = "327152655879"
service_name       = "my-bedrock-proxy"
bedrock_model_id   = "anthropic.claude-3-5-sonnet-20241022-v2:0"
# ... other variables
```

## 🧪 Testing

### Local Development

```bash
# Start the API locally
cd app
ddtrace-run uvicorn main:app --host 0.0.0.0 --port 8080

# Run tests against local instance
APP_URL=http://localhost:8080 pytest tests/test_smoke.py -v
```

### Production Testing

```bash
# Set your deployed URL
export APP_URL=https://your-app-runner-url.us-east-1.awsapprunner.com

# Run smoke tests
pytest tests/test_smoke.py -v
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

1. **CI** (`.github/workflows/ci.yml`):
   - Python linting (black, flake8, mypy)
   - Terraform validation and formatting
   - Basic test validation

2. **Deploy** (`.github/workflows/deploy.yml`):
   - OIDC authentication with AWS
   - Terraform plan and apply
   - Smoke tests against deployed service
   - Deployment summary with URLs

### Required GitHub Secrets

The Terraform configuration handles most secrets, but you may need:

- `AWS_REGION`: us-east-1 (or your preferred region)

## 🧹 Cleanup

To destroy all resources:

```bash
cd infra
terraform destroy
```

**⚠️ Warning:** This will permanently delete your App Runner service, IAM roles, and Datadog monitors.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Run tests: `pytest tests/ -v`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **App Runner deployment fails**: Check CloudTrail for IAM permission errors
2. **High latency**: Monitor Bedrock service quotas and consider request throttling
3. **Missing metrics**: Verify Datadog API keys and DD_AGENT_HOST configuration
4. **OIDC authentication fails**: Ensure GitHub repository name matches Terraform configuration

### Support

- AWS App Runner: [AWS Documentation](https://docs.aws.amazon.com/apprunner/)
- Bedrock: [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- Datadog: [Datadog Support](https://docs.datadoghq.com/)

---

**Built with ❤️ using FastAPI, AWS App Runner, and Datadog**