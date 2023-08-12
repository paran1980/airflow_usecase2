
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
import pendulum
from airflow.models.baseoperator import cross_downstream
from airflow.providers.amazon.aws.operators.emr import EmrCreateJobFlowOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
#from airflow.providers.amazon.aws.triggers.emr import EmrTerminateJobFlowTrigger
from airflow.providers.amazon.aws.sensors.emr import EmrStepSensor
from airflow.providers.amazon.aws.operators.emr import EmrTerminateJobFlowOperator
from airflow.utils.trigger_rule import TriggerRule


def _check_flag(**context):
    if context['dag_run'].conf['flag']  == "true":
        return "F0"
    else:
        return "F1"

SPARK_STEPS = [
    {
        'Name': 'hive_task',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': { 
            'Jar': 'command-runner.jar',              
            'Args':['bash', '-c','hive-script --run-hive-script --args -f s3://myawsbucket19080/hiveStep/script/my_taxi_updated.hql -d INPUT=s3://myawsbucket19080/hiveStep/inputData -d OUTPUT=s3://myawsbucket19080/hiveStep/output -d valid_time_stamp=10123456 -d author_name=paran']           
    },
    },
    {
      'Name': 'aggregate_task',
      'ActionOnFailure': 'CONTINUE',
      'HadoopJarStep': {
          'Jar': 'command-runner.jar',
          'Args': ['spark-submit','s3://myawsbucket19080/scripts/taxi_aggregate.py','s3://myawsbucket19080/hiveStep/output/','s3://myawsbucket19080/hiveStep/agg_output']

    },
    }
]


JOB_FLOW_OVERRIDES = {
    "Name": "Movie review classifier",
    "ReleaseLabel": "emr-6.12.0",
    "Applications": [{"Name": "Hadoop"}, {"Name": "Spark"},{"Name": "Hive"}], # We want our EMR cluster to have HDFS and Spark
    "Configurations": [
        {
            "Classification": "spark-env",
            "Configurations": [
                {
                    "Classification": "export",
                    "Properties": {"PYSPARK_PYTHON": "/usr/bin/python3"} # by default EMR uses py2, change it to py3
                
                },
                {
                   "Classification": "spark-hive-site",
                   "Properties": {
                   "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                                }
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
        "Ec2KeyName": "emr_key_pair",
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

    create_emr_cluster = EmrCreateJobFlowOperator(
     task_id="create_emr_cluster",
     #job_flow_overrides=JOB_FLOW_OVERRIDES,
     aws_conn_id="aws_connection",
     emr_conn_id="EMR_Connection",
     wait_for_completion=True,
     waiter_max_attempts=100,
     waiter_countdown=10

     )

    step_adder =EmrAddStepsOperator(
        task_id='step_adder',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
        aws_conn_id='aws_connection',
        steps=SPARK_STEPS,
    )

    step_checker_hive_task = EmrStepSensor(
    task_id='step_checker_hive_task',
    job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
    step_id="{{ task_instance.xcom_pull(task_ids='step_adder', key='return_value')[0] }}",
    aws_conn_id='aws_connection',
    poke_interval= 10,
    timeout=200
    )

    step_checker_agg_task = EmrStepSensor(
    task_id='step_checker_agg_task',
    job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
    step_id="{{ task_instance.xcom_pull(task_ids='step_adder', key='return_value')[1] }}",
    aws_conn_id='aws_connection',
    poke_interval=10,
    timeout=200
    )

    cluster_remover = EmrTerminateJobFlowOperator(
        task_id='cluster_remover',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
        aws_conn_id='aws_connection',
        trigger_rule=TriggerRule.ALL_DONE

    )

    S0 >> create_emr_cluster  >> step_adder >> [step_checker_hive_task , step_checker_agg_task ]>> cluster_remover
    

dagemr=emrPipeline()
