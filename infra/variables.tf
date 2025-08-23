variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = "327152655879"
}

variable "service_name" {
  description = "Name of the service"
  type        = string
  default     = "my-bedrock-proxy"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID to use"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "datadog_api_key" {
  description = "Datadog API key"
  type        = string
  sensitive   = true
  default     = "577c60349a1fda20d9a640459cb907a3"
}

variable "datadog_app_key" {
  description = "Datadog application key"
  type        = string
  sensitive   = true
  default     = "b1f533b6575381888d732563f525462278f10caf"
}

variable "datadog_site" {
  description = "Datadog site (datadoghq.com or datadoghq.eu)"
  type        = string
  default     = "datadoghq.com"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "GenAI-Guard"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}