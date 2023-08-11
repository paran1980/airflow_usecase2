#!/usr/bin/python3
import boto3
print("hello world")

def validateFile(**kwargs):
    print("Reading the file")
    exitFlag=True
    s3= boto3.client("s3")
    obj = s3.get_object(Bucket="myawsbucket19080",Key="raw/movies.csv")
    lines=obj['Body'].read().decode("utf-8")
    for line in lines.split("\n"):
        print(line)
        if len(line.split(",")) > 4:
            exitFlag=False
            break
    return exitFlag


validateFile()
