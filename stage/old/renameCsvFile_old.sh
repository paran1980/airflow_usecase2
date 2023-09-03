s3_buckName="myawsbucket19080"
s3_location="raw/movies.csv"
s3_file_name_without_ext=${s3_location%.*}
s3_file_ext=${s3_location: -4}
export AWS_ACCESS_KEY_ID=AKIAYJC6EOICLIH36STV
export AWS_SECRET_ACCESS_KEY=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
timestamp={{ ts_nodash }}
#timestamp="02092023120101"
aws s3 mv  s3://${s3_buckName}/${s3_location}   s3://${s3_buckName}/${s3_file_name_without_ext}_${timestamp}_validated${s3_file_ext}
