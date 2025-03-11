# variable "role_name" {
#   default = "iam-role-ipea-eia366-pbrent366"
# }

variable "role_name" {
  default = "LabRole"
}

variable "script_location" {
  default = "s3://s3-bucket-ipea-eia366-pbrent366/scripts/"
}

variable "default_arguments" {
  type = map(string)
  default = {
    "--job-bookmark-option"       = "job-bookmark-disable"
    "--enable-glue-datacatalog"   = "true"
    "--additional-python-modules" = "ipeadatapy"
  }
}
