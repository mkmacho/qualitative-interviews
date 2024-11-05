import json
import logging
import os
from redis import Redis
from redis.exceptions import ConnectionError


class DatabaseManager(object):
    def __init__(self):
        self.client = Redis(
            host=os.environ["REDIS_HOST"], 
            port=os.environ["REDIS_PORT"],
            password=os.environ["REDIS_PASSWORD"]
        )
        self.test_connection()

    def test_connection(self):
        """ Test connection to backend.

        Raises:
            ConnectionError
        """
        try:
            self.client.keys()
        except ConnectionError:
            raise ConnectionError("Database connection failed. Check credentials.")
        logging.info("Redis connection established -- should happen only once!")

    def load_remote_session(self, session_id:str) -> dict:
        """ Return interview session object. """
        if self.client.exists(session_id):
            return json.loads(self.client.get(session_id))
        return {}

    def delete_remote_session(self, session_id:str):
        """ Delete data associated with current interview session. """
        self.client.delete(session_id)
        logging.info(f"Session '{session_id}' successfully deleted!")

    def update_remote_session(self, session_id:str, data:dict):
        """ Update database interview session. """
        assert isinstance(data, dict)
        self.client.set(session_id, json.dumps(data))
        assert self.client.get(session_id)
        logging.info(f"Updated session '{session_id}' data!")

