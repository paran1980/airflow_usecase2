from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
import pendulum
from airflow.models.baseoperator import cross_downstream


def _check_flag(**context):
    if 'flag' in context['dag_run'].conf and context['dag_run'].conf['flag']  == "true":
        return "F0"
    else:
        return "F1"

@dag(
    schedule="0 * * * *",
    start_date=pendulum.from_format("2023-07-18", "YYYY-MM-DD").in_tz("UTC"),
    catchup=False,
)
def serial_parallel_data_pipeline():
    S0 = BashOperator(
        bash_command="sleep 10",
        task_id="S0",
    )

    S1 = BashOperator(
        bash_command="sleep 10",
        task_id="S1",
    )

    P0 = BashOperator(
        bash_command="sleep 5",
        task_id="P0",
    )

    P1 = BashOperator(
        bash_command="sleep 15",
        task_id="P1",
    )

    P2 = BashOperator(
        bash_command="exit 1",
        task_id="P2",
    )

    P3 = BashOperator(
        bash_command="sleep 15",
        task_id="P3",
    )

    S2 = BashOperator(
        bash_command="sleep 10",
        task_id="S2",
    )

    B0 = BranchPythonOperator(
        python_callable=_check_flag,
        task_id="B0",
    )

    F0 = BashOperator(
        bash_command="echo 'hello'",
        task_id="F0",
    )

    F1 = BashOperator(
        bash_command="echo 'Bye'",
        task_id="F1",
    )

    S3 = BashOperator(
        bash_command="sleep 10",
        task_id="S3",
        trigger_rule='all_done'
    )

    B0 << S2

    F0 << B0

    F1 << B0

    P0 << S1

    P1 << S1

    P2 << S1

    P3 << S1

    S1 << S0

    S2 << [P0, P1, P2, P3]

    S3 << [F0, F1]

dag_obj = serial_parallel_data_pipeline()

