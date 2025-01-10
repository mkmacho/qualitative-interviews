# Code for "Conducting Qualitative Interviews with AI" 

This codebase allows researchers to conduct qualitative interviews with human subjects by delegating the task of interviewing to an AI-interviewer. We support three options: (1) running the application locally on your own machine for testing and development; (2) deploying the application as a Flask app on your own server; (3) deploying the application as a serverless Lambda function on Amazon AWS. Option 2 and 3 are for eventual large-scale data collection. We explain the setup steps below. 

The application requires access to a large language model (LLM). The code currently operates with OpenAI's API. You can obtain API keys [here](https://platform.openai.com/).


## Paper and citation

The paper is available here: [https://dx.doi.org/10.2139/ssrn.4583756](https://dx.doi.org/10.2139/ssrn.4583756).


This code is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Commercial use, including applications in business or for-profit ventures, is strictly prohibited without prior written permission. Uses and distribution should cite:

```
Chopra, Felix and Haaland, Ingar, Conducting Qualitative Interviews with AI (2023). CESifo Working Paper No. 10666, Available at SSRN: https://ssrn.com/abstract=4583756 or http://dx.doi.org/10.2139/ssrn.4583756
```
or use the suggested Bibtex entry:
```
@article{ChopraHaaland2023,
  title={Conducting Qualitative Interviews with AI},
  author={Chopra, Felix and Haaland, Ingar},
  journal={CESifo Working PAper No. 10666},
  url={https://ssrn.com/abstract=4583756},
  year={2023}
}
```

For inquiries about commercial licenses, please contact [Felix Chopra](f.chopra@fs.de). 


## Table of Contents
* [Option 1: Local testing](#option-1-local-testing)
    * [Docker](#docker)
    * [Manually](#manual)
* [Option 2: Deploy as Flask app](#option-2-deploy-as-flask-app)
* [Option 3: Deploy on AWS](#option-3-deploy-on-aws)
* [Integrating with Qualtrics](#integrating-with-qualtrics)
* [Parameters of the app](#parameters-of-the-app)
* [How to interact with the app](#how-to-interact-with-the-app)


## Option 1: Local testing

This option is ideal for testing the app before data collection and making changes to the code or prompts to better fit your research setting. We explain how this is done using Docker as well as manually.

Note that regardless of how you build and test, the application will require an OpenAI key. You can supply this by simply changing line 5 of `parameters.py` from:
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
```
to 
```python
OPENAI_API_KEY = "MY_OPENAI_API_KEY"
```


### Docker

The cleanest way to then run the application -- locally or remotely -- is through a [Docker](https://docs.docker.com/engine/install/) container. You can easily build a Docker image containing only the necessary packages in a contained environment from whatever operating system. You will also need to have Git [installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).


**Step 1**: Clone the project from GitHub and navigate into the repo:

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews
```

**Step 2**: Build a Docker image (e.g. `interviews`) and run a container:

To build and then run a container in the background you can add the `--detach` flag. We are publishing the `8000` port to forward requests and mounting (i.e. sharing) the filesystem within the `/app` subdirectory such to see outputs directly. This can be done by running:

```bash
docker build --tag interviews .
docker run --detach --publish 8000:80 --volume $(pwd)/app:/app interviews
```

Or, alternatively, build and run using the template `docker-compose` YAML by running:

```bash
docker compose up --build --detach
```

You can now make requests to your local host listening on port `8000` (e.g. `localhost:8000`, `0.0.0.0:8000`, or `127.0.0.1:8000`). Running in the command line `curl http://127.0.0.1:8000/` should return text `Running!` to confirm the application is successfully up and running.


**Comments**: 
- You can stop (e.g. `docker stop`) and remove (i.e. `docker rm`) containers, or do the same using the compose file (e.g. `docker compose down`). If you make local changes to your code, you can restart the container to reflect these changes using `docker restart` or `docker compose restart`.


### Manual

If you decide against Docker, you will need to have (or download) Python. We recommend stable version 3.12. You can install Python from [here](https://www.python.org/downloads). You will also need to have Git [installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

**Optional Step 0:** Create a virtual environment, e.g. `interviews-env`, and activate it, so as to install necessary packages in a clean environment, guaranteeing no clashing dependencies. In your command-line terminal run:

```bash
python -m venv interviews-env
cd interviews-env
source bin/activate
```

**Step 1:** Clone this project from Github and install the necessary packages defined in the repository's `local_requirements.txt` file using `pip`:

```bash
git clone https://github.com/mkmacho/qualitative-interviews.git
cd qualitative-interviews

pip install -r local_requirements.txt
```

**Step 2:** Now start a *development* (Werkzeug) server to host your application by simply running:

```bash
python app/app.py
```

As you can see in `app.py`, we are listening on port `8000` so you can now make requests to your local host (e.g. `localhost`, `0.0.0.0`, or `127.0.0.1`). Running in the command line `curl http://127.0.0.1:8000/` should return text `Running!` to confirm the application is successfully up and running.


**Comments**: 
- Changes to your local code will automatically restart the server, reflecting your changes. You can stop the server by entering `control-C` on your command line.


## Option 2: Deploy as Flask app 

This option is for when you are ready to collect data and want to deploy your application on a production server. The benefit of this option is that you can manage the server and all aspects of your code, logs, and application service directly. We recommend that you use Docker for this, so again on your remote server make sure Docker is [installed](https://docs.docker.com/engine/install/).

**Step 1:** Copy your current codebase, including changes you have made, to your remote server.

In Linux, you can securely transfer files between servers using Secure Shell (SSH) protocol with `scp`, e.g.
```bash
scp -r <LOCAL_DIRECTORY> <REMOTE_DIRECTORY>
```

**Step 2:** Once you have your codebase on your remote server, you can use Docker just as you did locally, e.g.
```bash
docker compose up --build --detach
```

Your remote machine will now forward requests to port `8000` onto port `80` on which the Docker container is listening, thereby processing requests to `<REMOTE_HOST>:8000/`. 


## Option 3: Deploy on AWS

This option is for when you are ready to collect data and want to run your application *without a dedicated server*. The benefit of this option is that AWS abstracts the deployment and management details at a low price. We have had good experiences with this setup.

**Step 1:** To run the application serverless on AWS you will need to create an AWS account if you do not yet have one, and download (public and secret) access keys.

**Step 2:** With your command line interface keys, simply run: 

```bash
./serverless-setup.sh <AWS_PUBLIC_ACCESS_KEY> <AWS_SECRET_ACCESS_KEY> <AWS_REGION> <S3_BUCKET>
```
supplying your keys, your region (e.g. `eu-north-1`), and your chosen bucket name (e.g. `my-bucket`) which will configure your command line AWS credentials, create an AWS storage bucket where build template will be stored, and create an AWS Dynamo database table (by default named `interview-sessions`) to persistently store interviews sessions (in the Cloud). This has to be run just once!

**Step 3:** Deploy the Lambda function with OpenAI access and expose a public endpoint to which you can make requests: 

```bash 
./serverless-deploy.sh <S3_BUCKET>
```

supplying the same AWS S3 bucket name provided above (e.g. `my-bucket`).

Note that this script will return the following information:
```bash
Key             InterviewApi                                                                                      
Description     API Gateway endpoint URL for function
Value           https://<SOME_AWS_ID>.execute-api.<AWS_REGION>.amazonaws.com/Prod/
```

Save this final value, it is the public endpoint for your Lambda function. There is no endpoint suffix for this serverless function so requests will go straight to this URL.

**Comments:** 
- You can assert the function is up and working by making a `curl` call from the command-line, e.g.
```bash
curl -X POST \
    -d '{"route":"next", "payload":{"session_id":"test","interview_id":"STOCK_MARKET","user_message":"test"}}' \
    https://<SOME_AWS_ID>.execute-api.<AWS_REGION>.amazonaws.com/Prod/
```
- If you want to log information from the application or debug your code, you can look at AWS CloudWatch.


## Integrating with Qualtrics

Once you have deployed your app, you can integrate it (using the public endpoint) directly within your Qualtrics survey setup. 

**Step 1:** In Qualtrics, add embedded variables `user_id`, `interview_id` and `interview_endpoint`. `user_id` should identify your respondent.  `interview_id` should identify the parameter settings of your AI interviewer (see below, e.g. `STOCK_MARKET`). `interview_endpoint` is the public endpoint of your hosted application.

**Step 2:** Create a `Text/Graphic` question in your survey. The folders `Qualtrics` contain HTML and JS files. Copy the content into the HTML and JS fields of the `Text/Graphic` question.

**Step 3:** Test your low-cost, scalable survey!


## Parameters of the app

To customize the structure of the interviews (e.g. the topics covered, the duration, the LLM prompts, etc.) simply edit the `parameters.py` file. Detailed explanations of the variables can be found direclty in the file.


## How to interact with the app

There are three main API endpoints of the app: `/next`, `/transcribe` and `/retrieve`.

### next

The main API `/next` is to continue (or begin, if not started) an interview. This is done by making an HTTP POST request with the following body:

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

For example, we can test this API localy using `curl` at the `http://127.0.0.1:8000/next` URL:

```bash
curl -X POST -d '{"route":"next", "payload": {"session_id": "TEST-SESSION-123", "interview_id": "STOCK_MARKET", "user_message":"I dont have disposable income to invest"} }' http://127.0.0.1:8000/next
```

where you can replace the URL with the host, port, endpoint URL exposed on your remote server or through AWS serverless.

You can also test the `/next` endpoint through Python with the above body as follows:

```python
import requests
response = requests.post("http://127.0.0.1:8000/next", json=body)
```

or similarly through [Postman](https://www.postman.com/api-platform/api-testing/).


#### Interface

We can make additionally test the application interface non-programmatically when built using Flask locally or on a remote server.

Given the host and host port our application is serving up, plus the previously specified `interview_id` and a unique `session_id` we can simply open up a browser to this URL (making a GET request to begin the interview) and walk through an interview.

For example, having exposed localhost port 8000, we can navigate to `http://127.0.0.1:8000/STOCK_MARKET/TEST-SESSION-123` on your browser of choice. This will open a web page displaying the `interview_id`-specified first question of the interview (as specified in the `parameters.py` file) and prompt the user to answer this question. Each subsequent response by the user will be processed by the AI-interviewer and the web page will dynamically update to show this ongoing chat. 


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
curl -X POST -d '{"route":"retrieve", "payload": {"sessions": ["TEST-SESSION-123", "TEST-SESSION-456"]}}' http://127.0.0.1:8000/retrieve
```

or through Python with the above body as follows:

```python
import requests
response = requests.post("http://127.0.0.1:8000/retrieve", json=body)
```

This endpoint/route returns a list of messages, organized by `session_id`, `time`, `role`, and `message`, e.g.

```
[
    {'session_id':101, 'type':'question', 'message':'Hello?', 'order':0, ...},
    {'session_id':101, 'type':'answer', 'message':'World','order':1, ...},
    {'session_id':101, 'type':'question', 'message':'Why?','order':2, ...},
    {'session_id':101, 'type':'answer', 'message':'Because','order':3, ...},
    ...
]
```

Similarly, having run your experiments serverless on AWS, you can then download all sessions using the helper Python script `serverless-retrieve.py` which returns the above as a CSV from a given DynamoDB table, e.g.

```bash
python serverless-retrieve.py --table_name=interview-sessions --output_path=DESIRED_PATH_TO_DATA.csv
```
