output "app_runner_url" {
  description = "App Runner service URL"
  value       = "https://${aws_apprunner_service.main.service_url}"
}

output "dashboard_url" {
  description = "Datadog dashboard URL"
  value       = "https://app.${var.datadog_site}/dashboard/${datadog_dashboard.main.id}"
}

output "app_runner_service_arn" {
  description = "ARN of the App Runner service"
  value       = aws_apprunner_service.main.arn
}

output "high_latency_monitor_id" {
  description = "ID of the high latency monitor"
  value       = datadog_monitor.high_latency.id
}

output "high_error_rate_monitor_id" {
  description = "ID of the high error rate monitor"
  value       = datadog_monitor.high_error_rate.id
}
