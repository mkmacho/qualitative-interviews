from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import logging 
import os

def is_code(message:str, threshold:int=5) -> bool:
    """ Check if the message contains code as proxied by certain symbols. """
    counts = Counter(message)
    code_symbols = ["{", "}", "(", ")", "[", "]", ";", ":", "=", "<", ">", "+", "-", "*", "&", "|", "!", "^", "~", "@"]
    code_count = sum(counts[symbol] for symbol in code_symbols)
    return code_count > (threshold * (1 + len(message) / 100.0))

def cleaned(response, task:str):
    output = response.choices[0].message.content.strip("\n\" '''")
    logging.info(f"GPT response: '{output}'")
    if task in ['summary']:
        return output
    sections = re.sub("[\n'''*]", "", output).split(':')
    if len(sections) == 1:
        return sections[0].strip()
    elif len(sections) == 2:
        logging.warning(f"Multiple sections found: {output}")
        prompt = sections[0].lower()
        if len(prompt.split()) <= 2 and ("question" in prompt or "message" in prompt):
            return sections[1].strip()
    else:
        logging.error(f"Received many sections: '{output}'")
    return ':'.join(sections)

def current_topic_history(chat:list) -> str:
    """ Convert messages from current topic into one string. """
    topic_history = ""
    for message in chat:
        if message["role"] == "assistant":
            topic_history += f"Interviewer: ''{message['content']}''\n"
        if message["role"] == "user":
            topic_history += f"Interviewee: ''{message['content']}''\n"
    return topic_history.strip()

def fill_prompt_with_interview_state(template:str, topics:list, interview_state:dict) -> str:
    """ Fill the prompt template with parameters from current interview. """
    current_topic_idx = interview_state['current_topic_idx'] 
    next_topic_idx = min(current_topic_idx + 1, len(topics) - 1)
    history = current_topic_history(interview_state['chat'])
    if os.getenv("APP_ENV") == "DEV":
        logging.info(f"Conversation history:\n{history}")
    prompt = template.format(
        topics='\n'.join([topic['topic'] for topic in topics]),
        question=interview_state["chat"][-1]["content"],
        answer=interview_state["user_message"],
        summary=interview_state['summary'],
        current_topic=topics[current_topic_idx]["topic"],
        next_interview_topic=topics[next_topic_idx]["topic"],
        current_topic_history=history
    )
    if os.getenv("APP_ENV") == "DEV":
        logging.info(f"Prompt to GPT:\n{prompt}")
    assert not re.findall(r"\{[^{}]+\}", prompt)
    return prompt 

def execute_queries(query, task_args:dict) -> dict:
    """ 
    Execute queries (concurrently if multiple).
    In current Python 3.13, default `max_workers` set to
        min(32, (os.process_cpu_count() or 1) + 4)

    Args:
        query: function to execute
        task_args: (dict) of arguments for each task's query
    Returns:
        suggestions (dict): {task: output} 
    """
    st = time.time()
    suggestions = {}
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(query, **kwargs): task 
                for task, kwargs in task_args.items()
        }
        for future in as_completed(futures):
            task = futures[future]
            suggestions[task] = cleaned(future.result(), task)

    logging.info("Query took {:.2f} seconds, returned: {}".format(
        time.time() - st,
        suggestions
    ))
    return suggestions



