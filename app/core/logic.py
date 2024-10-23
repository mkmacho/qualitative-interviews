import os
import logging
from core.openai_management import execute_agents_in_parallel, security_check_user_message, choose_model_for_context
from core.agents import TopicAgent, HistoryAgent, FinishAgent, CombinedProbingAgent
from core.database import InterviewData
from core.parameters import MODEL_NAME_SECURITY, PROMPT_CLEANING, END_OF_INTERVIEW_SEQUENCE

APP_ENV = os.getenv("APP_ENV", "DEV")

def _next_action(interview:dict)->str:
	"""
	Determine what to do next in the interview.

	Args
		interview: dict object containing interview context
	Returns
		action (str): one of ("transition", "proceed", "finish")
	"""
	# Get the last topic id and the current topic id
	last_topic_id = max([int(k) for k in interview.get("topics").keys()])
	current_topic_id = int(interview.get("topic_history")[-1])

	# Get the current topic counter and the length of the current topic 
	topic_counter = int(interview.get("counter_topic"))
	topics_length = [int(k) for k in interview.get("topics_length")] + [10]  # for the "finish" topic, add 10.

	# This assumes that the "end of interview" topic is NOT among the listed topics,
	# such that "is_last_topic == True" means we are in the last non-finish block.
	is_last_question_in_topic = (topic_counter >= topics_length[current_topic_id - 1])

	if (current_topic_id == last_topic_id) and is_last_question_in_topic:
		return "finish"
	elif (current_topic_id < last_topic_id) and is_last_question_in_topic:
		return "transition"
	elif current_topic_id > last_topic_id:
		return "finish"
	return "proceed"

def next_question(body:dict)->str:
	"""
	Process user reply and generate the response by the AI interviewer.

	Args
		body (dict) containing request
		sandbox (bool): whether to integrate with DB
	Returns
		(str) response
	"""
	# Get conversation data
	interview = InterviewData(body)
	if APP_ENV != "DEV":
		# In DEV mode, just load empty dictionary
		interview.load_remote_session_data()

	# Exit condition: send response to the client that the interview is over
	if interview.get("terminated", raiseKeyError=False):
		logging.info("Interview terminated...")
		return "The interview is over. Please proceed to the next page."

	# Exit condition: client request for summary of interview 
	if body.get("get_summary"):
		logging.info("Returning interview transcripts summary...")
		return interview.get("summary_cleaned") or interview.get("summary")

	# Initialize interview history 
	if not interview.data:
		interview.initialize_conversation(body)
		interview.add_message(body['firstQuestion'], "assistant")
	
	if APP_ENV == "DEV":
		logging.info(f"Have initial interview history of {interview.data}...")

	################# PROCESS USER REPLY ####################

	user_reply = body['message']


	################## SECURITY CHECK ########################

	# Terminate if the conversation has been flagged too often
	exceeded, termination_message = interview.check_security_counter()
	if exceeded:
		logging.error("Security error: counter exceeded, terminating...")
		return termination_message

	# Sending code or repeating messages?
	if interview.user_repeated_previous_message(user_reply) or interview.is_code(user_reply):
		interview.flag(user_reply)

	# Response fits the interview context?
	secure = security_check_user_message(
		last_question=interview.data["chat"][-1]["content"],
		user_answer=user_reply, 
		model=MODEL_NAME_SECURITY
	)
	if not secure:
		interview.flag(user_reply)
		if APP_ENV != "DEV":
			interview.update_remote_session_data()
		# Send a response to the client that the user message is not secure
		logging.error("Security error: reseting interview....")
		return "I might have misunderstood your response, but it seems " \
			"you might be trying to steer the interview off topic or that " \
			"you have provided me with too little context. Can you please " \
			"try to answer the question again in a different way, preferably " \
			"with more detail, or say so directly if you prefer not to answer the question?"


	# Add new message to interview transcript
	# After security checks to ensure message is not added if it is flagged
	interview.add_message(user_reply, role="user")


	#################### API CALLS ##########################

	# Determine the next action in the interview workflow. Do routing based on this below.
	action = _next_action(interview)

	# Determine the model based on the expected context length (4k or 16k).
	default_model = choose_model_for_context(interview, user_reply)

	# TOPIC TRANSITION
	if action == "transition":
		suggestions = execute_agents_in_parallel([
			HistoryAgent(
				interview.data, 
				interview.get("prompt_history"), 
				interview.get("temperature_history"),
				interview.get("model_name_long")
			),
			TopicAgent(
				interview.data, 
				interview.get("prompt_topic"), 
				interview.get("temperature_topic"),
				default_model 
			)
		])
		next_agent = "topic_agent"
		interview.update_summary(suggestions["history_agent"]["response"]["summary"])		

	# WITHIN TOPIC
	if action == "proceed":
		probing_agent = CombinedProbingAgent(
			interview.data, 
			interview.get("prompt_probing"), 
			interview.get("temperature_probing"),
			default_model
		)
		suggestions = {"probing_agent": probing_agent.generate_output()}
		next_agent = "probing_agent"
	
	# FINISH INTERVIEW
	if action == "finish":
		finish_agent = FinishAgent(
			interview.data, 
			interview.get("prompt_finish"), 
			interview.get("temperature_finish"),
			default_model
		)
		counter_finish = int(interview.get("counter_finish"))
		next_agent = "finish_agent"

		if counter_finish <= 1:
			# First finish question: Update summary once.
			suggestions = execute_agents_in_parallel([
				finish_agent, 
				HistoryAgent(
					interview.data, 
					interview.get("prompt_history"),
					interview.get("temperature_history"),
					interview.get("model_name_long")
				)
			])
			interview.update_summary(suggestions["history_agent"]["response"]["summary"])

		elif counter_finish == 2:
			# 2nd finish question: Clean the summary from meta comments before we share it with users
			suggestions = execute_agents_in_parallel([
				finish_agent, 
				HistoryAgent(
					interview.data, 
					PROMPT_CLEANING, 
					0.0, 
					interview.get("model_name_long")
				)
			])
			# Add cleaned summary
			interview.set("summary_cleaned", suggestions["history_agent"]["response"]["summary"])

		else:
			# From 3rd question: Only return the pre-determined questions and check whether the interview should be terminated.
			suggestions = {"finish_agent": finish_agent.generate_output()}

			# Handle end of interview. Force end of interview if necessary.
			if END_OF_INTERVIEW_SEQUENCE in suggestions[next_agent]["response"]["question"]:
				interview.set("terminated", True)
				interview.set("terminated_reason", "end_of_interview_reached")


	############## BOOK KEEPING #############
	# New question from the AI
	new_question = suggestions[next_agent]["response"]["question"]

	# Add output from agents to interview
	interview.set("agent_output", interview.get("agent_output") + [suggestions])

	# Update the interview state variables
	interview.update_state_variables(next_agent)

	# Prepare tokens counts update (approximate)
	new_question_tokens = int((len(new_question) * 0.3))
	max_token_use = max([x["tokens_response"] for x in suggestions.values()])

	interview.add_message(new_question, "assistant", max_token_use, new_question_tokens)
	if APP_ENV != "DEV":
		interview.update_remote_session_data()

	logging.info("Successfully determined next question.")
	return new_question



