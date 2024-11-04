import os
import logging
from openai import OpenAI
from core.auxiliary import execute_queries, fill_prompt_with_interview_state

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class Agent(object):
    def __init__(self, api_key:str=OPENAI_API_KEY, timeout:int=20, max_retries:int=4):
        self.client = OpenAI(
            api_key=api_key, 
            timeout=timeout, 
            max_retries=max_retries
        )
        logging.info("OpenAI client instantiated -- should happen only once!")

    def load_parameters(self, parameters:dict):
        self.parameters = parameters
        logging.info("Interview-specific agent instructions loaded.")

    def construct_query(self, tasks:list, interview_state:dict) -> dict:
        return {
            task: {
                "messages": [{
                    "role":"user", 
                    "content": fill_prompt_with_interview_state(
                        self.parameters[task]['prompt'], 
                        self.parameters['open_topics'],
                        interview_state
                    )
                }],
                "model": self.parameters[task]['model'],
                "max_tokens": self.parameters[task]['max_tokens'],
                "temperature": self.parameters[task].get('temperature', 0)
            } for task in tasks
        }

    def is_message_relevant(self, message:str, interview_state:dict) -> bool:
        """ Is user answer relevant or 'on topic' to given prompt? """
        interview_state['user_message'] = message
        assert interview_state["chat"][-1]["role"] == "assistant"
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['security'], interview_state)
        )
        return "yes" in response["security"].lower()
        
    def probe_within_topic(self, interview_state:dict) -> (str, dict):
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['probe'], interview_state)
        )
        return response['probe'], response

    def transition_topic(self, interview_state:dict) -> (str, dict):
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['summary','transition'], interview_state)
        )
        return response['transition'], response


