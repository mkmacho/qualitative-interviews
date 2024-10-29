import logging
import os
from redis import Redis
from core.agent import Agent
from core.database import InterviewManager
from core.auxiliary import is_code
from parameters import INTERVIEW_PARAMETERS

agent = Agent(
    api_key=os.environ['OPENAI_API_KEY']
)
logging.info("OpenAI client instantiated -- should happen only once!")

client = Redis(
    host=os.environ["REDIS_HOST"], 
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"]
)
logging.info("Redis connection established -- should happen only once!")

def load_interview(session_id:str) -> dict:
    """ Return interview session history to user. """
    return InterviewManager(client, session_id).get_session()

def delete_interview(session_id:str) -> dict:
    """ Delete existing interview saved to database. """
    InterviewManager(client, session_id).delete_remote_session()
    return {'success': True}

def next_question(session_id:str, user_message:str, parameters_id:str) -> dict:
    """
    Process user message and generate response by the AI-interviewer.

    Args:
        session_id: (str) unique interview session ID
        user_message: (str) interviewee response
        parameters_id: (str) containing interview guidelines index
    Returns:
        response: (dict) containing `message` from interviewer
    """
    if not INTERVIEW_PARAMETERS.get(parameters_id):
        raise ValueError("Invalid interview parameters specified")
    parameters = INTERVIEW_PARAMETERS[parameters_id]
    agent.load_parameters(parameters)

    ##### LOAD INTERVIEW HISTORY OR INITIALIZE #####

    interview = InterviewManager(
        client, 
        session_id, 
        parameters['first_question'],
        parameters.get('max_flags_allowed', 4)
    )

    # Exit condition: this interview has been previously ended
    if interview.is_terminated():
        return {'message': parameters['termination_message']}

    # Flag if user sending code or repeating messages
    if interview.repeated_messages(user_message) or is_code(user_message):
        interview.flag_risk(user_message)

    # Terminate if the conversation has been flagged too often
    if interview.flagged_too_often():
        return {'message': parameters['flagged_message']}

    # Terminate if user message does not fit the interview context
    if not agent.is_message_relevant(user_message, interview.data):
        interview.flag_risk(user_reply)
        """ QUESTION: Update session history or not? """
        # interview.update_remote_session() 
        return {'message': parameters['off_topic_message']}

    # Update *after* security checks so flagged messages not added
    """ QUESTION: WHY NOT ADD TO HISTORY ANYWAY? """
    interview.add_message(user_message, role="user")


    ##### CONTINUE INTERVIEW BASED ON WORKFLOW #####

    # Current topic guide
    num_topics = len(parameters['open_topics'])
    current_topic_idx = interview.get_current_topic()
    on_last_topic = current_topic_idx == num_topics - 1
    logging.info(f"On topic {current_topic_idx+1}/{num_topics}...")

    # Current question within topic guide
    current_question_idx = interview.get_current_topic_question()
    num_questions = parameters['open_topics'][current_topic_idx]['length']
    on_last_question = current_question_idx == num_questions - 1
    logging.info(f"On question {current_question_idx+1}/{num_questions}...")

    # Continue in workflow
    if on_last_topic and on_last_question:
        # Close interview with pre-determined closing questions
        last_questions = parameters["closing_questions"]
        
        # Exit condition: have already produced last "final" question
        if interview["current_finish_idx"] == len(last_questions):
            interview.terminate()
            return {"message": parameters['end_of_interview_message']}

        # Otherwise, get next "final" interviewer question
        next_question = last_questions[interview["current_finish_idx"]]
        output = {"finish": {"message": next_question}}

    elif on_last_question:
        # Transition to *next* topic...
        next_question, output = agent.transition_topic(interview.data)
        # Also update running summary of prior topics covered
        interview.update_summary(output['summary']['message'])

    else:
        # Proceed *within* topic...
        next_question, output = agent.probe_within_topic(interview.data)

    # Update interview with new output
    logging.info(f"Interviewer produced output:\n{output}")
    interview.update_new_output(next_question, output)
    interview.update_remote_session()
    
    return {'message': next_question}



