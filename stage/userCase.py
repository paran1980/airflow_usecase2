from airflow.decorators import dag
from airflow import DAG
from airflow import settings
from airflow.utils.dates import days_ago
from datetime import timedelta
from airflow.operators.bash import BashOperator
from airflow.models import Connection
from airflow.decorators import dag
import pendulum
import boto3
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
import os

with DAG(dag_id="userCase2",schedule_interval="@hourly",start_date=pendulum.from_format("2023-07-18", "YYYY-MM-DD").in_tz("UTC"),catchup=False) as dag:

    bashOp = BashOperator(
        bash_command="sleep 10",
        task_id="S5",
    )

    s3_buckName="myawsbucket19080"
    s3_location="raw/movies.csv"

    def validateFile(**kwargs):
        print("Reading the file")
        exitFlag=True
        os.environ['AWS_ACCESS_KEY_ID']="xxxxxxxxxxxxxxx"
        os.environ['AWS_SECRET_ACCESS_KEY']="XXXXXXXXXXXXXXX"
        os.environ['AWS_DEFAULT_REGION']="us-east-1"
        s3= boto3.client("s3")
        obj = s3.get_object(Bucket="myawsbucket19080",Key="raw/movies.csv")
        lines=obj['Body'].read().decode("utf-8")
        for line in lines.split("\n"):
            print(line)
            if len(line.split(",")) > 4:
                exitFlag=False
                break
        return exitFlag

    fileCheck = S3KeySensor(
    task_id = "s3_file_check",
	poke_interval=10,
	timeout=30,
	soft_fail=False,
    retries = 2,
	bucket_key=s3_location,
	bucket_name=s3_buckName,
    aws_conn_id="aws_connection"
    )

    validateFile = PythonOperator(
    task_id='validate_file',
    python_callable=validateFile,
    )

    renameFile = BashOperator(
            task_id='renameFile',
            bash_command='scripts/renameCsvFile.sh'
            )
    moveFile = BashOperator(
            task_id="moveFile",
            bash_command='scripts/moveCsvFile.sh'
            )

    



    bashOp >> fileCheck >> validateFile >> renameFile >> moveFile

