output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.terraform_backend_bucket.arn
}
