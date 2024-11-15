import logging
from openai import OpenAI, AuthenticationError
from core.auxiliary import execute_queries, fill_prompt_with_interview_state, convert_chat_to_strings

class Agent(object):
    def __init__(self, timeout:int=30, max_retries:int=3):
        self.client = OpenAI(timeout=timeout, max_retries=max_retries)
        try:
            self.client.chat.completions.create(
                messages=[{'role':'user', 'content':'test'}], 
                model='gpt-4o-mini'
            )
        except AuthenticationError as e:
            logging.error(f"OpenAI connection failed: {e}")
            raise
        logging.info("OpenAI client instantiated. Should happen only once!")

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
                        self.parameters['interview_plan'],
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
            self.construct_query(['moderator'], interview_state)
        )
        return "yes" in response["moderator"].lower()
        
    def probe_within_topic(self, interview_state:dict) -> (str, dict):
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['probe'], interview_state)
        )
        return response['probe'], response

    def transition_topic(self, interview_state:dict) -> (str, dict):
        summarize = interview_state['parameters']['summarize']
        tasks = ['summary','transition'] if summarize else ['transition']
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(tasks, interview_state)
        )
        if not summarize:
            current_topic_idx = interview_state['current_topic_idx'] 
            last_answer_current_topic_idx = int(2 * sum(topic['length'] for topic in topics[:current_topic_idx]))
            response['summary'] = convert_chat_to_strings(interview_state['chat'][:last_answer_current_topic_idx])
        return response['transition'], response
