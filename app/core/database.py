import json
import logging
import os
from redis import Redis, ConnectionPool
from redis.exceptions import ConnectionError


class DatabaseManager(object):
    def __init__(self):
        pool = ConnectionPool(
            host=os.environ["REDIS_HOST"], 
            port=os.environ["REDIS_PORT"],
            password=os.environ["REDIS_PASSWORD"]
        )
        try:
            self.client = Redis(connection_pool=pool)
            logging.info(f"Have open sessions: {self.client.keys()}")
        except ConnectionError as e:
            logging.error(f"RedisConnectionError: {str(e)}")
            raise ConnectionError("Database connection failed. Check credentials.")
        logging.info(f"Redis connection established. Should happen only once!")

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

