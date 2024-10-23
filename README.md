# qualitative-interviews #

Python web application using Flask and uWSGI. 
TODO: Write description of project.


## Installation

To run locally, we advise you create a virtual environment so as to install necessary packages in a clean environment, guaranteed of no clashing dependencies.

```bash
 python3 -m venv interviews
 source ./inteviews/bin/activate
```

Install packages with `pip`

```bash
cd interviews
 pip install -r requirements.txt
```

Customize `parameters` to meet your personal requirements.


## To Run ##

TODO: explain Docker process.

```
cd interviews/
./run.sh
```

## API ##
Currently there is just one API call `/interview`.


###### interview ######

Given a user response (`message`) to a `firstQuestion`, prompts, and ID variables, we make a request to the application to return the subsequent step (i.e. new question or follow-up) in the interview process.

This can be done e.g. via [Postman](https://www.postman.com/) as follows:

`POST http://0.0.0.0:8000/interview` (using Docker, run `docker ps` to get the port forwarding)

or via the command-line as:

```python
import requests
response = requests.post("http://0.0.0.0:8000/interview", headers=headers, json=payload)
```

though the simplest will be to observe (and run) the tests in `tests.py`.

Example headers:
```
{
    "origin":"https://nhh.eu.qualtrics.com"
}
```

Example payload:
```
{
    "message": "I can't afford it and the stock market is rigged.",
    "firstQuestion": "I am interested in learning more about why you currently do not own any stocks or stock mutual funds. Can you help me understand the main factors or reasons why you are not participating in the stock market?",
    "topics": {
        "1": "Explore the reasons behind the interviewee's choice to avoid the stock market.",
        "2": "Delve into the perceived barriers or challenges preventing them from participating in the stock market.",
        "3": "Explore a 'what if' scenario where the interviewee invest in the stock market. What would they do? What would it take to thrive? Probing questions should explore the hypothetical scenario.",
        "4": "Prove for conditions or changes needed for the interviewee to consider investing in the stock market."
    },
    "topicsLength": [6, 5, 3, 2],
    "promptTopic": """
        CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You're guiding a semi-structured qualitative interview about the interviewee's reasons for not investing in the stock market.

        INPUTS:
        A. Previous Conversation Summary:
        {summary}

        B. Current Conversation:
        {current_topic_history}

        C. Next Interview Topic:
        {next_interview_topic}

        TASK: Introducing the Next Interview Topic from the interview plan by asking a transition question.

        GUIDELINES:
        1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
        2. Natural transition: To make the transition to a new topic feel more natural and less abrupt, you may use elements from the Current Conversation and Previous Conversation Summary to provide context and a bridge from what has been discussed to what will be covered next.
        3. Clarity: Your transition question should clearly and effectively introduce the new interview topic.

        RESPONSE FORMAT: Your response should use the template below:
        '''Question: "Insert your transition question here" '''

        Remember to include "Question:" in your response. Start your response here:
    """,
    "promptHistory": """
        CONTEXT: You're an AI proficient in summarizing qualitative interviews for academic research. You're overseeing the records of a semi-structured qualitative interview about the interviewee's reasons for not investing in the stock market.

        INPUTS:
        A. Interview Plan:
        {topics}

        B. Previous Conversation Summary:
        {summary}

        C. Current Topic:
        {current_topic}

        D. Current Conversation:
        {current_topic_history}

        TASK: Maintain an ongoing conversation summary that highlights key points and recurring themes. The goal is to ensure that future interviewers can continue exploring the reasons for non-participation without having to read the full interview transcripts.

        GUIDELINES:
        1. Relevance: Prioritize and represent information based on their relevance and significance to understanding the interviewee's reasons for not investing in the stock market.
        2. Update the summary: Integrate the Current Conversation into the Previous Conversation Summary, ensuring a coherent and updated overview. Avoid adding redundant information.
        3. Structure: Your summary should follow the interview's chronology, starting with the first topic. Allocate space in the summary based on relevance for the research objective, not just its recency.
        4. Neutrality: Stay true to the interviewee's responses without adding your own interpretations of inferences.
        5. Sensitive topics: Document notable emotional responses or discomfort, so subsequent interviewers are aware of sensitive areas.
        6. Reasons: Keep an up-to-date overview of the interviewee's reasons for non-participation.

        Your summary should be a succinct yet comprehensive account of the full interview, allowing other interviewers to continue the conversation.

        RESPONSE FORMAT: Your response should use the template below:
        '''Summary: "Insert your summary here" '''

        Remember to include "Summary:" in your response. Start your response here:
    """,
    "promptFinish": {
        "1": "As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
        "2": "Reflecting on our conversation, what would you identify as the main reason you're not participating in the stock market?",
        "3": "Thank you for sharing your insights and experiences today. Your input is invaluable to our research. Please proceed to the next page."
    },
    "promptProbing": """
        CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's reasons for not investing in the stock market.

        INPUTS:
        A. Previous Conversation Summary:
        {summary}

        B. Current Interview Topic:
        {current_topic}

        C. Current Conversation:
        {current_topic_history}

        TASK: Your task is to formulate the next probing question for the Current Conversation. The question should align with the Current Interview Topic, helping us to better understand and systematically explore why the interviewee is not participating in the stock market.

        GENERAL GUIDELINES:
        1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
        2. Neutrality: Use questions that are unbiased and don't lead the interviewee towards a particular answer. Don't judge or comment on what was said. It's also crucial not to offer any financial advice.
        3. Respect: Approach sensitive and personal topics with care. If the interviewee signals discomfort, respect their boundaries and move on.
        4. Relevance: Prioritize themes central to the interviewee's stock market non-participation. Don't ask for overly specific examples, details, or experiences that are unlikely to reveal new insights.
        5. Focus: Generally, avoid recaps. However, if revisiting earlier points, provide a concise reference for context. Ensure your probing question targets only one theme or aspect.

        PROBING GUIDELINES:
        1. Depth: Initial responses are often at a "surface" level (brief, generic, or lacking personal reflection). Follow up on promising themes hinting at depth and alignment with the research objective, exploring the interviewee's reasons, motivations, opinions, and beliefs. 
        2. Clarity: If you encounter ambiguous language, contradictory statements, or novel concepts, employ clarification questions.
        3. Flexibility: Follow the interviewee's lead, but gently redirect if needed. Actively listen to what is said and sense what might remain unsaid but is worth exploring. Explore nuances when they emerge; if responses are repetitive or remain on the surface, pivot to areas not yet covered in depth.

        YOUR RESPONSE:
    """,
    "userID": 1,
    "surveyID": 2,
    "questionID": 3,
    "versionID": 4
}
```

This will return, if successful, a JSON with a `message` field that contains the next directive.

Example return:
```
{
    'message': 'Could you elaborate on what you mean by the stock market being rigged? What specific aspects or experiences lead you to feel this way?', 
}
```



###### App Structure ######

```
└── app/
    ├── app.py
    ├── tests.py
    ├── decorators.py
    ├── schema_validators/
    ├── core/    
    ├───── logic.py
    ├───── agents.py
    ├───── database.py
    ├───── openai_management.py
    ├───── parameters.py
```


###### app.py ######

All app API calls will be set up here.

###### tests.py ######

All API tests will be added here.

###### decorators.py ######

All API decorators will sit here. 

###### schema_validators/ ######

Validated incoming JSON schema as per [JSON Schema](http://json-schema.org/documentation.html).

###### core/logic.py ######

The main endpoint requests the next interview action from here.

###### core/agents.py ######

This file contains the interviewing agents.

###### core/database.py ######

This file contains functions for interacting with the AWS DynamoDB database.

###### core/openai_management.py ######

Integration with OpenAI GPT models.

###### core/parameters.py ######

*FOR NOW* contains the project-specific parameters.


## TODO ##

- Continue cleaning, slimming code
- Change how parameters saved, used (e.g. YAML?)
- Investigate I/O with Qualtrics
    - Should parameters include defaults here or those better set in JS?