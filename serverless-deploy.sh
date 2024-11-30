#!/bin/bash


echo "Building application including local changes ..."
sam build \
	--template aws_config/template.yaml \
	--use-container \
	--no-cached


echo "Deploying to cloud with OPENAI_API_KEY=$1 ..." 
sam deploy \
	--parameter-overrides Secret=$1 \
	--no-confirm-changeset \
	--no-fail-on-empty-changeset \
	--s3-bucket serverless-interviews-bucket
