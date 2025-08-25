provider "aws" {
  region = var.aws_region
}

provider "datadog" {
  api_key = var.datadog_api_key
  app_key = var.datadog_app_key
  api_url = "https://api.${var.datadog_site}"
}

## GitHub OIDC and GitHub Actions role are bootstrapped outside Terraform
## (via .github/workflows/bootstrap.yml) to avoid drift/duplication.

# IAM Role for App Runner
resource "aws_iam_role" "app_runner_instance_role" {
  name = "${var.service_name}-app-runner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.service_name}-app-runner-instance-role"
    Environment = var.environment
  }
}

# IAM Policy for App Runner to access Bedrock
resource "aws_iam_role_policy" "app_runner_bedrock_policy" {
  name = "${var.service_name}-bedrock-policy"
  role = aws_iam_role.app_runner_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# App Runner Service
resource "aws_apprunner_service" "main" {
  service_name = var.service_name

  source_configuration {
    # Private ECR image pushed by CI
    image_repository {
      image_configuration {
        port = "8080"
        runtime_environment_variables = {
          BEDROCK_MODEL_ID   = var.bedrock_model_id
          DD_API_KEY         = var.datadog_api_key
          DD_APP_KEY         = var.datadog_app_key
          DD_SITE            = var.datadog_site
          DD_ENV             = var.environment
          DD_SERVICE         = var.service_name
          AWS_DEFAULT_REGION = var.aws_region
        }
        start_command = "ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port 8080"
      }
      image_identifier      = var.container_image
      image_repository_type = "ECR"
    }

    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu               = "0.25 vCPU"
    memory            = "0.5 GB"
    instance_role_arn = aws_iam_role.app_runner_instance_role.arn
  }

  health_check_configuration {
    healthy_threshold   = 1
    interval            = 10
    path                = "/health"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 5
  }

  tags = {
    Name        = var.service_name
    Environment = var.environment
  }
}

# IAM role for App Runner to pull from private ECR
resource "aws_iam_role" "apprunner_ecr_access" {
  name = "${var.service_name}-app-runner-ecr-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.service_name}-app-runner-ecr-access"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access_attachment" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# Datadog Dashboard
resource "datadog_dashboard" "main" {
  title       = "GenAI Guardian - ${var.service_name}"
  description = "Monitoring dashboard for Bedrock proxy service"
  layout_type = "ordered"

  widget {
    timeseries_definition {
      title = "Request Rate"
      request {
        q            = "sum:bedrock.requests.total{service:${var.service_name}}.as_rate()"
        display_type = "line"
      }
    }
  }

  widget {
    timeseries_definition {
      title = "P95 Latency"
      request {
        q            = "p95:bedrock.latency_ms{service:${var.service_name}}"
        display_type = "line"
      }
    }
  }

  widget {
    timeseries_definition {
      title = "Error Rate"
      request {
        q            = "sum:bedrock.requests.errors{service:${var.service_name}}.as_rate()"
        display_type = "line"
      }
    }
  }

  widget {
    timeseries_definition {
      title = "Token Usage"
      request {
        q            = "sum:bedrock.tokens_used{service:${var.service_name}}"
        display_type = "line"
      }
    }
  }

  widget {
    timeseries_definition {
      title = "Cost (USD)"
      request {
        q            = "sum:bedrock.cost_usd{service:${var.service_name}}"
        display_type = "line"
      }
    }
  }
}

# Datadog Monitor - High Latency
resource "datadog_monitor" "high_latency" {
  name    = "[${var.service_name}] High P95 Latency"
  type    = "metric alert"
  message = "P95 latency is above 800ms for ${var.service_name}. @slack-alerts"

  query = "avg(last_5m):p95:bedrock.latency_ms{service:${var.service_name}} > 800"

  monitor_thresholds {
    critical = 800
    warning  = 600
  }

  notify_audit = false
  timeout_h    = 0
  include_tags = true

  tags = ["service:${var.service_name}", "environment:${var.environment}"]
}

# Datadog Monitor - High Error Rate
resource "datadog_monitor" "high_error_rate" {
  name    = "[${var.service_name}] High Error Rate"
  type    = "metric alert"
  message = "Error rate is above 2% for ${var.service_name}. @slack-alerts"

  query = "avg(last_5m):sum:bedrock.requests.errors{service:${var.service_name}}.as_rate() / sum:bedrock.requests.total{service:${var.service_name}}.as_rate() * 100 > 2"

  monitor_thresholds {
    critical = 2
    warning  = 1
  }

  notify_audit = false
  timeout_h    = 0
  include_tags = true

  tags = ["service:${var.service_name}", "environment:${var.environment}"]
}
