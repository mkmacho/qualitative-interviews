import logging
from core.agent import Agent
from core.database import DatabaseManager
from core.manager import InterviewManager
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

def begin_interview_session(interview_id:str, session_id:str) -> dict:
    """ Begin new interview session.

    Returns:
        response: (dict) containing starting question and session_id
    Raises:
        ValueError: (exception) if invalid parameters or session in progress
    """
    if not INTERVIEW_PARAMETERS.get(interview_id):
        raise ValueError("Invalid interview parameters specified!")
    parameters = INTERVIEW_PARAMETERS[interview_id]
    response = {'session_id':session_id}

    # Check if interview has already been started
    if db.load_remote_session(session_id): 
        return response | {'message':'interview_in_progress_error'}

    interview = InterviewManager(db, session_id).begin_session(parameters)
    logging.info("Beginning {} interview session '{}' with prompt '{}'".format(
        interview_id, session_id, parameters['first_question']
    ))
    return response | {'message':parameters['first_question']}

def next_question(session_id:str, user_message:str) -> dict:
    """
    Process user message and generate response by the AI-interviewer.

    Args:
        session_id: (str) unique interview session ID
        user_message: (str) interviewee response
        interview_id: (str) containing interview guidelines index
    Returns:
        response: (dict) containing `message` from interviewer
    """
    logging.info("Generating next question for session '{}' user message '{}'".format(
        session_id, user_message
    ))    
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

    # Optional: Moderate interviewee responses, e.g. flagging off-topic or harmful messages
    if parameters.get('moderate_answers') and parameters.get('moderator'):
        flagged = agent.review_answer(user_message, interview.get_session_info())
        if not flagged or interview.repeated_messages(user_message):
            interview.flag_risk(user_message)

        # Terminate if the conversation has been flagged too often
        if interview.flagged_too_often():
            interview.update_session()
            return response | {'message':parameters['flagged_message']}

        # If user message does not fit the interview context, give another chance
        if not flagged:
            interview.update_session() 
            return response | {'message':parameters['off_topic_message']}

    """
    UPDATE INTERVIEW WITH NEW USER MESSAGE
    Note this happens *after* security checks such that
    flagged messages are *not* added to interview history.
    """
    interview.add_message(user_message)


    ##### CONTINUE INTERVIEW BASED ON WORKFLOW #####

    # Current topic guide
    num_topics = len(parameters['interview_plan'])
    current_topic_idx = interview.get_current_topic()
    on_last_topic = current_topic_idx == num_topics
    logging.debug(f"On topic {current_topic_idx+1}/{num_topics}...")

    # Current question within topic guide
    current_question_idx = interview.get_current_topic_question()
    num_questions = parameters['interview_plan'][current_topic_idx-1]['length']
    on_last_question = current_question_idx == num_questions
    logging.debug(f"On question {current_question_idx}/{num_questions}...")

    # Continue in workflow
    if on_last_topic and on_last_question:
        # Close interview with pre-determined closing questions
        last_questions = parameters["closing_questions"]
        
        # Exit condition: have already produced last "final" question
        current_finish_idx = interview.get_session_info("current_finish_idx")
        if current_finish_idx > len(last_questions):
            interview.terminate()
            interview.update_session()
            return response | {'message':parameters['end_of_interview_message']}

        # Otherwise, get next "final" interviewer question
        next_question = last_questions[current_finish_idx - 1]
        interview.update_final_questions()

    elif on_last_question:
        # Transition to *next* topic...
        next_question, summary = agent.transition_topic(interview.get_session_info())
        interview.update_transition(summary)

    else:
        # Proceed *within* topic...
        next_question = agent.probe_within_topic(interview.get_session_info())
        interview.update_probe()

    # Update interview with new output
    logging.info(f"Interviewer responded: '{next_question}'")
    interview.add_message(next_question, role="assistant")
    interview.update_session()

    # Optional: Check if next question is flagged by OpenAI's moderation endpoint
    if parameters.get('moderate_questions'):
        flagged_question = agent.review_question(next_question)
        if flagged_question:
            interview.terminate(reason="question_flagged")
            interview.update_session()
            return response | {'message':parameters['end_of_interview_message']}
    
    return response | {'message':next_question}
