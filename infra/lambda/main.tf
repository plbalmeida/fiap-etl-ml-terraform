# referência para a role IAM
data "aws_iam_role" "exec_role" {
  name = "iam-role-ipea-eia366-pbrent366"
}

resource "aws_lambda_function" "generate_training_vars" {
  function_name = "lambda-generate-training-vars"
  role          = data.aws_iam_role.exec_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  filename      = "${path.module}/lambda_function.zip"
}
