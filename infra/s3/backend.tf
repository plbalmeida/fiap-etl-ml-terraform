terraform {
  backend "s3" {
    region         = "us-east-1"
    bucket         = "terraform-backend-s3-ipea-eia366-pbrent366"
    key            = "terraform.tfstate"
    dynamodb_table = "terraform-backend-lock-table-s3-ipea-eia366-pbrent366"
    encrypt        = true
  }
}
