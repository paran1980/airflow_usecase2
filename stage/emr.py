
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
import pendulum
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import cross_downstream
from airflow.providers.amazon.aws.operators.emr import EmrCreateJobFlowOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
#from airflow.providers.amazon.aws.triggers.emr import EmrTerminateJobFlowTrigger
from airflow.providers.amazon.aws.sensors.emr import EmrStepSensor
from airflow.providers.amazon.aws.operators.emr import EmrTerminateJobFlowOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
import os
import boto3
from airflow.hooks.base import BaseHook
from pathlib import Path

def _check_flag(**context):
    if context['dag_run'].conf['flag']  == "true":
        return "F0"
    else:
        return "F1"

#SPARK_STEPS = [
#    {
#        'Name': 'hive_task',
#        'ActionOnFailure': 'CONTINUE',
#        'HadoopJarStep': { 
#            'Jar': 'command-runner.jar',              
#            'Args':['bash', '-c','hive-script --run-hive-script --args -f s3://myawsbucket19080/hiveStep/script/my_taxi_updated.hql -d INPUT=s3://myawsbucket19080/hiveStep/inputData -d OUTPUT=s3://myawsbucket19080/hiveStep/output -d valid_time_stamp=10123456 -d author_name=paran']           
#    },
#    },
#    {
#      'Name': 'aggregate_task',
#      'ActionOnFailure': 'CONTINUE',
#      'HadoopJarStep': {
#          'Jar': 'command-runner.jar',
#          'Args': ['spark-submit','s3://myawsbucket19080/scripts/taxi_aggregate.py','s3://myawsbucket19080/hiveStep/output/','s3://myawsbucket19080/hiveStep/agg_output']
#
#    },
#    }
#]



SPARK_STEPS = [
    {
        'Name': 'hive_task',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args':['bash', '-c','hive-script --run-hive-script --args -f  {{ dag_run.conf["hiveql"] }}   -d INPUT={{ dag_run.conf["input_path"] }} -d OUTPUT={{ dag_run.conf["output_path"] }} -d valid_time_stamp= {{ task_instance.xcom_pull(task_ids="copyFile", key="return_value") }} -d author_name={{ dag_run.conf["author_name"] }}']
    },
    },
    {
      'Name': 'aggregate_task',
      'ActionOnFailure': 'CONTINUE',
      'HadoopJarStep': {
          'Jar': 'command-runner.jar',
          'Args': ['spark-submit','{{ dag_run.conf["aggregate_script"] }}','{{ dag_run.conf["output_path"] }}','{{ dag_run.conf["aggregate_output"] }}']

    },
    }
]



