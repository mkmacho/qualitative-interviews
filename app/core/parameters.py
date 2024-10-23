END_OF_INTERVIEW_SEQUENCE = "---END---"  # Sequence that indicates the end of the interview. This is removed from the message on the client side.

MODEL_NAME_SECURITY = "gpt-4o-mini"  # model for the security check

MAX_SUMMARY_LENGTH = 1000  # Number of tokens to summarize the conversation history to
MAX_RESPONSE_LENGTH = 300  # Maximum number of tokens in the AI's response, except history agent

MAX_SECURITY_FLAG_COUNTER = 5  # Number of flags before the conversation is terminated
MAX_WRITING_SPEED_USER = 16  # Maximum writing speed of the user in characters per second that should not be exceeded, based on world record from Helena Matoušková (2003, 955 characters per minute).
MAX_FINISH_COUNTER = 4  # Maximum number of questions in the "finish" block at the end of the interview
MAX_SPEED_COUNTER = 4  # Number of times the user can exceed the maximum writing speed before the conversation is terminated.

WHITELISTED_DOMAINS = [
	"https://nhh.eu.qualtrics.com", 
	"https://cebi.eu.qualtrics.com"
]

### custom prompts ###

PROMPT_CLEANING = """
CONTEXT: Your task is clean a conversation summary by surgically removing specific meta comments without altering or reordering the remaining content in any way.

ORIGINAL SUMMARY:
"{summary}"

TASK: Review the ORIGINAL SUMMARY above and surgically remove any sentences or comments that specifically mention or highlight:
1. Areas where the interviewee signaled reluctance or discomfort to answer  questions.
2. Any indications that the interviewee preferred not to answer a particular question.

Ensure that:
- The order of the remaining sentences is identical to the original summary.
- The wording of each remaining sentence is identical and unaltered.
- No additions or rephrasings are made. Only specified sentences are removed.

RESPONSE FORMAT: Your response should use the template below:
'''Summary: "Insert your cleaned summary here" '''

Start your response here:
""".strip()
