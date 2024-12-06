# role que será usada nos jobs
data "aws_iam_role" "glue_role" {
  name = var.role_name
}

resource "aws_glue_job" "extract_job" {
  name     = "glue-job-extract-ipea-eia366-pbrent366"
  role_arn = data.aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://s3-bucket-ipea-eia366-pbrent366/scripts/glue-job-extract-ipea-eia366-pbrent366.py"
  }

  default_arguments = var.default_arguments

  max_retries       = 0
  worker_type       = "G.1X"
  number_of_workers = 2
}

resource "aws_glue_job" "transform_job" {
  name     = "glue-job-transform-ipea-eia366-pbrent366"
  role_arn = data.aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://s3-bucket-ipea-eia366-pbrent366/scripts/glue-job-transform-ipea-eia366-pbrent366.py"
  }

  default_arguments = var.default_arguments

  max_retries       = 0
  worker_type       = "G.1X"
  number_of_workers = 2
}

resource "aws_glue_job" "load_job" {
  name     = "glue-job-load-ipea-eia366-pbrent366"
  role_arn = data.aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://s3-bucket-ipea-eia366-pbrent366/scripts/glue-job-load-ipea-eia366-pbrent366.py"
  }

  default_arguments = var.default_arguments

  max_retries       = 0
  worker_type       = "G.1X"
  number_of_workers = 2
}
