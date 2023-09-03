
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
import pendulum
from airflow.models.baseoperator import cross_downstream


def _check_flag(**context):
    if context['dag_run'].conf['flag']  == "true":
        return "F0"
    else:
        return "F1"

@dag(
    schedule_interval="@hourly",
    start_date=pendulum.from_format("2023-07-18", "YYYY-MM-DD").in_tz("UTC"),
    catchup=False,
)
def pipeline():
    S0 = BashOperator(
        bash_command="sleep 10",
        task_id="S0",
    )
    S0
dagobj=pipeline()
