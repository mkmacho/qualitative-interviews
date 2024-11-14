import logging
from core.agent import Agent
from core.database import DatabaseManager
from core.manager import InterviewManager
from core.auxiliary import is_code
from parameters import INTERVIEW_PARAMETERS

agent = Agent()
db = DatabaseManager()

def load_interview_session(session_id:str) -> dict:
    """ Return interview session history to user. """
    return db.load_remote_session(session_id)

def all_interview_sessions() -> dict:
    """ Return all sessions (ID and interview) to user. """
    sessions = {}
    for session_id_bytes in db.client.keys():
        session_id = session_id_bytes.decode("utf-8")
        parameters = db.load_remote_session(session_id)['parameters']
        sessions[session_id] = parameters.get('_name', '')
    return sessions

def delete_interview_session(session_id:str):
    """ Delete existing interview saved to database. """
    db.delete_remote_session(session_id)

def begin_interview_session(interview_id:str, session_id:str) -> str:
    """ Begin new interview session.

    Returns:
        response: (dict) containing starting question and IDs
    Raises:
        ValueError: (exception) if invalid parameters or session in progress
    """
    if not INTERVIEW_PARAMETERS.get(interview_id):
        raise ValueError("Invalid interview parameters specified!")
    parameters = INTERVIEW_PARAMETERS[interview_id]

    # Check if interview has already been started
    if db.load_remote_session(session_id): return {'in_progress_error': True}

    logging.info(f"Beginning interview '{interview_id}': session '{session_id}'")
    interview = InterviewManager(db, session_id).begin_session(parameters)
    response = {
        'message':INTERVIEW_PARAMETERS[interview_id]['first_question'], 
        'interview_id':interview_id, 
        'session_id':session_id
    }
    logging.info(f"Interview ID: {response}")
    return response

def next_question(session_id:str, user_message:str) -> str:
    """
    Process user message and generate response by the AI-interviewer.

    Args:
        session_id: (str) unique interview session ID
        user_message: (str) interviewee response
        interview_id: (str) containing interview guidelines index
    Returns:
        response: (dict) containing `message` from interviewer
    """
    logging.info(f"Generating next question for user message '{user_message}'")    
    response = {'session_id':session_id}

    ##### LOAD INTERVIEW HISTORY OR INITIALIZE #####
    try:
        interview = InterviewManager(db, session_id).resume_session()
        parameters = interview.get_session_info('parameters')
    except (AssertionError, KeyError):
        logging.critical(f"Attempted to continue non-existent session {session_id}")
        return response | {'message':'interview_not_started_error'}

    # Load AI-interviewer agent 
    agent.load_parameters(parameters)

    # Exit condition: this interview has been previously ended
    if interview.is_terminated():
        return response | {'message':parameters['termination_message']}

    # Flag if user sending irrelevant, code or repeating messages
    on_topic = agent.is_message_relevant(user_message, interview.get_session_info())
    if not on_topic or interview.repeated_messages(user_message) or is_code(user_message):
        interview.flag_risk(user_message)

    # Terminate if the conversation has been flagged too often
    if interview.flagged_too_often():
        interview.update_session()
        return response | {'message':parameters['flagged_message']}

    # If user message does not fit the interview context, give another chance
    if not on_topic:
        interview.update_session() 
        return response | {'message':parameters['off_topic_message']}


    """ UPDATE INTERVIEW WITH NEW USER MESSAGE
    Note this happens *after* security checks such that
    flagged messages are *not* added to interview history.
    --> MIGHT RE-THINK THIS LOGIC TO ADD TO HISTORY BUT IGNORE? 
    """
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
        current_finish_idx = interview.get_session_info("current_finish_idx")
        if current_finish_idx == len(last_questions):
            interview.terminate()
            interview.update_session()
            return response | {'message':parameters['end_of_interview_message']}

        # Otherwise, get next "final" interviewer question
        next_question = last_questions[current_finish_idx]
        output = {"finish": {"message": next_question}}

    elif on_last_question:
        # Transition to *next* topic...
        next_question, output = agent.transition_topic(interview.get_session_info())
        # Also update running summary of prior topics covered
        interview.update_summary(output['summary'])

    else:
        # Proceed *within* topic...
        next_question, output = agent.probe_within_topic(interview.get_session_info())

    # Update interview with new output
    logging.info(f"Interviewer produced output:\n{output}")
    interview.update_new_output(next_question, output)
    interview.update_session()
    
    return response | {'message':next_question}



