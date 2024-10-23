from abc import ABC, abstractmethod
import re
import json
from core.openai_management import query_completion
from core.parameters import MAX_SUMMARY_LENGTH, MAX_RESPONSE_LENGTH, END_OF_INTERVIEW_SEQUENCE


class Agent(ABC):
    """General template for an agent."""
    @abstractmethod
    def __init__(self, name:str, interview:dict, prompt:str, temperature:float, model:str):
        self.name = name
        self.interview = interview
        self.prompt = prompt
        self.temperature = temperature
        self.model = model 

    @abstractmethod
    def generate_output(self, *args, **kwargs):
        pass

    @staticmethod
    def parse_response(response_str):
        """Extract response and parse them into a dictionary with one of the following keys: question, justification, choice, summary, new_topic_id."""
        tag_pattern = r"(Justification\:|Choice\:|Summary\:|Question\:|New_Topic_ID\:)"
        sections = re.split(tag_pattern, response_str, flags=re.DOTALL)
        clean = lambda x: x.replace("\n", " ").replace('"', '').replace(":", "").replace("'''", "").replace("''", "").strip()
        result = {
            clean(sections[i]).lower(): re.sub(" +", " ", clean(sections[i+1]))
            for i in range(len(sections)) if clean(sections[i]).lower() in ["question", "justification", "choice", "summary", "new_topic_id"]
        }
        return result

    def check_if_template_is_filled(self, template):
        """Check that all variables were filled"""
        pattern = r"\{[^{}]+\}"
        unfilled_templates = re.findall(pattern, template)
        if unfilled_templates:
            raise ValueError(f"Unfilled parameters in the prompt template of the {self.name} agent: {unfilled_templates}")
        return True

    def system_message(self):
        """Add a system message to the chat."""
        name = self.name

        if name in ["history_agent"]:
            message = f"""
            You are an expert at summarizing qualitative interviews for academic research.
            You ALWAYS (!) use the response template below:
            '''Summary: "Insert your summary here" '''
            """.strip()
        elif name in ["topic_agent"]:
            message = f"""
            You are an expert at conducting qualitative interviews for academic research.
            You ALWAYS (!) use the response template below:
            '''Question: "Insert your transition question here" '''
            """.strip()
        elif name in ["finish_agent"]:
            message = f"""
            You ALWAYS (!) use the response template below:
            '''Question: "Insert your question here" '''
            """.strip()
        elif name in ["probing_agent"]:
            message = """
            You are an expert at conducting qualitative interviews for academic research.
            You ALWAYS (!) use the response template below:
            '''Question: "Insert your question here" '''
            """.strip()
        else:
            raise ValueError(f"Unknown agent name in .system_message(): {name}")

        return [{"role": "system", "content": message}]

    def construct_current_topic_history(self):
        """Convert the recent messages on the current topic into a string"""

        index_summary_end = self.interview["summary_end"]
        new_messages = self.interview["chat"][index_summary_end:]

        current_topic_history = ""
        for msg in new_messages:
            if msg["role"] == "assistant":
                current_topic_history += f"Interviewer: ''{msg['content']}''\n"
            elif msg["role"] == "user":
                current_topic_history += f"Interviewee: ''{msg['content']}''\n"

        return current_topic_history.strip()
    

    def fill_prompt_template(self):
        """Fill the instruction templates with all possible parameters."""
    
        # Summary of previous topics
        summary = self.interview["summary"]

        # Topic related parameters
        topics_dict = self.interview["topics"]
        topic_history = self.interview["topic_history"]
        current_topic = topic_history[-1]

        # Next topic in plan (assume sequential numbering, be careful with data types here)
        # make sure to not run out of the dictionary by taking the min with the max of keys
        max_topic_keys = max([int(k) for k in topics_dict.keys()])
        next_id = min([int(current_topic) + 1, max_topic_keys])
        next_interview_topic = topics_dict[str(next_id)]

        # Construct the new prompt:
        remaining_interview_topics = '\n'.join(
            [f"  {k}. {v}" for k, v in topics_dict.items() if int(k) not in topic_history]
        )

        # full topic plan (for history agent ONLY)
        topics = '\n'.join([f"  {k}. {v}" for k, v in topics_dict.items()])
        
        # Question counters
        counter_topic = self.interview["counter_topic"]

        # Recent message history
        current_topic_history = self.construct_current_topic_history()

        # Fill the template with the variable names
        filled_prompt_template = f'''{self.prompt}'''.format(
            # Summary and topics
            topics=topics,
            summary=summary,
            current_topic=current_topic,
            remaining_interview_topics=remaining_interview_topics,
            next_interview_topic=next_interview_topic,
            # Recent message history
            current_topic_history=current_topic_history,
            # Counters
            counter_topic=counter_topic,
        )

        return filled_prompt_template


