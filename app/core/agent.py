from openai import OpenAI
import os
from core.auxiliary import execute_queries, construct_messages
from core.parameters import *


class Agent(object):
    def __init__(self, timeout:int=20, max_retries:int=4):
        self.client = OpenAI(
            timeout=timeout,     # 20 seconds (default is 10 minutes)
            max_retries=max_retries,  # default is 2
            api_key=os.environ['OPENAI_API_KEY'],
        )
        
    def check_relevance(self, question:str, answer:str) -> bool:
        """ Is user answer relevant or 'on topic' re: interviewer question? """
        response = self.client.chat.completions.create(
            messages= [{
                "role": "user", 
                "content": SECURITY_PROMPT.format(
                    last_question=question,
                    user_answer=answer,
                )
            }],
            model= SECURITY_MODEL,
            max_tokens= 2,
        )
        return "yes" in response.choices[0].message.content.lower()

    @staticmethod
    def _summary_query(user_prompt:str, interview:dict) -> dict:
        return {
            "messages": construct_messages(
                user_prompt,
                interview,
                SYSTEM_SUMMARY_PROMPT
            ),
            "model": DEFAULT_MODEL,
            "max_tokens": MAX_SUMMARY_LENGTH
        }

    @staticmethod
    def _transition_query(interview:dict) -> dict:
        return {
            "messages": construct_messages(
                USER_TRANSITION_PROMPT,
                interview,
                SYSTEM_TRANSITION_PROMPT
            ),
            "model": DEFAULT_MODEL,
            "max_tokens": MAX_RESPONSE_LENGTH,
            "temperature": TRANSITION_TEMPERATURE
        }

    @staticmethod
    def _probe_query(interview:dict) -> dict:
        return {
            "messages": construct_messages(
                USER_PROBING_PROMPT,
                interview,
                SYSTEM_PROBING_PROMPT
            ),
            "model": DEFAULT_MODEL,
            "max_tokens": MAX_RESPONSE_LENGTH,
            "temperature": PROBING_TEMPERATURE
        }

    def summarize(self, interview:dict, clean=False) -> dict:
        return execute_queries(
            self.client.chat.completions.create,
            {
                "SUMMARY": self._summary_query(
                    USER_CLEANING_PROMPT if clean else USER_SUMMARY_PROMPT,
                    interview
                )
            }
        )

    def probe_within_topic(self, interview:dict) -> str:
        response = execute_queries(
            self.client.chat.completions.create,
            {
                "PROBE": self._probe_query(interview)
            }
        )
        return response["PROBE"]["Question"], response

    def transition_topic(interview:dict) -> str:
        response = execute_queries(
            self.client.chat.completions.create,
            {
                "SUMMARY": self._summary_query(
                    USER_SUMMARY_PROMPT,
                    interview
                ), 
                "TRANSITION": self._transition_query(interview)
            }
        )
        return response["TRANSITION"]["Question"], response


