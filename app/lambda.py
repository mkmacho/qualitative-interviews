import json
from core.logic import next_question

def handler(event, context):
    """
    Lambda function for `/next` endpoint.

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict
        Specifically contains a body key with an associated dictionary of return values.
        
        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    assert isinstance(event['body'], str), "Malformed request body. Try again!"
    return {
        "statusCode": 200, 
        "body": json.dumps(next_question(**json.loads(event['body'])))
    }