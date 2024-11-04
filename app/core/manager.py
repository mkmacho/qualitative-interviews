import json
import time
import logging


class InterviewManager(object):
    """
    Class to manage the conversation history for an interview 
    between the user and the AI-interviewer.

    Args:
        client: database manager
        session_id: (str) unique interview session key
    """
    def __init__(self, client, session_id:str):
        self.client = client
        self.session_id = session_id
        self.data = {}
    
    def begin_session(self, parameters:dict):
        """
        Loads interview data and variables into session. 

        Args:
            parameters: (dict) interview guidelines
        """
        assert not self.data
        assert not self.client.load_remote_session(self.session_id)
        logging.info(f"Starting new session '{self.session_id}'")
        self.data = {
            'session_id': self.session_id,
            'current_topic_idx': 0,
            'current_question_idx': 0,
            'current_finish_idx': 0,
            'chat': [],
            'flagged_messages': [],
            'terminated': False,  
            'summary': '',
            'outputs': [],
            'max_flags_allowed': parameters.get('max_flags_allowed', 4),
            'parameters': parameters
        }
        # Add starting interview question to transcript
        self.add_message(parameters['first_question'], role='assistant')
        self.update_session()
        return self

    def resume_session(self):
        """ Load (remote) data into current Interview object. """
        self.data = self.client.load_remote_session(self.session_id)
        assert self.data 
        logging.info(f"Resumed existing interview session '{self.session_id}'")
        return self

    def get_session(self) -> dict:
        """ Get data associated with current interview session. """
        return self.data

    def is_terminated(self) -> bool:
        """ If interview has been terminated. """
        return self.data['terminated']

    def get_summary(self) -> str:
        """ Return summary of interview. """
        summary = self.data['summary']
        if not summary:
            logging.error("No summary: return empty string!")
        return summary

    def flag_risk(self, user_reply:str):
        """ Flag possible security risk. """
        self.data["flagged_messages"].append((
            user_reply, 
            int(time.time())
        ))
        logging.warning("Flagging possible risk...")

    def flagged_too_often(self) -> bool:
        """ Check if the conversation has been flagged too often. """
        if len(self.data['flagged_messages']) > self.data['max_flags_allowed']:
            self.terminate("security_flags_exceeded")
            logging.error("Flagged too often: quitting!")
            return True        
        return False

    def add_message(self, message:str, role:str):
        """ Add to chat history. """
        assert role in ["user", "assistant", "system"]
        self.data['chat'].append({
            'role':role, 
            'content':message,
            'time':int(time.time())
        })

    def repeated_messages(self, message:str, min_length:int=5) -> bool:
        """ Check if user has repeated the same message multiple times. """
        if len(self.data["chat"]) < min_length: # Ignore for short chats
            return False
        # Return if the last or penultimate message of the user are the same
        return message in (chat['content'] for chat in self.data["chat"][-2:])

    def terminate(self, reason:str="end_of_interview"):
        """ Record termination of interview. """
        self.data["terminated"] = True
        logging.info(f"Terminating interview because: '{reason}'")

    def update_summary(self, summary:str, agent:object):
        """ Update summary of prior interview. """
        self.data["summary"] = summary
        logging.info("Successfully added summary to history.")

    def get_current_topic(self) -> int:
        """ Return topic index. """
        return self.data["current_topic_idx"]

    def get_current_topic_question(self) -> int:
        """ Return question index within topic. """
        return self.data["current_question_idx"]

    def _update_counters(self, output:dict):
        """ Update the topic and question counters in interview based
            on action (e.g. transition, probe, or finish) we just took.
        """
        if output.get("transition"):
            # Having just transitioned topic...
            self.data["current_question_idx"] = 1   # reset question counter
            self.data["current_topic_idx"] += 1     # increment topic counter
        elif output.get("probe"):
            # Having just probed within topic... 
            self.data["current_question_idx"] += 1  # only increment question
        else:
            assert output.get("finish")
            self.data["current_finish_idx"] += 1    # increment final questions

    def update_new_output(self, next_question:str, output:dict):
        """ Update all interview variables before closing application. """
        output.update({
            "topic_idx": self.data['current_topic_idx'],
            "question_idx": self.data['current_question_idx']
        })
        self.data["outputs"] += [output]
        self.add_message(next_question, "assistant")
        self._update_counters(output)

    def update_session(self):
        """ Update session in remote database """ 
        self.client.update_remote_session(self.session_id, self.data)
   