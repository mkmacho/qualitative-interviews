import logging
from openai import OpenAI, AuthenticationError
from core.auxiliary import execute_queries, fill_prompt_with_interview_state, chat_to_string


class Agent(object):
    """ Class to manage LLM-based agents. """

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

    def construct_query(self, tasks:list, interview_state:dict) -> dict:
        """ 
        Construct OpenAI API completions query, 
        defaults to `gpt-4o-mini` model and temperature of 0. 
        For details see https://platform.openai.com/docs/api-reference/completions.
        """
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
                "model": self.parameters[task].get('model', 'gpt-4o-mini'),
                "max_tokens": self.parameters[task].get('max_tokens'),
                "temperature": self.parameters[task].get('temperature')
            } for task in tasks
        }

    def review_answer(self, message:str, interview_state:dict) -> bool:
        """ Moderate answers: Are they off topic or contain harmful content? """
        interview_state['user_message'] = message
        assert interview_state["chat"][-1]["role"] == "assistant"
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['moderator'], interview_state)
        )
        return "yes" in response["moderator"].lower()

    def review_question(self, next_question:str) -> bool:
        """ Moderate questions: Are they flagged by the moderation endpoint? """
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=next_question,
            )
        return response.to_dict()["results"][0]["flagged"]
        
    def probe_within_topic(self, interview_state:dict) -> str:
        """ Return next 'within-topic' probing question. """
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['probe'], interview_state)
        )
        return response['probe']

    def transition_topic(self, interview_state:dict) -> tuple[str, str]:
        """ 
        Determine next interview question transition from one topic
        cluster to the next. If have defined `summarize` model in parameters
        will also get summarization of interview thus far.
        """
        summarize = interview_state['parameters'].get('summarize')
        tasks = ['summary','transition'] if summarize else ['transition']
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(tasks, interview_state)
        )
        return response['transition'], response.get('summary', '')
