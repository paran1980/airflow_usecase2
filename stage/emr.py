
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
import pendulum
from airflow.models.baseoperator import cross_downstream
from airflow.providers.amazon.aws.operators.emr import EmrCreateJobFlowOperator
from airflow.providers.apache.hdfs.sensors.web_hdfs import WebHdfsSensor

def _check_flag(**context):
    if context['dag_run'].conf['flag']  == "true":
        return "F0"
    else:
        return "F1"
JOB_FLOW_OVERRIDES = {
    "Name": "Movie review classifier",
    "ReleaseLabel": "emr-5.29.0",
    "Applications": [{"Name": "Hadoop"}, {"Name": "Spark"},{"Name": "Hive"}], # We want our EMR cluster to have HDFS and Spark
    "Configurations": [
        {
            "Classification": "spark-env",
            "Configurations": [
                {
                    "Classification": "export",
                    "Properties": {"PYSPARK_PYTHON": "/usr/bin/python3"}, # by default EMR uses py2, change it to py3
                }
            ],
        }
    ],
    "Instances": {
        "InstanceGroups": [
            {
                "Name": "Master node",
                "Market": "SPOT",
                "InstanceRole": "MASTER",
                "InstanceType": "m4.xlarge",
                "InstanceCount": 1,
            },
            {
                "Name": "Core - 2",
                "Market": "SPOT", # Spot instances are a "use as available" instances
                "InstanceRole": "CORE",
                "InstanceType": "m4.xlarge",
                "InstanceCount": 2,
            },
        ],
        "KeepJobFlowAliveWhenNoSteps": True,
        "TerminationProtected": False, # this lets us programmatically terminate the cluster
        "Ec2SubnetId": "subnet-0f8738060149dc7ca"
    },
    "JobFlowRole": "EMR_EC2_DefaultRole",
    "ServiceRole": "EMR_DefaultRole",
}

@dag(
    schedule_interval="@hourly",
    start_date=pendulum.from_format("2023-07-18", "YYYY-MM-DD").in_tz("UTC"),
    catchup=False,
)
def emrPipeline():
    S0 = BashOperator(
        bash_command="sleep 10",
        task_id="S0",
    )
    
    emr = EmrCreateJobFlowOperator(
    task_id="create_emr_cluster",
    #job_flow_overrides=JOB_FLOW_OVERRIDES,
    aws_conn_id="aws_connection",
    emr_conn_id="EMR_Connection"
    )
    S0 >> emr 

dagemr=emrPipeline()
