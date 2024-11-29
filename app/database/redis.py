import json
import logging
import os
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

class RedisWrapper(object):
    def __init__(self) :
        """ 
        Initialize the Redis connection using required environment variables.
        """
        self.client = Redis(
            host=os.environ["REDIS_HOST"], 
            port=os.environ["REDIS_PORT"],
            password=os.environ["REDIS_PASSWORD"]
        )
        try:
            self.client.keys()
            logging.info("Redis connection established. Should happen only once!")
        except RedisConnectionError as e:
            logging.error(f"Database connection failed: {e}")
            raise e
        logging.info("Redis connection established -- should happen only once!")

    def load_remote_session(self, session_id:str) -> dict:
        """ Retrieve the interview session data from the database. """
        if self.client.exists(session_id):
            return json.loads(self.client.get(session_id))
        logging.warning(f"Can't load session '{session_id}': not started!")
        return {}

    def delete_remote_session(self, session_id:str):
        """ Delete session data from the database. """
        self.client.delete(session_id)
        logging.info(f"Session '{session_id}' deleted!")

    def update_remote_session(self, session_id:str, data:dict):
        """ Update or insert session data in the database. """
        assert isinstance(data, dict)
        self.client.set(session_id, json.dumps(data))
        assert self.client.get(session_id)
        logging.info(f"Session '{session_id}' updated!")

    def retrieve_all_sessions(self) -> list:
        raise NotImplementedError

