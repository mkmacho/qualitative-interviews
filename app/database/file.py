import logging
import os
import json


class FileWriter(object):
    def __init__(self, filedir:str='data') :
        self.filedir = filedir
        if not os.path.isdir(filedir): os.makedirs(filedir)
        logging.info(f"Will write interviews to '{filedir}'.")

    def load_remote_session(self, session_id:str) -> dict:
        """ Retrieve the interview session data from file. """
        filepath = os.path.join(self.filedir, f"{session_id}.json")
        if not os.path.isfile(filepath):
            logging.warning(f"Can't load session '{session_id}': not started!")
            return {}
        with open(filepath, 'r') as f:
            session = json.load(f) 
        for k, v in session.items():
            print(k, type(k), type(v), v)
        logging.info(f"Session loaded:\n{session}")
        logging.info(f"Session parameters:\n({type(session['parameters'])})\n{session['parameters']}")
        return session

    def delete_remote_session(self, session_id:str):
        """ Delete session data from the database. """
        os.remove(os.path.join(self.filedir, f"{session_id}.json"))
        logging.info(f"Session '{session_id}' deleted!")

    def update_remote_session(self, session_id:str, data:dict):
        """ Update or insert session data in the database. """
        assert 'session_id' in data and data['session_id'] == session_id
        with open(os.path.join(self.filedir, f"{session_id}.json"), 'w') as f:
            json.dump(data, f)
        logging.info(f"Session '{session_id}' updated!")

    def retrieve_sessions(self, sessions:list=None) -> list:
        """ 
        Retrieve chat history (list of dicts) for specified sessions (list of dicts)
        or *all* sessions if no sessions specified in optional argument.

        Returns
            chats: (list) of "long" form data with one session-message per row, e.g.
                [
                    {'session_id':101, 'time':0, 'role':'interviewer', 'message':'Hello', ...}
                    {'session_id':101, 'time':1, 'role':'respondent', 'message':'World', ...}
                    ...
                ]
        """
        chats = []
        for session_file in os.listdir(self.filedir):
            if not session_file.endswith('.json'): continue
            if sessions and not os.splitext(session_file)[0] in sessions: continue
            filepath = os.path.join(self.filedir, session_file)
            with open(filepath, 'r') as f:
                session = json.load(f) 
            # Add all messages in current interview session
            chats.extend([message for message in session['chat']])

        logging.info(f"Retrieved {len(chats)} messages!")
        return chats
