import json 
import logging 
from psycopg2 import connect, OperationalError
from psycopg2.extras import RealDictCursor 


class postgres(object):
    def __init__(self, db_url:str) :
        """ 
        Initialize the PostgreSQL database connection and table.
        Note: we are using the URL in format
            "postgresql://username:password@host:port/database"
        """
        self.db_url = db_url
        create_table_query = """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR PRIMARY KEY, data JSONB
            );
        """
        try:
            with connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_table_query)
            logging.info("PostgreSQL connection established. Should happen only once!")
        except OperationalError as e:
            logging.error(f"Database connection failed: {e}")
            raise e

    def load_remote_session(self, session_id:str) -> dict:
        """ Retrieve the interview session data from the database. """
        select_query = "SELECT data FROM sessions WHERE session_id = %s;"
        with connect(self.db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(select_query, (session_id,))
                result = cursor.fetchone()
        if not result:
            logging.warning(f"Can't load '{session_id}': not started!")
        return result['data'] if result else {}

    def delete_remote_session(self, session_id:str):
        """ Delete session data from the database. """
        delete_query = "DELETE FROM sessions WHERE session_id = %s;"
        with connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(delete_query, (session_id,))
        logging.info(f"Session '{session_id}' deleted!")

    def update_remote_session(self, session_id:str, data:dict):
        """ Update or insert session data in the database. """
        upsert_query = """
            INSERT INTO sessions (session_id, data) VALUES (%s, %s)
            ON CONFLICT (session_id) DO UPDATE SET data = EXCLUDED.data;
        """
        with connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(upsert_query, (session_id, json.dumps(data)))
        logging.info(f"Session '{session_id}' updated!")

    def retrieve_all_sessions(self) -> dict:
        raise NotImplementedError
