from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import logging 

def might_be_code(message:str, threshold:int=5) -> bool:
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

def parsed_response(response) -> dict:
    """ Extract response and parse them into a dictionary based on pre-set keys. """
    response_str = response.choices[0].message.content.strip().strip("'''")
    logging.info(f"GPT response: '{response_str}'...")
    section_names = ["Justification","Choice","Summary","Question","New_Topic_ID"]
    tag_pattern =  "(" + r"\: |".join(section_names) + ")"
    sections = re.split(tag_pattern, response_str, flags=re.DOTALL)
    result = {}
    for i in range(len(sections) - 1):
        if sections[i].split(': ')[0] in section_names:
            result[clean(sections[i])] = clean(sections[i+1])
    return result

def execute_queries(query, agent_args:dict) -> dict:
    """ 
    Execute queries (concurrently if multiple).

    Args:
        query: function to execute
        agent_args: (dict) of arguments for each agent's query
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
            suggestions[agent] = parsed_response(future.result())
    logging.info("Query took {:.2f} seconds.".format(time.time() - st))
    return suggestions

def construct_messages(user_prompt, data, system_prompt) -> list:
    return [
        {
            "role":"user", 
            "content":_fill_prompt(
                user_prompt, 
                data["open_topics"],
                data["current_topic_idx"],
                ### NOTE: Should this not be summary_end + 1 ? ###
                data["chat"], 
                data["summary"]
            )
        },
        {
            "role":"system", 
            "content":system_prompt
        }
    ]

def _conversation_history_str(messages:list) -> str:
    """ Convert the recent messages on the current topic into one string. """
    topic_history = ""
    for message in messages:
        if message["role"] == "assistant":
            topic_history += f"Interviewer: ''{message['content']}''\n"
        if message["role"] == "user":
            topic_history += f"Interviewee: ''{message['content']}''\n"
    return topic_history.strip()

def _fill_prompt(
    prompt_template:str, 
    topics_list:list, 
    current_topic_idx:int, 
    messages:str,
    summary:str
    ) -> str:
    """ Fill the instruction templates with all possible parameters. """
    next_topic_idx = min(current_topic_idx + 1, len(topics_list) - 1)
    history = _conversation_history_str(messages)
    logging.info(f"Conversation history (post summary):\n{history}")
    prompt = prompt_template.format(
        topics='\n'.join([topic['topic'] for topic in topics_list]),
        summary=summary,
        current_topic=topics_list[current_topic_idx]["topic"],
        next_interview_topic=topics_list[next_topic_idx]["topic"],
        current_topic_history=history
    )
    logging.info(f"Prompt to GPT:\n{prompt}")
    assert not re.findall(r"\{[^{}]+\}", prompt)
    return prompt 

