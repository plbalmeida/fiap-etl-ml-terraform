resource "aws_s3_bucket" "terraform_backend_bucket" {
  bucket = "terraform-backend-${var.component_name}"
}

resource "aws_s3_bucket_versioning" "terraform_backend_versioning" {
  bucket = aws_s3_bucket.terraform_backend_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_backend_encryption" {
  bucket = aws_s3_bucket.terraform_backend_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
