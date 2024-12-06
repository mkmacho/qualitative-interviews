# qualitative-interviews #

Companion codebase for ["Conducting Qualitative Interviews with AI"](https://dx.doi.org/10.2139/ssrn.4583756). Set up your own interview structure and leverage [OpenAI's](https://platform.openai.com/docs/overview) GPT large language models (LLMs) to probe specified topics, smoothly transition between topics, and gracefully close interviews with respondents. 

Suggested citation:
```
Chopra, Felix and Haaland, Ingar, Conducting Qualitative Interviews with AI (2023). CESifo Working Paper No. 10666, Available at SSRN: https://ssrn.com/abstract=4583756 or http://dx.doi.org/10.2139/ssrn.4583756
```


## Table of Contents
* [Usage](#usage)
  * [Requirements](#requirements)
  * [Local](#local)
  * [Flask](#flask)
  * [Serverless](#serverless)
  * [Customization](#customization)
* [API](#api)
* [App Structure](#app-structure)
* [Licensing](#licensing)



## Usage

This repository contains code to help you build, customize, test, and run AI interviews [locally](#Local), deploy a containerized [Flask](#Flask) application to any server, or deploy as a [serverless](#Serverless) [Lambda](https://docs.aws.amazon.com/lambda/) Function to Amazon Web Services (AWS).


### Requirements

The application requires OpenAI API access. You can obtain API keys [here](https://platform.openai.com/). 

You can then need to supply your secret key as an environment variable as follows:

```bash
export OPENAI_API_KEY='<YOUR_OPENAI_API_KEY>'
```

which will now be supplied to the application automatically!


### Local

To quickly run the application on your local machine, where it will be easy to implement changes to the interview guidelines and test the results, follow these instructions.

We advise you to first create a virtual environment so as to install necessary packages in a clean environment, guaranteed of no clashing dependencies.

```bash
 python3 -m venv my-test-env
 cd my-test-env
 source ./bin/activate
```

Then clone this project from Github, or if you have already cloned, activate a virtual environment. Now, install the necessary packages defined in the repository's `requirements.txt` file with `pip` and export the default local PostgreSQL database:

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews

pip install -r flask_config/requirements.txt

export DATABASE_URL=postgresql://postgres:postgres@0.0.0.0:5432/interviews
```

Now we are ready to start serving the application by simply running:

```bash
python app/app.py
```

This starts up our Flask web application in Python that run with [uWSGI and Nginx](https://flask.palletsprojects.com/en/stable/deploying/uwsgi/). 

As you can see in `app.py`, we are listening on port 8000 so you can now make requests to your local host at *http://0.0.0.0:8000/*!


### Docker

The simplest way to then run the application is via [Docker](https://www.docker.com/products/docker-desktop/). You can easily build a Docker image containing only the necessary packages in a contained environment -- from whatever operating system!

#### Build

To *build* a `qualitative-interviews` container, first clone the project:

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews
```

Then build and run a container using the provided `Dockerfile` and the template `docker-compose` YAML, which will automatically pick up your OpenAI API key from our environment, by running:

```bash
docker compose up --build --detach
```

Note that the `--build` option builds the image locally from the `Dockerfile`, while removing the `build` option will *pull* the image from DockerHub. The `--detach` option runs the containers in the background. 

Just like that, you can now make requests to your local host listening (by default) port 8000, e.g. *http://0.0.0.0:8000/*.

Note that you can stop and remove containers and networks in the compose file using `docker compose down`.

#### Deploy

If you want to deploy the Flask application remotely, Docker makes that easy too!

From your remote host make sure Docker is [installed](https://docs.docker.com/engine/install/ubuntu/) and then copy the `docker-compose` file. Then, again, we can simply run from the command line:

```bash
docker compose up --detach 
```

making use of the remote DockerHub image builds which we mentioned previously. 

Your remote machine will now forward requests to port 8000 onto port 80 on which the Docker container is listening, thereby processing remote requests. 


### Serverless

To run the application serverless on AWS you will need to create an AWS account if you do not yet have one and download (public and secret) access keys. With these command line interface keys, simply run 

```bash
./serverless-setup.sh <AWS_PUBLIC_ACCESS_KEY> <AWS_SECRET_ACCESS_KEY> <AWS_REGION>`
```

which will configure your command line AWS credentials, create an AWS storage bucket where build template will be stored, and create an AWS Dynamo database table to persistently store interviews sessions (in the Cloud). This has to be run just once!

Then, run 

```bash 
./serverless-deploy.sh` 
```

which will again take advantage of your environment-stored OpenAI key to deploy the Lambda function with OpenAI access and expose a public endpoint for you to make requests to!

Note that there is no endpoint suffix for this serverless function so requests will go straight to the endpoint, e.g. `https://<SOME_AWS_ID>.execute-api.<AWS_REGION>.amazonaws.com/Prod/`.


### Customization

To customize the structure of the interviews (e.g. the topics covered, the duration, the LLM prompts, etc.) simply add or edit a new `python` dictionary containing relevant information for your project.

Currently, in `parameters.py` you will see a few elements in `INTERVIEW_PARAMETERS`: *STOCK_MARKET* and *VOTING*. These interview parameters objects holds the guidelines for interviewing respondents on their lack of participation in the stock market (or voting), but generally it will be beneficial to use this as a template for constructing your own interview parameters.

Specifically, the parameters object must contain elements:

* *first_question*: the initial prompt that begins the interview
* *interview_plan*: the list of topic dictionaries which include the `topic` as well as the `length`, indicating for how many questions to cover in this topic
* *closing_questions*: the (fixed) list of questions/comments (if any) with which to end the interview
* *end_of_interview_message*: the message to display at the end of the interview
* *termination_message*: the message to display in the event the user responds to an ended interview
* *flagged_message*: the message to display to adversarial behavior
* *off_topic_message*: the message to display if the user's response is deemed off-topic

with the following elements being defaulted:

* *moderate_answers*: (True) whether to active the moderation agent for incoming answers from the respondent
* *moderate_questions*: (True) whether to check outgoing questions with OpenAI's moderation endpoint
* *summarize*: (True) whether to active the summarization agent


As well as elements defining the LLM-interactions:

* *summary*: if/how you would like the AI-interviewer to summarize the interview thus far
* *transition*: if/how you would like the AI-interviewer to transition topics 
* *probe*: if/how you would like the AI-interviewer to probe topics
* *moderator*: if/how you would like the AI-interviewer to ascertain user message relevance

Where the last four objects above define a `prompt` for the AI-interviewer, a maximum length (`max_tokens`) for the desired response, a `temperature` for the variability of the response, and a `model` for the LLM to use. Note that the prompt may reference the current state of the interview or the defined interview structure through the use of curly bracket variables (e.g. `{topics}` will be populated by the defined `interview_plan`).

A sample of this template for *STOCK_MARKET* interviews is displayed here:

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

### next

The main API `\next` is to continue (or begin, if not started) an interview. This is done by making an HTTP POST request with the following body:

```
{
    "route": "next",
    "payload": {
        "user_message": "USER_RESPONSE_TO_PRIOR_INTERVIEW_QUESTION",
        "session_id": "UNIQUE_INTERVIEW_SESSION_ID",
        "interview_id": "SET_OF_INTERVIEW_GUIDELINES"
    }
}
```

where the `route` key tells the application to return the `next` interview question, the `user_message` provdies the prior response (*if not the first request*) on which to build, the `interview_id` informs how to guide the interview at a high-level, and the `session_id` identifies the interview session.

For example, we can test this API localy using `curl` at the `http://0.0.0.0:8000/next` URL:

```bash
curl -X POST -d '{"route":"next", "payload": {"session_id": "TEST-SESSION-123", "interview_id": "STOCK_MARKET", "user_message":"I dont have disposable income to invest"} }' http://0.0.0.0:8000/next
```

where you can replace the URL with the host, port, endpoint URL exposed on your remote server or through AWS serverless.

You can also test the `/next` endpoint through Python with the above body as follows:

```python
import requests
response = requests.post("http://0.0.0.0:8000/next", json=body)
```

or similarly through [Postman](https://www.postman.com/api-platform/api-testing/).


#### Interface

We can make additionally test the application interface non-programmatically when built using Flask locally or on a remote server.

Given the host and host port our application is serving up, plus the previously specified `interview_id` and a unique `session_id` we can simply open up a browser to this URL (making a GET request to begin the interview) and walk through an interview.

For example, having exposed local "http://0.0.0.0:8000/", we can navigate to `http://0.0.0.0:8000/STOCK_MARKET/TEST-SESSION-123` on your browser of choice. This will open a web page displaying the `interview_id`-specified first question of the interview (as specified in the `parameters.py` file) and prompt the user to answer this question. Each subsequent response by the user will be processed by the AI-interviewer and the web page will dynamically update to show this ongoing chat. 


#### Qualtrics

TODO: Add Qualtrics methodology here.


#### Additional configurations

If you have pulled Docker `postgres` as the `docker-compose.yml` configuration does, and wish to use this as your backend from a locally serving app or using Docker but without the compose network, you should set the environment variables to:

```
export DATABASE=POSTGRES
export DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/interviews"
```

Alternatively, if you wish to use Redis as your backend, you should set the environment variables to:

```
export DATABASE=REDIS
export REDIS_HOST=<YOUR_REDIS_HOST>
export REDIS_PORT=<YOUR_REDIS_PORT>
export REDIS_PASSWORD=<YOUR_REDIS_PASSWORD>
```

And finally, if you wish to AWS Dynamo as your backend from a non-serverless set-up, you should configure your AWS credentials in your environment and pass the Dynamo table name to `DATABASE_URL`, e.g.

```
export DATABASE=DYNAMODB
export DATABASE_URL=<DYNAMO_TABLE_NAME>
```


### retrieve

The `/retrieve` endpoint/route retrieves a list of specified `session_id`'s or if no specific `session_id`'s are provided, *all* sessions.

The body looks like:
```
{
    "route": "retrieve",
    "payload": {
        "sessions": [
            "TEST-SESSION-123",
            "TEST-SESSION-456"
        ]
    }
}
```

which is called in a request as:

```bash
curl -X POST -d '{"route":"retrieve", "payload": {"sessions": ["TEST-SESSION-123", "TEST-SESSION-456"]}}' http://0.0.0.0:8000/retrieve
```

or through Python with the above body as follows:

```python
import requests
response = requests.post("http://0.0.0.0:8000/retrieve", json=body)
```

This endpoint/route returns a list of messages, organized by `session_id`, `time`, `role`, and `message`, e.g.

```
[
    {'session_id':101, 'time':0, 'role':'interviewer', 'message':'Hello', ...}
    {'session_id':101, 'time':1, 'role':'respondent', 'message':'World', ...}
    ...
]
```

Similarly, having run your experiments serverless on AWS, you can then download all sessions using the helper Python script `serverless-retrieve.py` which returns the above as a CSV from a given DynamoDB table, e.g.

```bash
python serverless-retrieve.py --table_name=interview-sessions --output_path=PATH_TO_DATA.csv
```


### transcribe

TODO: Explain user access to this route.


## App Structure

```
└── app/
    ├── app.py
    ├── parameters.py
    ├── lambda.py
    ├── requirements.py
    ├── tests.py
    ├── core/    
    ├───── logic.py
    ├───── agent.py
    ├───── manager.py
    ├───── auxiliary.py    
    ├── database/    
    ├───── manager.py
    ├───── postgres.py
    ├───── dynamo.py
    ├───── redis.py
    ├── setup/    
    ├───── decorators.py
    ├───── log.py
    ├── templates/    
    ├───── chat.html    
```


### app.py

All app API calls set up here.

### tests.py

All API tests live here.

### parameters.py

Contains the interview-specific guidelines and parameters. *Update or create your own LLM prompts here!*

### lambda.py

AWS Lambda interface lives here.

### requirements.txt

AWS Lambda requirements live here.

### core/logic.py

Endpoint responses are processed here.

### core/agent.py

AI-interviewer (GPT integration) lives here.

### core/manager.py

The interview manager processes run through here.

### core/auxiliary.py

This file contains additional functions useful to the core logic.

### database/manager.py

Backend is routed through here to PostgreSQL, Dynamo, or Redis as currently supported.

### core/dynamo.py

DynamoDB backend database integration.

### core/redis.py

Redis backend database integration.

### core/postgres.py

PostgreSQL backend database integration.

### templates/html.py

This file the HTML landing page users see and interact with. *Update the HTML or Javascript to reflect personal taste!*


## Licensing 

This code is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Commercial use, including applications in business or for-profit ventures, is strictly prohibited without prior written permission. For inquiries about commercial licenses, please contact [Felix Chopra](f.chopra@fs.de).
