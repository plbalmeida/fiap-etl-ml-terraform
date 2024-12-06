output "dynamodb_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}
