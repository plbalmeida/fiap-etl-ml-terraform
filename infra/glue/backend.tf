terraform {
  backend "s3" {
    region         = "us-east-1"
    role_arn       = "arn:aws:iam::413467296690:role/glue-ipea-eia366-pbrent366-terraform-backend-role"
    bucket         = "terraform-backend-glue-ipea-eia366-pbrent366"
    key            = "terraform.tfstate"
    dynamodb_table = "terraform-backend-lock-table-glue-ipea-eia366-pbrent366"
    encrypt        = true
  }
}
