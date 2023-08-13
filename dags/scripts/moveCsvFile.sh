s3_buckName=${s3_bucketName}
s3_source_dir=${s3_source_dir}
s3_target_dir=${s3_target_dir}
export AWS_ACCESS_KEY_ID=${access_key_id}
export AWS_SECRET_ACCESS_KEY=${aws_secret_access_key}
fileName=$( aws s3 ls s3://${s3_buckName}/${s3_source_dir}/ | sed -n 2p | awk '{ print $4 }')
timeStamp=$(echo $fileName | awk -F "_"  '{ print $2}')
aws s3 cp   s3://${s3_buckName}/${s3_source_dir}/$fileName   s3://${s3_buckName}/${s3_target_dir}/
echo $timeStamp

