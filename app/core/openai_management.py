from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from core.parameters import MAX_RESPONSE_LENGTH
import logging

# Instantiate OpenAI client
client = OpenAI(
    timeout=20,   # 20 seconds (default is 10 minutes)
    max_retries=4,  # default is 2
    api_key=os.environ['OPENAI_API_KEY'],
)
logging.critical("OpenAI client instantiated -- should happen only once!")


CONTEXT_LENGTH = {
    "gpt-4o": 100000,
    "gpt-4o-mini": 100000,
    "gpt-4-turbo": 100000,
    "gpt-4": 8000,
}

def choose_model_for_context(interview, user_reply):
    """ Choose GPT model to use based on the length of conversation history. """
    tokens_last_call = interview.get('tokens_last_reply') + interview.get('tokens_last_prompt')
    expected_tokens = tokens_last_call + int(len(user_reply) * 0.3) + MAX_RESPONSE_LENGTH + 500
    model_short, model_long = interview.get("model_name_short"), interview.get("model_name_long")
    return model_short if expected_tokens < CONTEXT_LENGTH[model_short] else model_long


def query_completion(
        prompt: list,
        model: str = 'gpt-4o-mini',
        temperature: float = 0.5,
        max_tokens: int = 300,
        top_p: float = 1.0,
        n: int = 1,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0,
        **kwargs,
    ):
    """ Chat completion requests to OpenaAI. 
    Query the OpenAI API for a completion, based on the previous chat history.
    """

    assert model in ["gpt-4o-mini", "gpt-4o", "gpt-4"]
    assert isinstance(prompt, list), "Prompt must be a list of dicts."

    response = client.chat.completions.create(
        model=model,
        messages=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p, # don't set this away from 1 if temperature is below 1.0
        n=n, # number of completions to generate
        stream=False, # return all completions at once
        frequency_penalty=frequency_penalty, # penalize the model from repeating itself
        presence_penalty=presence_penalty, # penalize the model from talking about new topics
        **kwargs
    )

    # Return processed response
    return {
        "response": response.choices[0].message.content.strip(),
        "tokens_response": response.usage.completion_tokens,
        "tokens_prompt": response.usage.prompt_tokens,
    }


def security_check_user_message(last_question, user_answer, model):
    """
    Check if the user prompt fits the context of the conversation.
    - user_prompt: the user prompt to check
    - question: the question that the user prompt is supposed to answer

    Returns
        secure: bool(True) if user prompt fits context of conversation, else False
    """

    # Prompt for the security check
    check = f"""You are monitoring a conversation that is part of an in-depth interview. The interviewer asks questions and the interviewee replies. The interview should stay on topic. The interviewee should try to respond to the question of the interviewer (but it is not important to answer all questions that are asked), express a wish to move on, or decline to respond. The interviewee is also allowed to say that they don't know, do not understand the question, or express uncertainty. Responses can be very short, as long as they have some connection with the question. The interviewee's response might contain spelling and grammar mistakes. Here is the last part of the conversation.

    Interviewer: '{last_question}.'

    Interviewee: '{user_answer}.'

    That is the end of the conversation. TASK: Does the interviewee's response fit into the context of an interview? Please answer only with 'yes' or 'no' """

    # Perform query
    message = [{"role": "user", "content": check}]
    response = query_completion(
        prompt=message, temperature=0,
        max_tokens=2, model=model)

    # Process response (1 = secure, 0 = not secure)
    response_text = response["response"].lower().strip()
    if "yes" in response_text:
        secure = True
    else:
        secure = False

    return secure


def user_declines_to_answer(user_reply, model_name):
    """ Check whether the user wishes to move on or declines to answer the question. """

    prompt = f"""
    You are monitoring a conversation that is part of an interview. Your task is to assess whether the interviewee explicitly says that they decline to answer the question or expresses a strong wish to move on to the next question or topic. Ignore spelling and grammar mistakes in the interviewee's response.

    Interviewee: '{user_reply}'.

    Does the interviewee explicitly decline to answer the question or expresses a wish to move on? Please answer only with 'yes' or 'no'.
    
    Your assessment:"""

    message = [{"role": "user", "content": prompt}]

    response = query_completion(
        prompt=message,
        temperature=0,
        max_tokens=4,
        model=model_name)
    
    # Process response (1 = declines, 0 = does not decline)
    response_text = response["response"]
    if "yes" in response_text.lower():
        declines = True
    else:
        declines = False
    return declines


def execute_agents_in_parallel(agent_list):
    """ Execute agents in parallel.

    Arg:
        agent_list: list of instantiated agent classes to execute
    Returns:
        suggestions (dict): {agent_name: agent_output} 
        where agent_output is a dict with the keys "response" and "tokens_response"
    """

    def get_output(agent, *args, **kwargs):
        """Function wrapper for agent.generate_output method. Needed for parallel API calls."""
        return agent.generate_output(*args, **kwargs)

    output = dict()
    with ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its agent
        future_to_agent = {executor.submit(get_output, agent): agent.name for agent in agent_list}

        for future in as_completed(future_to_agent):
            agent_name = future_to_agent[future]
            try:
                output[agent_name] = future.result()
            except Exception as exc:
                print(f"{agent_name} generated an exception in execute_agents_in_parallel: {exc}")
    return output
