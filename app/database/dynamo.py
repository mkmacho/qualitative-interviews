from boto3 import resource
from botocore.exceptions import ClientError
import logging 
import json

class DynamoDB(object):
    def __init__(self, table_name:str) :
        """ 
        Initialize the Dynamo database table.
        """
        logging.info(f"Setting up DynamoDB for table '{table_name}'")
        self.table = resource('dynamodb').Table(table_name)
        logging.info("DynamoDB table connection established. Should happen only once!")

    def load_remote_session(self, session_id:str) -> dict:
        """ Retrieve the interview session data from the database. """
        result = self.table.get_item(Key={'session_id':session_id})
        data = result.get('Item', {})
        if not data:
            logging.warning(f"Can't load '{session_id}': not started!")
        logging.info(f"Loaded remote data:\n{data}") # Delete
        return data

    def delete_remote_session(self, session_id:str):
        """ Delete session data from the database. """
        self.table.delete_item(Key={"session_id":session_id})
        logging.info(f"Session '{session_id}' deleted!")

    def update_remote_session(self, session_id:str, data:dict):
        """ Update or insert session data in the database. """
        assert 'session_id' in data
        assert data['session_id'] == session_id
        self.table.put_item(Item=data)
        logging.info(f"Session '{session_id}' updated!")
