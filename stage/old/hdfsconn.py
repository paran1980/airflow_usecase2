from airflow import DAG
from airflow import settings
from airflow.utils.dates import days_ago
from datetime import timedelta
from airflow.operators.bash import BashOperator
from airflow.models import Connection
from airflow.decorators import dag
import pendulum
from airflow.providers.apache.hdfs.sensors.web_hdfs import WebHdfsSensor
from airflow.providers.apache.hdfs.hooks.webhdfs import WebHDFSHook



dag_execute_hdfs_commands = DAG(
      dag_id ='connect_hdfs',
      schedule_interval='@once',
      start_date=days_ago(1),
      dagrun_timeout=timedelta(minutes=60),
      description='excuting hdfs commands',
     )







#Establish connection to HDFS
conn =Connection(
         conn_id = 'webhdfs',
         host='htpp://ec2-54-86-231-42.compute-1.amazonaws.com',
        conn_type='HDFS',
         login='AKIAYJC6EOICLIH36STV',
         password='rdsScy41O8kXwPgwQXzryQKHmDZ+X2U8WbUagXZw',
         port='50070',
         )
session = settings.Session()
#session.add(conn)
session.close()

webHDFS_hook = WebHDFSHook(webhdfs_conn_id="webhdfs")
client = webHDFS_hook.get_conn()
client.list("hdfs:///tmp")

if __name__ == '__main__':
    dag_execute_hdfs_commands.cli()

