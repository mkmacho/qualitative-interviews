#!/bin/bash

# Create AWS S3 bucket where build template will be stored
aws s3api create-bucket \
	--bucket serverless-interviews-bucket \
	--region eu-north-1 \
	--create-bucket-configuration LocationConstraint=eu-north-1

# Get rid of old templates after 24hours
aws s3api put-bucket-lifecycle-configuration \
	--bucket serverless-interviews-bucket  \
	--lifecycle-configuration file://lifecycle.json

# Create AWS DynamoDB table to store interviews
aws dynamodb create-table \
	--table-name INTERVIEWS \
	--attribute-definitions AttributeName=session_id,AttributeType=S \
	--key-schema AttributeName=session_id,KeyType=HASH \
	--billing-mode PAY_PER_REQUEST \
	--region eu-north-1