import os
import redis
import json
import time
import logging
from core.parameters import MAX_FLAGS_COUNTER

sessions = redis.Redis(
    host=os.environ["REDIS_HOST"], 
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"]
)
logging.info("Redis connection established -- should happen only once!")

class InterviewManager(object):
    """
    Class to manage the conversation history for an interview 
    between the user and the AI-interviewer, 
    """
    def __init__(self, session_id:str, body:dict={}):
        self.session_id = session_id
        if sessions.get(session_id):
            logging.info(f"Resuming interview session '{session_id}'...")
            self.data = json.loads(sessions.get(session_id))
            logging.info(f"Loaded:\n{self.data}")
        elif body.get('open_topics'):
            assert body.get('first_question')
            logging.info(f"Starting interview session '{session_id}'...")
            self.data = {
                'session_id': session_id,
                'open_topics': body['open_topics'],
                'closing_questions': body.get('closing_questions', []),
                'current_topic_idx': 0,
                'current_question_idx': 0,
                'current_finish_idx': 0,
                'chat': [],
                'security': {
                    'flag_counter': 0, 
                    'flagged_messages': []
                },
                'terminated': False,  
                'summary': '',
                'summary_cleaned': '',
                'outputs': []
            }
            self.add_message(body['first_question'], role='assistant')
        else:
            logging.info(f"Interview session '{session_id}' not loaded!")
            self.data = {}

    def delete(self):
        """ Delete Redis interview key """
        sessions.delete(self.session_id)
        logging.info(f"Interview '{self.session_id}' successfully deleted!")

    def is_terminated(self) -> bool:
        """ If interview has been terminated. """
        return self.data['terminated']

    def get_summary(self) -> str:
        """ Return summary of interview. """
        summary = self.data.get("summary_cleaned") or self.data.get("summary")
        if not summary:
            logging.error("No summary to return.")
        return summary

    def get_topic_guide(self) -> dict:
        """ Return list of topics to cover in interview. """
        return self.data['open_topics']

    def flag_risk(self, user_reply:str):
        """ Flag possible security risk. """
        self.data["security"]["flag_counter"] += 1
        self.data["security"]["flagged_messages"].append((
            user_reply, 
            int(time.time())
        ))
        logging.warning("Flagging possible risk...")

    def is_off_topic(self, agent:object, user_reply:str) -> bool:
        assert self.data["chat"][-1]["role"] == "assistant"
        prior_question = self.data["chat"][-1]["content"]
        if not agent.check_relevance(prior_question, user_reply):
            interview.flag_risk(user_reply)
            interview.update_remote_session_data()
            logging.error("User response not on topic, quitting.")
            return True
        return False

    def flagged_too_often(self) -> bool:
        """ Check if the conversation has been flagged too often. """
        if self.data["security"]["flag_counter"] >= MAX_FLAGS_COUNTER:
            self.terminate("security_flag_counter_exceeded")
            self.update_remote_session_data()
            logging.error("Flagged too often, quitting.")
            return True        
        return False

    def update_remote_session_data(self):
        """ Update remote database interview object. """
        sessions.set(self.session_id, json.dumps(self.data))
        assert sessions.get(self.session_id)
        logging.info(f"Updated interview session '{self.session_id}'...")

    def add_message(self, message:str, role:str):
        """ Add to chat history. """
        assert role in ["user", "assistant", "system"]
        self.data['chat'].append({
            'role':role, 
            'content':message,
            'time':int(time.time())
        })

    def has_repeated_message(self, message:str, min_length:int=5) -> bool:
        """ Check if user has repeated the same message multiple times. """
        # Ignore if the chat is not long enough
        if len(self.data["chat"]) < min_length:
            return False

        # Check if the last/penultimate message of the user are the same
        return message in (chat['content'] for chat in self.data["chat"][-2:])

    def terminate(self, reason:str="end_of_interview_reached"):
        """ Record termination of interview. """
        self.data["terminated"] = True
        self.data["terminated_reason"] = reason

    def update_summary(self, agent:object, clean:bool=False):
        """ Update summary information. """
        summary = agent.summarize(self.data, clean=clean)['SUMMARY']['Summary']
        self.data["summary_cleaned" if clean else "summary"] = summary
        logging.info("Successfully added summary to history.")

    def get_current_topic(self) -> int:
        """ Return topic index. """
        return self.data["current_topic_idx"]

    def get_current_topic_question(self) -> int:
        """ Return question index within topic. """
        return self.data["current_question_idx"]

    def _update_counters(self, output:dict):
        """ Update the topic and question counters in interview 
            history based on action we just took. 
        """
        if output.get("TRANSITION"):
            # Having just transitioned topic...
            self.data["current_question_idx"] = 1   # reset question counter
            self.data["current_topic_idx"] += 1     # increment topic counter
        elif output.get("PROBE"):
            # Having just probed within topic... 
            self.data["current_question_idx"] += 1  # only increment question
        else:
            assert output.get("FINISH")
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



   