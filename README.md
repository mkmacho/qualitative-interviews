# qualitative-interviews #

Companion codebase for ["Conducting Qualitative Interviews with AI"](https://dx.doi.org/10.2139/ssrn.4583756). Set up your own interview structure and leverage [OpenAI's](https://platform.openai.com/docs/overview) GPT large language models (LLMs) to probe specified topics, smoothly transition to new topics, and gracefully close interviews with respondents. 

Suggested citation:
```
Chopra, Felix and Haaland, Ingar, Conducting Qualitative Interviews with AI (2023). CESifo Working Paper No. 10666, Available at SSRN: https://ssrn.com/abstract=4583756 or http://dx.doi.org/10.2139/ssrn.4583756
```


## Table of Contents
* [Usage](#usage)
  * [Requirements](#requirements)
  * [Docker](#docker)
  * [Manually](#manually)
  * [Customization](#customization)
* [API](#api)
* [App Structure](#app-structure)
* [TODO](#todo)



## Usage

This is a Flask web application in Python that run with [uWSGI and Nginx](https://flask.palletsprojects.com/en/stable/deploying/uwsgi/). We can install manually or run it in a single Docker container.

### Requirements

The application requires OpenAI API access. You can obtain API keys [here](https://platform.openai.com/). You will then need to supply your secret key as an environment variable in the `docker-compose` YML file as `OPEN_AI_KEY`. 


### Docker

The simplest way to then run the application is via [Docker](https://www.docker.com/products/docker-desktop/). You can easily build a Docker image containing only the necessary packages in a contained environment -- from whatever operating system!

To start a `qualitative-interviews` container, first clone the project:

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews
```

Then build and run a container using the provided `Dockerfile` and the template `docker-compose` YAML, modified by replacing "YOUR_OPENAI_API_KEY" with your actual key.

```bash
docker-compose up --build --detach
```

Just like that, you can now make requests to your local host listening (by default, at least) port 8000, e.g. *http://0.0.0.0:8000/*.

Finally, note that you can stop and remove containers and networks in the compose file using ``docker-compose down``.


### Manually 

Otherwise, you can set it up by hand. We advise you to first create a virtual environment so as to install necessary packages in a clean environment, guaranteed of no clashing dependencies.

```bash
 python3 -m venv venv
 cd venv
 source ./bin/activate
```

Then clone the project, install the necessary packages with `pip`, and export necessary environment variables:

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews

pip install -r requirements.txt

export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
export DATABASE_URL="<YOUR_DB_URL>"
```

Finally, start serving the application by running:

```bash
python app/app.py
```

And again you can make requests to your local host at *http://0.0.0.0:8000/*.


### Customization

To customize the structure of the interviews (e.g. the topics covered, the duration, the LLM prompts, etc.) simply add or edit a new `python` dictionary containing relevant information for your project.

Currently, in `parameters.py` you will see one element in `INTERVIEW_PARAMETERS`: *STOCK_MARKET_PARTICIPATION*. This interview parameters object holds the guidelines for interviewing respondents on their lack of participation in the stock market, but generally it will be beneficial to use this as a template for constructing your own interview parameters.

Specifically, the parameters object must contain elements:

* *moderate_answers*: whether to active the moderation agent for incoming answers from the respondent
* *moderate_questions*: whether to check outgoing questions with OpenAI's moderation endpoint
* *summarize*: whether to active the summarization agent
* *first_question*: the initial prompt that begins the interview
* *interview_plan*: the list of topic dictionaries which include the `topic` as well as the `length`, indicating for how many questions to cover in this topic
* *closing_questions*: the (fixed) list of questions/comments (if any) with which to end the interview
* *end_of_interview_message*: the message to display at the end of the interview
* *termination_message*: the message to display in the event the user responds to an ended interview
* *flagged_message*: the message to display to adversarial behavior
* *off_topic_message*: the message to display if the user's response is deemed off-topic

As well as elements defining the LLM-interactions:

* *summary*: if/how you would like the AI-interviewer to summarize the interview thus far
* *transition*: if/how you would like the AI-interviewer to transition topics 
* *probe*: if/how you would like the AI-interviewer to probe topics
* *moderator*: if/how you would like the AI-interviewer to ascertain user message relevance

All of which define a `prompt` for the AI-interviewer, a maximum length (`max_tokens`) for the desired response, a `temperature` for the variability of the response, and a `model` for the LLM to use. Note that the prompt may reference the current state of the interview or the defined interview structure through the use of curly bracket variables (e.g. `{topics}` will be populated by the defined `interview_plan`).

A sample of this template for *STOCK_MARKET_PARTICIPATION* interviews is displayed here:

```
{
    "moderate_answers": True,
    "moderate_questions": True,
    "summarize": True,
    "first_question": "I am interested in learning more about why you currently do not own any stocks or stock mutual funds. Can you help me understand the main factors or reasons why you are not participating in the stock market?",
    "interview_plan": [
        {
            "topic":"Explore the reasons behind the interviewee's choice to avoid the stock market.",
            "length":6
        },
        {
            "topic":"Delve into the perceived barriers or challenges preventing them from participating in the stock market.",
            "length":5
        }
    ],
    "closing_questions": [
        "As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?"
    ],
    "end_of_interview_message": "Thank you for sharing your insights and experiences today. Your input is invaluable to our research. Please proceed to the next page.---END---",
    "summary": {
        "prompt": """
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

            YOUR RESPONSE:
        """,
        "max_tokens": 1000,
        "temperature": 0,
        "model": "gpt-4o"
    },
    "transition": {
        "prompt": "...",
    },
    "probe": {
        "prompt": "...",
    },
    "moderator": {
        "prompt": "...",
    }
}
```


## API

The main API is to begin and host an interview. This is done by making a GET request with the interview `interview_id` and the interview `session_id` in the URL. 

For example, given an interview parameter ID (e.g. `interview_id == 'STOCK_MARKET'`) and the (unique) session ID of the interview (`session_id == 'TEST_SESSION'`), we can make a request to the host and port our application is serving on plus these keys, in this case just opening `http://0.0.0.0:8000/STOCK_MARKET/TEST_SESSION` on any browser. The web page will show you the beginning question of the interview, as specified in the parameters corresponding to the `parameters_id` you supplied, and prompt the user to answer this question. Each subsequent response by the user will be processed by the 'AI-interviewer' and the web page will dynamically update to show this ongoing chat. 

Note that the dynamic updating is done in the back end through a `POST` request to the internal `/next` endpoint which, for a given session and user reply, determines the following message to be shown.


### Testing 

You can test the `/next` endpoint through Python as follows:

```python
import requests
response = requests.post("http://0.0.0.0:8000/next", headers=headers, json=payload)
```

Example headers:
```
{
    "origin":"http://0.0.0.0:8000"
}
```

Example starting payload:
```
{
    "user_message": "I can't afford it and the stock market is rigged.",
    "session_id": "TEST_SESSION",
    "interview_id": "STOCK_MARKET"
}
```

This will return, if successful, a JSON with a `message` field that contains the next directive (as well as the `session_id`):

Example return:
```
{
    'message': 'Could you elaborate on what you mean by the stock market being rigged? What specific aspects or experiences lead you to feel this way?',
    'session_id': 'TEST_SESSION'
}
```

Example follow-up payload:

```
{
    "user_message": "People like me never get ahead, only the super rich and big trading firms win.  I don't want to be swindled.",
    "session_id": "TEST_SESSION",
    "interview_id": "STOCK_MARKET"
}
```

Example follow-up response:
```
{
    'message': 'What specific events or information have you come across that reinforce your belief that the stock market primarily benefits the wealthy and large trading firms?',
    'session_id': 'TEST_SESSION'
}
```

And et cetera.


## App Structure

```
└── app/
    ├── app.py
    ├── tests.py
    ├── log.py
    ├── decorators.py
    ├── schema_validators.py
    ├── parameters.py
    ├── core/    
    ├───── logic.py
    ├───── agent.py
    ├───── database.py
    ├───── manager.py
    ├───── auxiliary.py
    ├── templates/    
    ├───── chat.html    
```


### app.py

All app API calls set up here.

### tests.py

All API tests live here.

### decorators.py

All API decorators live here. 

### schema_validators.py

Validated incoming JSON schema as per [JSON Schema](http://json-schema.org/documentation.html).

### parameters.py

Contains the interview-specific guidelines and parameters. *Update or create your own LLM prompts here!*

### core/logic.py

Endpoint responses are processed here.

### core/agent.py

AI-interviewer (GPT integration) lives here.

### core/database.py

The Redis data store integration live here.

### core/manager.py

The interview manager processes run through here.

### core/auxiliary.py

This file contains additional functions useful to the core logic.

### templates/html.py

This file the HTML landing page users see and interact with. *Update the HTML or Javascript to reflect personal taste!*



## TODO

- **How to best deploy application?**
    - [Google](https://realpython.com/python-web-applications/)
    - AWS
        - *Will start with trying to deploy here 06/12!*
    - Azure
        - Potentially easy for academics to use through institutions
    - *Regardless, want either easy script set-up or detailed manual instructions*
- **Stress testing**
    - *Recall: Need low latency, handle multiple queries sudden influx*    
    - Is bottleneck given machine/instance memory limit?
    - Can set (rule) number of child processes/workers?
    - Is our API (similarly OpenAI) parallel or concurrent?
- Fix spare algorithm in `app.ini`


