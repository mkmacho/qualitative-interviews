import os

def connect_to_database():
    """ Instantiate specific backend database. """
    backend = os.getenv('BACKEND', 'DYNAMODB')
    if backend == "POSTGRES":
        from database.postgres import PostgreSQL
        return PostgreSQL(os.environ["DATABASE"])
    elif backend == "DYNAMODB":
        from database.dynamo import DynamoDB
        return DynamoDB(os.environ["DATABASE"])
    else:
        raise NotImplementedError("Requested database not supported. ")