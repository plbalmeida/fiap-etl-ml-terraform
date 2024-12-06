resource "aws_s3_bucket" "bucket" {
  bucket = "s3-bucket-ipea-eia366-pbrent366"
}

resource "aws_s3_object" "raw_path" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "raw/"
}

resource "aws_s3_object" "interim_path" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "interim/"
}

resource "aws_s3_object" "final_path" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "final/"
}

resource "aws_s3_object" "query_results_path" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "query-results/"
}

resource "aws_s3_object" "scripts_path" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "scripts/"
}

resource "aws_s3_object" "predictions_path" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "predictions/"
}