class TopicAgent(Agent):
    """Agent that guides the conversation across topics."""

    def __init__(self, *args, **kwargs):
        """Initialize the agent"""
        super().__init__("topic_agent", *args, **kwargs)

    def generate_output(self):
        """Generate a topic question based on the current state."""

        query = {"role": "user", "content": self.fill_prompt_template()}
        self.check_if_template_is_filled(query["content"])

        response = query_completion(
            model=self.model,
            prompt=[query] + self.system_message(),
            temperature=self.temperature,
            max_tokens=MAX_RESPONSE_LENGTH,
        )
        raw_response = response["response"]
    
        # Parse response: Handle the topic ID response (e.g. remove quotation marks and other non-numerical characters):
        response["response"] = self.parse_response(response["response"])
        assert "question" in response["response"], f"{self.name} did not return a question.  RESPONSE:\n {raw_response}"

        return response



class HistoryAgent(Agent):
    """Agent that coordiantes other agents."""

    def __init__(self, *args, **kwargs):
        """Initialize the agent"""
        super().__init__("history_agent", *args, **kwargs)


    def generate_output(self):
        """Generate a topic question based on the current state."""

        # If summary is needed
        query = {"role": "user", "content": self.fill_prompt_template()}
        self.check_if_template_is_filled(query["content"])

        response = query_completion(
            model=self.model,
            prompt=[query] + self.system_message(),
            temperature=self.temperature,
            max_tokens=MAX_SUMMARY_LENGTH,
        )
        raw_response = response["response"]

        # Parse response
        response["response"] = self.parse_response(raw_response)
        assert "summary" in response["response"], f"{self.name} did not return a summary. RESPONSE:\n {raw_response}"

        return response


class FinishAgent(Agent):
    """Agent that finishes the interview."""

    def __init__(self, *args, **kwargs):
        """Initialize the agent"""
        super().__init__("finish_agent", *args, **kwargs)


    def generate_output(self):
        """Generate a new question based on the current state."""

        # Get the next question from a pre-determined list of "final" wrap-up questions
        finish_counter = int(self.interview.get("counter_finish"))
        prompt_finish = json.loads(self.prompt)
        final_questions = {int(key): value for key, value in prompt_finish.items()}

        next_question = final_questions[finish_counter]

        # handle end of interview
        if finish_counter == len(final_questions):
            next_question += "\n" + END_OF_INTERVIEW_SEQUENCE

        response = {
            "response": {"question": next_question.strip()},
            "tokens_response": 0,
            "tokens_prompt": 0
        }

        return response


class CombinedProbingAgent(Agent):
    """Agent that comes up with probing questions."""

    def __init__(self, *args, **kwargs):
        """Initialize the agent"""
        super().__init__("probing_agent", *args, **kwargs)

    def generate_output(self):
        """Query the OpenAI API for a new question."""

        query = {"role": "user", "content": self.fill_prompt_template()}
        self.check_if_template_is_filled(query["content"])

        response = query_completion(
            model=self.model,
            prompt=[query] + self.system_message(),
            temperature=self.temperature,
            max_tokens=MAX_RESPONSE_LENGTH,
        )
        raw_response = response["response"]

        # Parse response
        response["response"] = self.parse_response(response["response"])
        assert "question" in response["response"], f"{self.name} did not return a question.  RESPONSE:\n {raw_response}"

        return response
