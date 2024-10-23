import boto3
import json
import time
import logging
from core.parameters import MAX_SECURITY_FLAG_COUNTER, END_OF_INTERVIEW_SEQUENCE

DB = boto3.resource('dynamodb').Table("UserChats")
logging.critical("DynamoDB connection established -- should happen only once!")

def to_camelCase(s:str):
    """Converts string from snake_case to camelCase."""
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

class InterviewData(object):
    """
    Class to manage the conversation history for a single interview 
    between the user and the AI interviewer.

    The (unique) ID of each session will be
    a concatenation of request data keys separated with a hash.
    """
    def __init__(self, body:dict):
        session_id = []
        for key in ["userID", "surveyID", "questionID", "versionID"]:
            session_id.append(str(body[key]))
        self.session_id = "#".join(session_id)
        self.data = {}
        logging.info(f"Loaded specific interview: {self.session_id}.")
    
    def get(self, key, raiseKeyError=True):
        """ Get a value from the local interview data (chat history). """
        return self.data.get(key) if not raiseKeyError else self.data[key]

    def set(self, key, value):
        """ Set a value in the local interview data (chat history). """
        self.data[key] = value

    def load_remote_session_data(self):
        """ Load data for this participants x survey # question combination. """
        response = DB.get_item(Key={'session_id':self.session_id})
        if not 'Item' in response: return
        
        # Format session data
        self.data = response['Item']
        for key in ['counter_topic', 'tokens_last_prompt', 'tokens_last_reply', "summary_end"]:
            self.data[key] = int(self.data[key]) 

        # Second level attributes
        for key in ["flag_counter", "speed_counter"]:
            self.data["security"][key] = int(self.data["security"][key])

        # List attributes
        self.data["topic_history"] = [int(x) for x in self.data["topic_history"]]

        logging.info("Successfully loaded interview history from DB.")

    def flag(self, user_reply:str):
        """ Flag possible security risk. """
        self.data["security"]["flag_counter"] += 1
        self.data["security"]["flagged_messages"].append((user_reply, int(time.time())))

    def update_summary(self, new_summary:str):
        """ Update summary information 
        (we summarized everything, so override the previous summary)
        """
        self.set("summary", new_summary)
        self.set("summary_end", len(self.get("chat")))

    def initialize_conversation(self, body:dict):
        """
        Create first db entry for the participant x survey x question x version combination.

        Arg
            body (dict): the HTML request data from the event object.
        Returns:
            new_entry (dict): the new entry to be added to the DynamoDB table.
        """
        assert not self.data
        self.data = {
            'session_id': self.session_id,
            'userID': str(body['userID']),
            'surveyID': str(body['surveyID']),
            'questionID': str(body['questionID']),
            'versionID': str(body['versionID']),
            'temperature_history': float(body.get('temperature_history', 0.0)),
            'temperature_finish': float(body.get('temperature_finish', 0.7)),
            'temperature_topic': float(body.get('temperature_topic', 0.7)),
            'temperature_probing': float(body.get("temperature_probing", 0.7)),
            'tokens_last_prompt': 0,
            'tokens_last_reply': 0,
            'counter_topic': 1,
            'counter_finish': 1,
            'topics': body['topics'], # json.loads(body['topics']) if isinstance(body['topics'], str)
            "topics_length": body["topicsLength"],
            'topic_history': [1],
            'question_type': ['topic_agent'],
            'agent_output': [{
                'topic_agent': {
                    'response': {
                        'new_topic_id': 1, 
                        'question': str(body['firstQuestion'])
                    }
                }
            }],
            'model_name_short': body.get('model_name_short', 'gpt-4o'),
            'model_name_long': body.get('model_name_long', 'gpt-4o'),
            # Could default these here from parameters
            'prompt_topic': body['promptTopic'],
            'prompt_history': body['promptHistory'],
            'prompt_finish': body['promptFinish'],
            'prompt_probing': body['promptProbing'],
            #'prompt_combined': '',
            'chat': [],
            'chat_timestamps': [],
            'security': {
                'flag_counter': 0,
                'flagged_messages': [],
                'speed_counter': 0,
                'speed_flagged_messages': []
            },
            'terminated': False,  # True if the interview was terminated
            'terminated_reason': '', # Reason for termination
            'summary': '',
            'summary_cleaned': '',
            'summary_end': 0  # index of the last message that was included in the summary
        }

    def update_remote_session_data(self):
        """ Update db entry with local conversation data. """
        DB.put_item(Item=self.data)

    def add_message(self, message:str, role:str, tokens_last_prompt:int=0, tokens_last_reply:int=0):
        """
        Add message to the raw chat history.
        
        Args
            message (str): the message to be added.
            role (str): the role of the message, either "user" or "assistant" or "system"
        """
        self.data['chat'].append({'role': role, 'content': message})
        self.data['chat_timestamps'].append(int(time.time()))

        # update token count
        if (tokens_last_prompt > 0) & (tokens_last_reply > 0):
            self.data['tokens_last_prompt'] = tokens_last_prompt
            self.data['tokens_last_reply'] = tokens_last_reply
        
    def update_state_variables(self, agent_name:str):
        """ Update the counters and other state variables in interview object. """
        # Update topic history (assuming the "finish" topic is NOT among the listed topics)
        topic_history = self.get("topic_history")
        current_topic_id = int(topic_history[-1])
        last_topic_id = max([int(k) for k in self.get("topics").keys()])

        if agent_name == "topic_agent":
            self.set("topic_history", topic_history + [current_topic_id + 1])
        elif agent_name == "finish_agent":
            self.set("topic_history", topic_history + [last_topic_id + 1])
        else:
            self.set("topic_history", topic_history + [current_topic_id])

        # Update question type (e.g. which agent is asking the question)
        self.set("question_type", self.get("question_type") + [agent_name])

        # Update counters
        if agent_name == "topic_agent":
            self.set("counter_topic", 1)

        elif agent_name == "probing_agent":
            self.set("counter_topic", self.get("counter_topic") + 1)

        elif agent_name == "finish_agent":
            if current_topic_id == last_topic_id:
                # Handle the case where we just transitioned to the "finish" topic
                self.set("counter_topic", 1)
                self.set("counter_finish", self.get("counter_finish") + 1)
            else:
                # In all other cases, increment the topic counter
                self.set("counter_topic", self.get("counter_topic") + 1)
                self.set("counter_finish", self.get("counter_finish") + 1)
        else:
            raise ValueError(f"Unknown choice: {agent_name}")

    def check_security_counter(self):
        """ 
        Check if the conversation has been flagged too often. 
        If so, terminate the conversation, update, and return termination message.

        Returns
            exceeded (bool): whether security counter has been exceeded
        """
        if self.data["security"]["flag_counter"] >= MAX_SECURITY_FLAG_COUNTER:
            # Update termination status, if necessary
            if not self.data["terminated"]:
                self.set("terminated", True)
                self.set("terminated_reason", "security_flag_counter_exceeded")
                self.update_remote_database()

            # Termination message to the client
            termination_message = f"Please note, many of your messages have " \
                "been identified as unusual input. " \
                "Please proceed to the next page.\n {END_OF_INTERVIEW_SEQUENCE}"
            return (True, termination_message)
        
        return (False, None)

    def user_repeated_previous_message(self, user_message:str, min_chat_length:int=5):
        """ Check if the user has repeated the same message multiple times. """
        # Don't do this if the chat is not long enough
        if len(self.data["chat"]) < min_chat_length:
            return False

        # Check if the last two messages of the user are the same
        if user_message == self.data["chat"][-2]["content"]:
            return True

        # Check if the user just repeated the last message of the AI
        if user_message == self.data["chat"][-1]["content"]:
            return True

        return False

    def is_code(self, user_message:str, threshold:int=5):
        """ Check if the message contains code. 
        Return True if it does, False otherwise.
        """
        symbols = ["{", "}", "(", ")", "[", "]", ";", ":", "=", "<", ">", "+", "-", "*", "&", "|", "!", "^", "~", "@"]
        count = sum(user_message.count(symbol) for symbol in symbols)
        return count > (threshold * (1 + len(user_message) / 100.0))
  