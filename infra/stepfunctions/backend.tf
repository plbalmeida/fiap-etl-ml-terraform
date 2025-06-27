terraform {
  backend "s3" {
    region         = "us-east-1"
    role_arn       = "arn:aws:iam::626957573797:role/LabRole"
    bucket         = "terraform-backend-stepfunctions-ipea-eia366-pbrent366"
    key            = "terraform.tfstate"
    dynamodb_table = "terraform-backend-lock-table-stepfunctions-ipea-eia366-pbrent366"
    encrypt        = true
  }
}