@dag(
    schedule_interval="@hourly",
    start_date=pendulum.from_format("2023-07-18", "YYYY-MM-DD").in_tz("UTC"),
    catchup=False,
)
def emrPipeline():

    def getAwsLogin():
        conn = BaseHook.get_connection('aws_connection')
        return str(conn.login)

    def getAwsPassword():
        conn = BaseHook.get_connection('aws_connection')
        return conn.password

    def validateFile(**kwargs):
        print("Reading the file")
        exitFlag=True
        conn = BaseHook.get_connection('aws_connection')
        #print(conn)
        #print(dir(conn))
        #print(conn.EXTRA_KEY)
        #print(conn.extra)
        print(conn._extra)
        os.environ['AWS_ACCESS_KEY_ID']= conn.login
        os.environ['AWS_SECRET_ACCESS_KEY']= conn.password
        os.environ['AWS_REGION']= kwargs['region_name']
    
        s3= boto3.client("s3")
        obj = s3.get_object(Bucket=kwargs['s3_bucketName'] ,Key= kwargs['s3_location'] )
        lines=obj['Body'].read().decode("utf-8")
        for line in lines.split("\n"):
            print(line)
            if len(line.split(",")) > 4:
                exitFlag=False
                break
        return exitFlag

    bash_env ={
            "AWS_ACCESS_KEY_ID"  : getAwsLogin(),
            "AWS_SECRET_ACCESS_KEY" :  getAwsPassword()
            }

    s3_rename_file_cmd =r""" 
        . ~/.profile
        . ~/.bashrc
        export PATH=$HOME/.local/bin:$PATH
        s3_buckName=${s3_bucketName}
        s3_location=${s3_location}

        s3_file_name_without_ext=${s3_location%.*}
        s3_file_ext=${s3_location: -4}

        """ \
        + """
        export AWS_ACCESS_KEY_ID="%s"
        export AWS_SECRET_ACCESS_KEY="%s"
        timestamp={{ ts_nodash }}
        /home/airflow/.local/bin/aws  s3 mv  s3://${s3_buckName}/${s3_location}   s3://${s3_buckName}/${s3_file_name_without_ext}_${timestamp}_validated${s3_file_ext} 

    """%(bash_env.get("AWS_ACCESS_KEY_ID"),bash_env.get("AWS_SECRET_ACCESS_KEY"))

    s3_cp_file_cmd="""
    s3_buckName=${s3_bucketName}
    s3_source_dir=${s3_source_dir}
    s3_target_dir=${s3_target_dir}
    export AWS_ACCESS_KEY_ID="%s"
    export AWS_SECRET_ACCESS_KEY="%s"
    fileName=$(/home/airflow/.local/bin/aws s3 ls s3://${s3_buckName}/${s3_source_dir}/ | sed -n 2p | awk '{ print $4 }')
    timeStamp=$(echo $fileName | awk -F "_"  '{ print $2}')
    /home/airflow/.local/bin/aws s3 cp   s3://${s3_buckName}/${s3_source_dir}/$fileName   s3://${s3_buckName}/${s3_target_dir}/
    echo $timeStamp
    """%(bash_env.get("AWS_ACCESS_KEY_ID"),bash_env.get("AWS_SECRET_ACCESS_KEY"))

    S0 = BashOperator(
        bash_command="sleep 10",
        task_id="S0",
    
    )

    s3_file_check = S3KeySensor(
    task_id = "s3_file_check",
    poke_interval=10,
    timeout=300,
    soft_fail=False,
    retries =30,
    bucket_key="{{ dag_run.conf['s3_location'] }}",
    bucket_name="{{ dag_run.conf['s3_bucketName'] }}",
    aws_conn_id="aws_connection"
    )

    
    validateFile = PythonOperator(
    task_id='validate_file',
    python_callable=validateFile,
    op_kwargs={'s3_bucketName': "{{ dag_run.conf['s3_bucketName'] }}" , 's3_location': "{{ dag_run.conf['s3_location'] }}", "region_name" : "{{ dag_run.conf['region_name'] }}" },
    )

    renameFile = BashOperator(
     task_id='renameFile',
     bash_command=s3_rename_file_cmd,
     env = {"s3_bucketName" : "{{ dag_run.conf['s3_bucketName'] }}" ,
            "s3_location" : "{{ dag_run.conf['s3_location'] }}" }
     )

    copyFile = BashOperator(
        task_id="copyFile",
    bash_command=s3_cp_file_cmd,
    env= {"s3_bucketName" : "{{ dag_run.conf['s3_bucketName'] }}" ,
          "s3_source_dir": "{{ dag_run.conf['s3_source_dir'] }}",
          "s3_target_dir": "{{ dag_run.conf['s3_target_dir'] }}"}
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

    #S0 >> create_emr_cluster  >> step_adder >> [step_checker_hive_task , step_checker_agg_task ]>> cluster_remover
    S0 >> s3_file_check >> validateFile >> renameFile >> copyFile >> create_emr_cluster  >> step_adder >> [step_checker_hive_task , step_checker_agg_task ]>> cluster_remover 

dagemr=emrPipeline()
