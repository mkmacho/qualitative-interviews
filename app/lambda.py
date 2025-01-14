"""
    This file is only used for deployment as an AWS Lambda function. You can delete this file if you 
    are deploying the AI interviewer application on your own dedicated server.
"""

import json
from core.logic import (
    next_question, 
    retrieve_sessions, 
    transcribe
)

def handler(event, context):
    """
    Lambda function for the AI interviewer application. This function is used to handle all incoming requests
    to the AI interviewer if hosted on AWS as a Lambda function.

    The function expects a POST request with the following structure depending on the endpoint you want to use.

    1) Generating the next question (the /next endpoint):
        {
            "route": "next",
            "payload": {
                "session_id": "session_id",
                "interview_id": "interview_id", 
                "user_message": "the_response_from_the_interviewee"
            }
        }

    2) Transcribing an audio file (the /transcribe endpoint):
        {
            "route": "transcribe",
            "payload": {
                "audio": "the audio file in base64 format"
            }
        }

    3) Retrieving all stored interviews from the DynamoDB database (the /retrieve endpoint):
        {
            "route": "retrieve",
            "payload": {}
        }

    Arguments:
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format (see above for requirements depending on the endpoint)
        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes
        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns:
    ------
    API Gateway Lambda Proxy Output Format: dict
        Specifically contains a body key with an associated dictionary of return values.
        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    response = {
        "statusCode": 200, 
        "headers": {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",            
            "Access-Control-Allow-Methods": "POST"            
        },
    }

    request = json.loads(event.get('body', '{}'))
    payload = request.get('payload', {})
    if request.get('route') == 'transcribe':
        response['body'] = json.dumps(transcribe(payload['audio']))
    elif request.get('route') == 'next':
        response['body'] = json.dumps(
            next_question(
                payload['session_id'], 
                payload['interview_id'], 
                payload.get('user_message')
            )
        )
    elif request.get('route') == 'retrieve':
        response['body'] = json.dumps(retrieve_sessions())
    else:
        raise ValueError("Invalid request. Please try again.")

    return response
