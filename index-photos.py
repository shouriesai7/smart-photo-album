import json
import os
import time
import logging
import boto3
import requests
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

headers = { "Content-Type": "application/json" }
host = 'search-photos-twu34m6xdkbq5z3ua6ss4ujtye.us-west-2.es.amazonaws.com'
#testing
#Setting values to be referenced later in the program
port = 443
ssl = True
certs = True
service = "es"
region = 'us-west-2'
username = "master_user"
password = "Suits1998*"

#Getting Boto3 credentials creating client
credentials = boto3.Session().get_credentials()
rekognition = boto3.client('rekognition')

os = OpenSearch(
        hosts=[{'host': host,'port': port}], 
        http_auth=(username, password), 
        use_ssl = ssl, 
        verify_certs=certs, 
        connection_class=RequestsHttpConnection
    )


def lambda_handler(event, context):
    logger.debug(credentials)
    records = event['Records']

    for record in records:
        s3object = record['s3']
        bucket = s3object['bucket']['name']
        objectKey = s3object['object']['key']

        image = {
            'S3Object' : {
                'Bucket' : bucket,
                'Name' : objectKey
            }
        }
        
        s3Client=boto3.client('s3')
        metadata = s3Client.head_object(Bucket=bucket, Key=objectKey)
        custom_labels = metadata['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'].split(',')
        response = rekognition.detect_labels(Image = image)
        labels = list(map(lambda x : x['Name'], response['Labels']))
        for label in custom_labels:
                labels.append(label.strip().title())
        print(labels)
        #timestamp = datetime.now().strftime('%Y-%d-%mT%H:%M:%S')
        timestamp=str(int(time.time()))
        print("new time:", int(time.time()))
        esObject = json.dumps({
            'objectKey' : objectKey,
            'bucket' : bucket,
            'createdTimeStamp' : timestamp,
            'labels' : labels
        })
        os.index(index = "photo_index", id = objectKey, body = esObject, refresh = True)


    return {
        'statusCode': 200,
        'body': json.dumps('Indexing successfully done!')
    }
