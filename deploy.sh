#!/bin/bash


echo "Building application including local changes ..."
sam build \
	--use-container \
	--no-cached


echo "Deploying to cloud with OPENAI_API_KEY=$1 ..." 
sam deploy \
	--parameter-overrides Secret=$1 \
	--no-confirm-changeset \
	--no-fail-on-empty-changeset \
	--s3-bucket serverless-interviews-bucket

echo "Succesfully deployed. Save API Gateway endpoint URL above!"