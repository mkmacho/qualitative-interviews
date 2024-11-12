import json 
import logging 
import os
import psycopg2
from psycopg2.extras import RealDictCursor 
from contextlib import contextmanager

class DatabaseManager (object):
    def __init__(self, db_url=None) :
        """ Initialize the PostgreSQL database connection.
        Args:
            db_url (str): Database URL in the format
                postgresql://username:password@host:port/database
                If None, reads from environment variables.
        """
        self.db_url = db_url or os.environ.get("DATABASE_URL" )
        self.test_connection()


    @contextmanager
    def get_connection(self):
        """ Context manager for database connection and cursor. """
        conn = psycopg2.connect(self.db_url)
        conn.autocommit = True # Ensure each command is committed automatically
        try:
            yield conn 
        finally:
            conn.close()

    def test_connection(self):
        """ Test connection to the database. """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
            logging.info("PostgreSQL connection established -- should happen only once!")
        except psycopg2.OperationalError as e:
            logging.error(f"Database connection failed: {e}")
            raise


    def setup_database(self):
        """ Set up the sessions table if it doesn't already exist. """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR PRIMARY KEY,
            data JSONB
        );
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_query)

    def load_remote_session(self, session_id: str) -> dict:
        """ Retrieve the session data from the database. """
        select_query = "SELECT data FROM sessions WHERE session_id = %s;"
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(select_query, (session_id,))
            result = cursor.fetchone()
            if result:
                return result['data']  # JSON data is directly returned
        return {}

    def delete_remote_session(self, session_id: str):
        """ Delete session data from the database. """
        delete_query = "DELETE FROM sessions WHERE session_id = %s;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(delete_query, (session_id,))
        logging.info(f"Session '{session_id}' successfully deleted!")

    def update_remote_session(self, session_id: str, data: dict):
        """ Update or insert session data in the database. """
        upsert_query = """
        INSERT INTO sessions (session_id, data) VALUES (%s, %s)
        ON CONFLICT (session_id) DO UPDATE SET data = EXCLUDED.data;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(upsert_query, (session_id, json.dumps(data)))
        logging.info(f"Updated session '{session_id}' data!")
