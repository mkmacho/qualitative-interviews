import json
import time
import logging


class InterviewManager(object):
    """
    Class to manage the conversation history for an interview 
    between the user and the AI-interviewer.

    Args:
        client: (redis.Redis) database client
        session_id: (str) unique interview session key
        first_question: (str) question that began interview
        max_flags_allowed: (int) how many possible security risks to allow
    """
    def __init__(
        self, 
        client:object, 
        session_id:str, 
        first_question:str=None,
        max_flags_allowed:int=4
    ):
        self.session_id = session_id
        self.client = client
        if client.get(session_id):
            logging.info(f"Resuming interview session '{session_id}'...")
            self.data = json.loads(client.get(session_id))
            logging.info(f"Loaded interview data:\n{self.data}")
        else:
            logging.info(f"Starting new interview session '{session_id}'...")
            assert first_question
            self.data = {
                'session_id': session_id,
                'current_topic_idx': 0,
                'current_question_idx': 0,
                'current_finish_idx': 0,
                'chat': [],
                'flagged_messages': [],
                'terminated': False,  
                'summary': '',
                'outputs': [],
                'max_flags_allowed': max_flags_allowed
            }
            # Add starting interview question to transcript
            self.add_message(first_question, role='assistant')

    def get_session(self) -> dict:
        """ Get data associated with current interview session. """
        return self.data

    def delete_remote_session(self):
        """ Delete data associated with current interview session. """
        self.client.delete(self.session_id)
        logging.info(f"Interview '{self.session_id}' successfully deleted!")

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
            self.update_remote_session_data()
            logging.error("Flagged too often: quitting!")
            return True        
        return False

    def update_remote_session(self):
        """ Update remote database interview object. """
        self.client.set(self.session_id, json.dumps(self.data))
        assert self.client.get(self.session_id)
        logging.info(f"Updated interview session '{self.session_id}'...")

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


   