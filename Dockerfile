FROM apache/airflow:2.6.3-python3.9
ADD requirements.txt .
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends  gcc heimdal-dev   libffi-dev \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
RUN apt-get install -y --no-install-recommends \
        freetds-bin \
        krb5-user \
        ldap-utils \
#        libffi6 \
        libsasl2-2 \
        libsasl2-modules \
        libssl1.1 \
        locales  \
        lsb-release \
        sasl2-bin \
        sqlite3 \
        unixodbc\
        gzip



RUN apt-get update && apt-get install -y zip 

        
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" 
RUN unzip  awscliv2.zip
RUN ./aws/install -i /usr/local/aws -b /usr/local/bin/aws
USER airflow
RUN pip install "apache-airflow[apache-airflow-providers-slack,apache-airflow-providers-apache-spark,apache-airflow-providers-apache-hdfs,itsdangerous,email_validator,Werkzeug,flask,pandahouse,clickhouse-driver,sqlalchemy,airflow.providers.amazon,apache-airflow-providers-common-sql]==2.6.3" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.6.3/constraints-3.9.txt"
RUN pip install apache-airflow-providers-apache-hdfs
RUN pip install hdfs[avro,dataframe,kerberos]
#RUN pip install -r requirements.txt
RUN pip uninstall -y argparse
RUN pip install awscli --upgrade
