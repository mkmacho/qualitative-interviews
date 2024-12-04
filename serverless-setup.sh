#!/bin/bash

echo "----------------------------------- IMPORTANT NOTES: --------------------------------------"
echo "This file configures AWS in order to build and deploy your application. You should run:"
echo "    $0 <AWS PUBLIC ACCESS KEY> <AWS SECRET ACCESS KEY> <AWS REGION>"; 
echo
echo "Or if you prefer, modify this file directly setting the key variables to the AWS access "
echo "keys you generated. Then, run without arguments the script: "; echo "    $0    "; 
echo 
echo "Finally, you can modify the default values of the AWS S3 bucket and Dynamo database that"
echo "this script will generate by setting 'S3_BUCKET' and 'DYNAMO_TABLE' environment variables"
echo "e.g. running 'export S3_BUCKET=BUCKET' and then running this script."
echo "-------------------------------------------------------------------------------------------"
echo 

AWS_PUBLIC_ACCESS_KEY=$1
AWS_SECRET_ACCESS_KEY=$2
AWS_REGION=${3-'eu-north-1'}

if [ -z "$AWS_PUBLIC_ACCESS_KEY" ]
then
    echo "Error: AWS_PUBLIC_ACCESS_KEY cannot be empty!"; echo; exit
fi
if [ -z "$AWS_SECRET_ACCESS_KEY" ]
then
    echo "Error: AWS_SECRET_ACCESS_KEY cannot be empty!"; echo; exit
fi

# Configure AWS credentials
echo; echo "Configuring AWS access for '$AWS_REGION'"; echo 
aws configure set aws_access_key_id $AWS_PUBLIC_ACCESS_KEY 
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set default.region $AWS_REGION


# Create AWS S3 bucket where build template will be stored
BUCKET_NAME=${S3_BUCKET:-'serverless-interviews-bucket-'$(date +"%Y%m%d")}
echo "Creating S3 bucket '$BUCKET_NAME' where templates will be stored"
aws s3api create-bucket \
	--bucket $BUCKET_NAME \
	--region $AWS_REGION \
	--create-bucket-configuration LocationConstraint=$AWS_REGION

# Get rid of old templates after 24hours
aws s3api put-bucket-lifecycle-configuration \
	--bucket $BUCKET_NAME  \
	--lifecycle-configuration '{
	    "Rules": [
	        {
	            "Filter": {},
	            "Status": "Enabled",
	            "Expiration": {
	                "Days": 1
	            },
	            "ID": "QuickExpiration"
	        }
	    ]
	}'

# Create AWS DynamoDB table to store interviews
TABLE_NAME=${DYNAMO_TABLE:-'INTERVIEWS'}
echo; echo "Creating DynamoDB table '$TABLE_NAME' to store interview sessions"
aws dynamodb create-table \
	--table-name $TABLE_NAME \
	--attribute-definitions AttributeName=session_id,AttributeType=S \
	--key-schema AttributeName=session_id,KeyType=HASH \
	--billing-mode PAY_PER_REQUEST \
	--region $AWS_REGION

echo
echo "----------------------------------- IMPORTANT NOTES: --------------------------------------"
echo "This file needs to be run just once as all future changes will be reflected in re-deployment."
echo "And if you haved changed the 'TABLE_NAME' variable here, ensure that the same table is "
echo "referred to during deployment."; echo
echo "You are now ready to deploy your app running './serverless-deploy.sh <YOUR_OPENAI_API_KEY>'"
echo "-------------------------------------------------------------------------------------------"
echo