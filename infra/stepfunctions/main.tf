# referência para a role IAM
data "aws_iam_role" "exec_role" {
  name = "iam-role-ipea-eia366-pbrent366"
}

resource "aws_sfn_state_machine" "state_machine" {
  name     = "state-machine-ipea-eia366-pbrent366"
  role_arn = data.aws_iam_role.exec_role.arn

  definition = jsonencode({
    "Comment" : "Orquestração dos jobs de ETL e treinamento usando Step Functions",
    "StartAt" : "glue-job-extract-ipea-eia366-pbrent366",
    "States" : {
      "glue-job-extract-ipea-eia366-pbrent366" : {
        "Type" : "Task",
        "Resource" : "arn:aws:states:::glue:startJobRun.sync",
        "Parameters" : {
          "JobName" : "glue-job-extract-ipea-eia366-pbrent366"
        },
        "Catch" : [{
          "ErrorEquals" : ["States.ALL"],
          "Next" : "fail-state"
        }],
        "Next" : "glue-job-transform-ipea-eia366-pbrent366"
      },
      "glue-job-transform-ipea-eia366-pbrent366" : {
        "Type" : "Task",
        "Resource" : "arn:aws:states:::glue:startJobRun.sync",
        "Parameters" : {
          "JobName" : "glue-job-transform-ipea-eia366-pbrent366"
        },
        "Catch" : [{
          "ErrorEquals" : ["States.ALL"],
          "Next" : "fail-state"
        }],
        "Next" : "glue-job-load-ipea-eia366-pbrent366"
      },
      "glue-job-load-ipea-eia366-pbrent366" : {
        "Type" : "Task",
        "Resource" : "arn:aws:states:::glue:startJobRun.sync",
        "Parameters" : {
          "JobName" : "glue-job-load-ipea-eia366-pbrent366"
        },
        "Catch" : [{
          "ErrorEquals" : ["States.ALL"],
          "Next" : "fail-state"
        }],
        "Next" : "lambda-generate-training-vars"
      },
      "lambda-generate-training-vars" : {
        "Type" : "Task",
        "Resource" : "arn:aws:lambda:us-east-1:413467296690:function:lambda-generate-training-vars",
        "ResultPath" : "$.TrainingVars",
        "Catch" : [{
          "ErrorEquals" : ["States.ALL"],
          "Next" : "fail-state"
        }],
        "Next" : "sagemaker-training-job-ipea-eia366-pbrent366"
      },
      "sagemaker-training-job-ipea-eia366-pbrent366" : {
        "Type" : "Task",
        "Resource" : "arn:aws:states:::sagemaker:createTrainingJob.sync",
        "Parameters" : {
          "TrainingJobName.$" : "$.TrainingVars.TrainingJobName",
          "ResourceConfig" : {
            "InstanceCount" : 1,
            "InstanceType" : "ml.m5.large",
            "VolumeSizeInGB" : 50
          },
          "AlgorithmSpecification" : {
            "TrainingImage" : "413467296690.dkr.ecr.us-east-1.amazonaws.com/ecr-ipea-eia366-pbrent366:latest",
            "TrainingInputMode" : "File"
          },
          "OutputDataConfig" : {
            "S3OutputPath" : "s3://s3-bucket-ipea-eia366-pbrent366/predictions"
          },
          "StoppingCondition" : {
            "MaxRuntimeInSeconds" : 86400,
            "MaxWaitTimeInSeconds" : 86400
          },
          "RoleArn" : "arn:aws:iam::413467296690:role/iam-role-ipea-eia366-pbrent366",
          "InputDataConfig" : [
            {
              "ChannelName" : "training",
              "ContentType" : "application/x-parquet",
              "DataSource" : {
                "S3DataSource" : {
                  "S3DataType" : "S3Prefix",
                  "S3Uri.$" : "States.Format('s3://s3-bucket-ipea-eia366-pbrent366/final/dataproc={}', $.TrainingVars.DataProc)",
                  "S3DataDistributionType" : "ShardedByS3Key"
                }
              }
            }
          ],
          "EnableManagedSpotTraining" : true
        },
        "Catch" : [
          {
            "ErrorEquals" : [
              "States.ALL"
            ],
            "Next" : "fail-state"
          }
        ],
        "End" : true
      },
      "fail-state" : {
        "Type" : "Fail",
        "Error" : "JobFailed",
        "Cause" : "A execução do job falhou."
      }
    }
  })
}
