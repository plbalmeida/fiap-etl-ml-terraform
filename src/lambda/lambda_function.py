from datetime import datetime


def lambda_handler(event, context):
    training_job_name = f"sagemaker-training-job-ipea-eia366-pbrent366-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    dataproc = datetime.utcnow().strftime("%Y%m%d")

    return {
        "TrainingJobName": training_job_name,
        "DataProc": dataproc
    }
