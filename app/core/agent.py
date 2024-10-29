from openai import OpenAI
from core.auxiliary import execute_queries, fill_prompt_with_interview_state


class Agent(object):
    def __init__(self, api_key:str, timeout:int=20, max_retries:int=4):
        self.client = OpenAI(
            timeout=timeout,     # 20 seconds (default is 10 minutes)
            max_retries=max_retries,  # default is 2
            api_key=api_key,
        )

    def load_parameters(self, parameters:dict):
        self.parameters = parameters

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


