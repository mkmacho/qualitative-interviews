import logging
from core.agent import Agent
from core.database import DatabaseManager
from core.manager import InterviewManager
from core.auxiliary import is_code
from parameters import INTERVIEW_PARAMETERS

agent = Agent()
client = DatabaseManager()

def load_interview_session(session_id:str) -> dict:
    """ Return interview session history to user. """
    return client.load_remote_session(session_id)

def delete_interview_session(session_id:str):
    """ Delete existing interview saved to database. """
    client.delete_remote_session(session_id)

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

    if client.load_remote_session(session_id):
        raise ValueError("Interview already in progress!")

    logging.info(f"Beginning interview '{interview_id}': session '{session_id}'")
    interview = InterviewManager(client, session_id).begin_session(parameters)
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
    response = {'session_id':session_id, 'message':"Test message prompt answer"}

    ##### LOAD INTERVIEW HISTORY OR INITIALIZE #####

    interview = InterviewManager(client, session_id).resume_session()
    parameters = interview.data['parameters']

    # Load AI-interviewer agent 
    agent.load_parameters(parameters)

    # Exit condition: this interview has been previously ended
    if interview.is_terminated():
        return response | {'message':parameters['termination_message']}

    # Flag if user sending code or repeating messages
    if interview.repeated_messages(user_message) or is_code(user_message):
        interview.flag_risk(user_message)

    # Terminate if the conversation has been flagged too often
    if interview.flagged_too_often():
        interview.update_session()
        return response | {'message':parameters['flagged_message']}

    # Terminate if user message does not fit the interview context
    if not agent.is_message_relevant(user_message, interview.data):
        interview.flag_risk(user_message)
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
        if interview["current_finish_idx"] == len(last_questions):
            interview.terminate()
            interview.update_session()
            return response | {'message':parameters['end_of_interview_message']}

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
    interview.update_session()
    
    return response | {'message':next_question}



