 
        . ~/.profile
        . ~/.bashrc
        export PATH=$HOME/.local/bin:$PATH
        s3_buckName=${s3_bucketName}
        s3_location=${s3_location}

        s3_file_name_without_ext=${s3_location%.*}
        s3_file_ext=${s3_location: -4}

        
        export AWS_ACCESS_KEY_ID="AKIAYJC6EOICLQ475Y7D"
        export AWS_SECRET_ACCESS_KEY="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"
        timestamp={{ ts_nodash }}
        aws  s3 mv  s3://${s3_buckName}/${s3_location}   s3://${s3_buckName}/${s3_file_name_without_ext}_${timestamp}_validated${s3_file_ext} 

    