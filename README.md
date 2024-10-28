# qualitative-interviews #

## Companion codebase for "Conducting Qualitative Interviews with AI"

This is a Python web application built with Flask and uWSGI. Using customizable prompts to [OpenAI's](https://platform.openai.com/docs/overview) GPT large language models (LLMs), the "AI-interviewer" will guide an interview along topics laid out in the request. Specifically, it will probe the respondent to learn more about their views on each topic laid out in the request, for up to a certain number of questions. 


## Installation

To run locally, first clone the repository

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews
```

Next, customize the LLM prompts in `parameters` to meet your personal requirements or use the defaults.


## To Run ##

### Docker ###

The simplest way to then run the application is via [Docker](https://www.docker.com/products/docker-desktop/). You can easily build a Docker image containing only the necessary packages in a contained environment -- from whatever operating system -- and run a container as follows:

```bash
docker build -t interviews .
docker run -d \
    -p "<YOUR_FORWARDING_PORT>:80" \
    -e OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>" \
    -e REDIS_HOST="<YOUR_REDIS_HOST_FOR_DATABASE>" \
    -e REDIS_PASSWORD="<YOUR_REDIS_PASSWORD>" \
    -e REDIS_PORT="<YOUR_REDIS_HOST_PORT>" \
    --name=interviews interviews
```

Now, you can make requests to your local "http://0.0.0.0:<YOUR_FORWARDING_PORT>/".


### Manually ### 

Otherwise, you can set it up by hand. First install the necessary packages with `pip`

```bash
pip install -r requirements.txt
```

TODO: Figure out manual supervisor set-up.


## API ##

The main API is to retrieve the next action in the interview process. Specifically, the AI-interviewer will supply the next question to the interviewee. This is done through a request to the `/next` endpoint.


###### /next ######

Given a user response (`message`) to a `first_question` and the structure of the interview, we make a request to the application to return the subsequent step (i.e. new question or follow-up) in the interview process.

The API can be called e.g. via [Postman](https://www.postman.com/) as follows:

`POST http://0.0.0.0:8000/next` (using Docker, run `docker ps` to get the port forwarding)

or via the command-line as:

```python
import requests
response = requests.post("http://0.0.0.0:8000/next", headers=headers, json=payload)
```

though the simplest will be to observe (and run) the tests in `tests.py`.

Example headers:
```
{
    "origin":"https://nhh.eu.qualtrics.com"
}
```

Example starting payload:
```
{
    "user_message": "I can't afford it and the stock market is rigged.",
    "first_question": "I am interested in learning more about why you currently do not own any stocks or stock mutual funds. Can you help me understand the main factors or reasons why you are not participating in the stock market?",
    "open_topics": [
        {
            "topic": "Explore the reasons behind the interviewee's choice to avoid the stock market.",
            "length": 6
        },
        {
            "topic":" Delve into the perceived barriers or challenges preventing them from participating in the stock market.",
            "length": 5
        },
        {
            "topic": "Explore a 'what if' scenario where the interviewee invest in the stock market. What would they do? What would it take to thrive? Probing questions should explore the hypothetical scenario.",
            "length": 3
        },
        {
            "topic": "Prove for conditions or changes needed for the interviewee to consider investing in the stock market.",
            "length": 2
        }
    ],
    "closing_questions":[
        "As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
        "Reflecting on our conversation, what would you identify as the main reason you're not participating in the stock market?"
    ],
    "session_id":101
}
```

This will return, if successful, a JSON with a `message` field that contains the next directive.

Example return:
```
{
    'message': 'Could you elaborate on what you mean by the stock market being rigged? What specific aspects or experiences lead you to feel this way?', 
}
```

Example follow-up payload:

```
{
    "user_message": "People like me never get ahead, only the super rich and big trading firms win.  I don't want to be swindled.",
    "session_id":101
}
```

Example response:
```
{
    'message': 'What specific events or information have you come across that reinforce your belief that the stock market primarily benefits the wealthy and large trading firms?'}
}
```

Et cetera.


###### App Structure ######

```
└── app/
    ├── app.py
    ├── tests.py
    ├── log.py
    ├── decorators.py
    ├── schema_validators.py
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

###### schema_validators.py ######

Validated incoming JSON schema as per [JSON Schema](http://json-schema.org/documentation.html).

###### core/logic.py ######

The main endpoint requests the next interview action from here.

###### core/agent.py ######

This file contains the AI-interviewer GPT integration.

###### core/database.py ######

This file contains the InterviewManager responsible for storing the conversation.

###### core/auxiliary.py ######

This file contains additional functions useful to the core.

###### core/parameters.py ######

**FOR NOW** contains the project-specific parameters.


## TODO ##

- HTTP Post vs Patch for continuing existing interview
- Does Redis interview store work well going forward?
- Change how custom parameters saved? (e.g. YAML?)
- Investigate I/O with Qualtrics
    - **Should parameters include defaults here or those better set in JS?**
- More generally, how best to deploy?
    - Google (https://realpython.com/python-web-applications/)
    - AWS
    - Azure
    - *Recall: Need low latency, handle multiple queries sudden influx*