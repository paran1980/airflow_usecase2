from airflow.decorators import dag
from airflow import DAG
from airflow import settings
from airflow.utils.dates import days_ago
from datetime import timedelta
from airflow.operators.bash import BashOperator
from airflow.models import Connection
from airflow.decorators import dag
import pendulum
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator

with DAG(dag_id="emrSteps",schedule_interval="@hourly",start_date=pendulum.from_format("2023-07-18", "YYYY-MM-DD").in_tz("UTC"),catchup=False) as dag:
    S5 = BashOperator(
        bash_command="sleep 10",
        task_id="S5",
    )
    S6 = EmrAddStepsOperator(
            task_id="S6",
            aws_conn_id="aws_connection",
            job_flow_id="j-3EO35D3IB9FCU",
            steps=[
                 {
        "Name": "check the file exist in HDFS",
        "ActionOnFailure": "CANCEL_AND_WAIT",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [ "bash","-c","aws s3 cp  s3://myawsbucket19080/scripts/check_hdfs_file_exists.sh .; chmod +x check_hdfs_file_exists.sh; ./check_hdfs_file_exists.sh /data/movies.csv"]
            }
    }
    ],
    wait_for_completion=True,
    waiter_delay=10,
    waiter_max_attempts=3
    )
    S5 >> S6



