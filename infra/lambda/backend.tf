terraform {
  backend "s3" {
    region         = "us-east-1"
    role_arn       = "arn:aws:iam::626957573797:role/LabRole"
    bucket         = "terraform-backend-lambda-ipea-eia366-pbrent366"
    key            = "terraform.tfstate"
    dynamodb_table = "terraform-backend-lock-table-lambda-ipea-eia366-pbrent366"
    encrypt        = true
  }
}
