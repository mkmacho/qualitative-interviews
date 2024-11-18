from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import logging 
import os

def cleaned(response, task:str):
    """ 
    In theory, we can trust OpenAI API responses to be formatted
    as we have requested. However, in case not, this is a very 
    simple check. 
    """
    output = response.choices[0].message.content.strip("\n\" '''")
    logging.debug(f"GPT response: '{output}'")
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
        logging.error(f"Received too many sections: '{output}'")
        raise ValueError("Unexpected response format from OpenAI.")
    return ':'.join(sections)

def chat_to_string(chat:list, topic_idx:int=None) -> str:
    """ Convert messages from chat into one string. """
    topic_history = ""
    for message in chat:
        # If desire specific topic's chat history:
        if topic_idx and message['topic_idx'] != topic_idx: 
            continue
        if message["role"] == "assistant":
            topic_history += f'Interviewer: "{message['content']}"\n'
        if message["role"] == "user":
            topic_history += f'Interviewee: "{message['content']}"\n'
    return topic_history.strip()

def fill_prompt_with_interview_state(template:str, topics:list, interview_state:dict) -> str:
    """ Fill the prompt template with parameters from current interview. """
    current_topic_idx = interview_state['current_topic_idx'] 
    next_topic_idx = min(current_topic_idx + 1, len(topics))
    current_topic_chat = chat_to_string(interview_state['chat'], current_topic_idx)
    prompt = template.format(
        topics='\n'.join([topic['topic'] for topic in topics]),
        question=interview_state["chat"][-1]["content"],
        answer=interview_state["user_message"],
        summary=interview_state['summary'],
        current_topic=topics[current_topic_idx - 1]["topic"],
        next_interview_topic=topics[next_topic_idx - 1]["topic"],
        current_topic_history=current_topic_chat
    )
    logging.debug(f"Prompt to GPT:\n{prompt}")
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
    with ThreadPoolExecutor(max_workers=len(task_args)) as executor:
        futures = {
            executor.submit(query, **kwargs): task 
                for task, kwargs in task_args.items()
        }
        for future in as_completed(futures):
            task = futures[future]
            suggestions[task] = cleaned(future.result(), task)

    logging.info("OpenAI query took {:.2f} seconds".format(time.time() - st))
    logging.debug(f"OpenAI query returned: {suggestions}")
    return suggestions
