#!/usr/bin/python
import boto3
s3_bucketName="myawsbucket19080"
s3_location="hiveStep/raw/tripdata.csv"
exitFlag=True
s3= boto3.client("s3")
obj = s3.get_object(Bucket=s3_bucketName ,Key= s3_location )
lines=obj['Body'].read().decode("utf-8")
for line in lines.split("\n"):
        print(line)
        if len(line.split(",")) > 4:
            exitFlag=False
            break
#return exitFlag
if exitFlag is True:
    print(exitflag)
else:
    print("False")
