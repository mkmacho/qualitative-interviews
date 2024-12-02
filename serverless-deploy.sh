#!/bin/bash

echo "----------------------------------- IMPORTANT NOTES: --------------------------------------"
echo "This file deploy your application, requiring your OPENAI API key. You can run:"
echo "    $0 <AWS PUBLIC ACCESS KEY>"; echo
echo "Or if you prefer, modify this file directly setting the OpenAI key variable to your key."
echo "Then, run without arguments the script: "; echo "    $0    "; echo 
echo "Finally, you can modify the default values of the AWS S3 bucket and Dynamo database that"
echo "this script will generate by setting 'S3_BUCKET' and 'DYNAMO_TABLE' environment variables"
echo "e.g. running 'export S3_BUCKET=BUCKET' and then running this script."
echo "-------------------------------------------------------------------------------------------"
echo 


OPENAI_API_KEY=$1
if [ -z "$OPENAI_API_KEY" ]
then
    echo "Error: OPENAI_API_KEY cannot be empty!"; echo; exit
fi

echo; echo "Building application including local changes..."
sam build \
	--template aws_config/template.yaml \
	--use-container \
	--no-cached

BUCKET_NAME=${S3_BUCKET:-'serverless-interviews-bucket'}
TABLE_NAME=${DYNAMO_TABLE:-'INTERVIEWS'}
echo; echo "Deploying to cloud using provided OpenAI API Key, S3 bucket '$BUCKET_NAME', and Dynamo table '$TABLE_NAME'" 
sam deploy \
	--parameter-overrides OpenAIAPIKey=$OPENAI_API_KEY Port=${PORT:-8000} TableName=$TABLE_NAME \
	--no-confirm-changeset \
	--no-fail-on-empty-changeset \
	--s3-bucket $BUCKET_NAME

echo
echo "------------------------------- IMPORTANT NOTES: ------------------------------------"
echo "Take note of the API Gatekey endpoint published above. This is where to make requests."
echo "If no changes have been deployed your endpoint will remain the same. Good luck!"
echo "-------------------------------------------------------------------------------------"
echo