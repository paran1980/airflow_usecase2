s3_buckName="myawsbucket19080"
s3_source_dir="raw"
s3_target_dir="validated"
export AWS_ACCESS_KEY_ID=AKIAYJC6EOICLIH36STV
export AWS_SECRET_ACCESS_KEY=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
#aws s3 mv  s3://${s3_buckName}/${s3_location}   s3://${s3_buckName}/${s3_file_name_without_ext}_${timestamp}_validated${s3_file_ext}
fileName=$( aws s3 ls s3://${s3_buckName}/${s3_source_dir}/ | sed -n 2p | awk '{ print $4 }')
timeStamp=$(echo $fileName | awk -F "_"  '{ print $2}')
echo $fileName
echo $timeStamp
aws s3 cp   s3://${s3_buckName}/${s3_source_dir}/$fileName   s3://${s3_buckName}/${s3_target_dir}/
echo {{ ti.xcom_push(key="timestamp", value=${timeStamp}) }}

