#!/bin/bash

echo "----------------------------------- IMPORTANT NOTES: --------------------------------------"
echo "This file deploys your application. You should run:"
echo "    $0 <S3_BUCKET>"; 
echo
echo "Or if you prefer, export BUCKET_NAME as an environment variables or even modify this file "
echo "directly with chosen bucket name from serverless-setup. "
echo "-------------------------------------------------------------------------------------------"
echo 

OPENAI_API_KEY=${1:-${OPENAI_API_KEY}}
BUCKET_NAME=${2:-${S3_BUCKET}}
TABLE_NAME=${DYNAMO_TABLE:-'interview-sessions'}

if [ -z "$BUCKET_NAME" ]
then
    echo "Error: S3_BUCKET cannot be empty and must match that used during setup!"; echo; exit
fi

echo; echo "Building application including local changes..."
sam build \
	--use-container \
	--no-cached


echo; echo "Deploying to cloud using provided S3 bucket and Dynamo table..." 
sam deploy \
	--parameter-overrides TableName=$TABLE_NAME \
	--no-confirm-changeset \
	--no-fail-on-empty-changeset \
	--s3-bucket $BUCKET_NAME

echo
echo "------------------------------- IMPORTANT NOTES: ------------------------------------"
echo "Take note of the API Gatekey endpoint published above. This is where to make requests."
echo "If no changes have been deployed your endpoint will remain the same. Good luck!"
echo "-------------------------------------------------------------------------------------"
echo