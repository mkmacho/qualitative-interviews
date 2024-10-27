import logging
from core.agent import Agent
from core.database import InterviewManager
from core.auxiliary import might_be_code

agent = Agent()
logging.info("OpenAI client instantiated -- should happen only once!")


OFF_TOPIC_MESSAGE = """
I might have misunderstood your response, 
but it seems you might be trying to steer the interview off topic 
or that you have provided me with too little context. 
Can you please try to answer the question again in a different way, 
preferably with more detail, 
or say so directly if you prefer not to answer the question?
"""

END_OF_INTERVIEW_MESSAGE = """
Thank you for sharing your insights and experiences today. 
Your input is invaluable to our research. 
Please proceed to the next page.
---END---
"""

TERMINATION_MESSAGE = """
The interview is over. 
Please proceed to the next page.
---END---
"""

MAX_FLAGGED_MESSAGE = """
Please note, too many of your messages have been identified 
as unusual input. Please proceed to the next page.
---END---
"""

def load_interview(request:dict) -> dict:
    """ Return (summary of) interview history to user. """
    session_id = request['session_id']
    if request.get('get_summary'):
        return {'summary': InterviewManager(session_id).get_summary()}  
    return InterviewManager(session_id).data

def delete_interview(request:dict) -> dict:
    """ Delete existing interview saved to database. """
    session_id = request['session_id']
    return InterviewManager(session_id).delete()

def next_question(request:dict) -> dict:
    """
    Process user message and generate response by the AI-interviewer.

    Args:
        request: (dict) containing user input and interview structure
    Returns:
        response: (dict) containing `message` from interviewer
    """

    user_input = request['user_message']


    ##### LOAD INTERVIEW HISTORY OR INITIALIZE #####

    interview = InterviewManager(request['session_id'], request)

    # Exit condition: this interview has been previously ended
    if interview.is_terminated():
        return {'message': TERMINATION_MESSAGE}

    # Flag if user sending code or repeating messages
    if interview.has_repeated_message(user_input) or might_be_code(user_input):
        interview.flag_risk(user_input)

    # Terminate if the conversation has been flagged too often
    if interview.flagged_too_often():
        return {'message': MAX_FLAGGED_MESSAGE}

    # Terminate if user message does not fit the interview context
    if interview.is_off_topic(agent, user_input):
        return {'message': OFF_TOPIC_MESSAGE}

    # Update *after* security checks so flagged messages not added
    """ QUESTION: WHY NOT ADD TO HISTORY ANYWAY? """
    interview.add_message(user_input, role="user")


    ##### CONTINUE INTERVIEW BASED ON WORKFLOW #####

    # Topics to cover in interview
    topics_to_cover = interview.get_topic_guide()
    num_topics = len(topics_to_cover) 

    # Current topic guide
    current_topic_idx = interview.get_current_topic()
    on_last_topic = current_topic_idx == num_topics - 1
    logging.info(f"On topic {current_topic_idx+1}/{num_topics}...")

    # Current question within topic guide
    current_question_idx = interview.get_current_topic_question()
    num_questions = topics_to_cover[current_topic_idx]["length"]
    on_last_question = current_question_idx == num_questions - 1
    logging.info(f"On question {current_question_idx+1}/{num_questions}...")

    # Continue in workflow
    final_summary = False
    if on_last_topic and on_last_question:
        # Close interview with pre-determined closing questions
        last_questions_idx = interview["current_finish_idx"]
        last_questions = interview["closing_questions"]
        final_summary = last_questions_idx == len(last_questions) - 1
        
        # Exit condition: have already produced last "final" question
        if last_questions_idx == len(last_questions):
            interview.terminate()
            return {"message": END_OF_INTERVIEW_MESSAGE}

        # Otherwise, get next "final" interviewer question
        next_question = last_questions[last_questions_idx]
        output = {"FINISH": {"Question": next_question}}

    elif on_last_question:
        # Transition to *next* topic...
        next_question, output = agent.transition_topic(interview.data)

    else:
        # Proceed *within* topic...
        next_question, output = agent.probe_within_topic(interview.data)

    # Update interview with new output
    logging.info(f"Interviewer produced output:\n{output}")
    interview.update_summary(agent, clean=final_summary)
    interview.update_new_output(next_question, output)
    interview.update_remote_session_data()
    
    return {'message': next_question}



