import boto3
import os
from dotenv import load_dotenv
from rest_framework.exceptions import APIException

load_dotenv()


def generate_signed_url_from_bucket(s3_file_name):
    s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                      config=boto3.session.Config(signature_version='s3v4'),
                      region_name=os.getenv('AWS_REGION')
                      )
    try:
        url = s3.generate_presigned_url('get_object',
                                        Params={'Bucket': os.getenv('AWS_PUBLIC_S3_BUCKET_NAME'),
                                                'Key': s3_file_name},
                                        ExpiresIn=int(os.getenv('SIGNED_URL_DURATION') * 1000)
                                        )
        return url
    except Exception as e:
        print('generateSignedUrlFromS3@Error')
        print(e)
        return ""


def upload_file_to_bucket(file_path, s3_file_name):
    print(os.getenv('AWS_SECRET_ACCESS_KEY'))
    s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    try:
        s3.upload_file(
            file_path, os.getenv('AWS_PUBLIC_S3_BUCKET_NAME'), s3_file_name)
    except Exception as e:
        print('uploadFileToS3@Error')
        print(e)
        raise APIException(e)
