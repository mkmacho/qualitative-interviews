from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import logging 


def is_code(message:str, threshold:int=5) -> bool:
    """ Check if the message contains code as proxied by certain symbols. """
    counts = Counter(message)
    code_symbols = ["{", "}", "(", ")", "[", "]", ";", ":", "=", "<", ">", "+", "-", "*", "&", "|", "!", "^", "~", "@"]
    code_count = sum(counts[symbol] for symbol in code_symbols)
    return code_count > (threshold * (1 + len(message) / 100.0))

def clean(output_str:str):
    cleaned = re.sub("[\"\'\''\''':]", "", output_str)
    cleaned = re.sub("\n", " ", cleaned)
    cleaned = re.sub(r"\+", " ", cleaned)
    return cleaned.strip()

def parsed(response_str:str) -> dict:
    """ Parse response into dictionary based on pre-set keys. """
    logging.info(f"GPT response: '{response_str}'...")
    section_names = ["Justification", "Choice", "Summary", "Question", "New_Topic_ID"]
    tag_pattern =  "(" + r"\: |".join(section_names) + ")"
    sections = re.split(tag_pattern, response_str, flags=re.DOTALL)
    result = {}
    for i in range(len(sections) - 1):
        if sections[i].split(': ')[0] in section_names:
            result[clean(sections[i])] = clean(sections[i+1])
    return result

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
    logging.info(f"Prompt to GPT:\n{prompt}")
    assert not re.findall(r"\{[^{}]+\}", prompt)
    return prompt 

def execute_queries(query, agent_args:dict) -> dict:
    """ 
    Execute queries (concurrently if multiple).

    Args:
        query: function to execute
        agent_args: (dict) of arguments for each agent's query
        parse_output: (bool) to parse output for task specific response
    Returns:
        suggestions (dict): {agent_name: agent_output} 
    """
    st = time.time()
    suggestions = {}
    with ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its agent
        future_to_agent = {
            executor.submit(query, **kwargs): agent 
                for agent, kwargs in agent_args.items()
        }
        for future in as_completed(future_to_agent):
            agent = future_to_agent[future]
            resp = future.result().choices[0].message.content.strip("\n '''")
            suggestions[agent] = resp

    logging.info("Query took {:.2f} seconds.".format(time.time() - st))
    return suggestions



