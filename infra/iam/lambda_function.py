import uuid
from datetime import datetime


def lambda_handler(event, context):
    training_job_name = f"training-job-{str(uuid.uuid4())[:8]}"
    dataproc = datetime.utcnow().strftime("%Y%m%d")

    return {
        "TrainingJobName": training_job_name,
        "DataProc": dataproc
    }
