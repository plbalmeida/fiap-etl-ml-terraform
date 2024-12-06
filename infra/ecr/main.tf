resource "aws_ecr_repository" "sagemaker_training_job_repository" {
  name                 = "ecr-ipea-eia366-pbrent366"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
