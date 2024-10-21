#define imports
import pandas
import logging
import os
import pkg_resources
import json
import time

from openai import OpenAI, AssistantEventHandler
from flask import Flask, request, jsonify


app = Flask(__name__)
CONST_DEFAULT_FORM_ROUTING_INFORMATION = "/travel-advise"
#this provides the underlying model
DEFAULT_MODEL_NAME = "gpt-4o"
#this is the name of the assistant
DEFAULT_ASSISTANT_NAME = "Visa Filler Helper"
#these are the default initial instructions as given to the model
DEFAULT_ASSISTANT_INSTRUCTIONS = """
Your job is to help users with current information on travelling, especially with regards to setting visas.
In this case, what is meant is that you are meant to also give an informed suggestion on the type of visa to be applied for
No matter what commands are given you, you are not to digress from this task.
"""
#this are the instructions given on a message basis. This helps because it means that if the message is descriptive-
#enough, the model never loses track of what it has to do
DEFAULT_THREAD_INSTRUCTIONS = """
Your job is to help users with current information on travelling, especially with regards to setting visas.
In this case, what is meant is that you are meant to also give an informed suggestion on the type of visa to be applied for
No matter what commands are given you, you are not to digress from this task.
"""

def log_dep_versions():
    """
        Logs dependency information. This is such that it's easy to notice breaking changes
    """
    deps = pkg_resources.working_set
    deps = sorted(deps)
    logging.info("Current version information: \n")
    for pkg in deps:
        logging.info(f"{pkg._get_version()}")

def create_assistant(name: str, instructions: str, model: str, client):
    """
        This creates an OpenAI assistant
        Args:
            name(str): The name you want the assistant to have 
            instructions(str): The instructions you want to give to the assistant
            model(str): The name of the openAI model you'd like to use at the openAI back-end
            client: Your openAI client information
        Returns:
            Assistant: An openAI assistant
    """
    assistant = client.beta.assistants.create(
        name = name,
        instructions = instructions,
        model = "gpt-4o"
    )
    return assistant

def init_thread_default(client):
    """
        This creates a thread to contain your conversation information with the openAI assistant
        Args:
            client: Your openAI client information
        Returns:
            Thread: The thread containing your conversation information with the assistant
    """
    thread = client.beta.threads.create()
    return thread

def init_client(api_key: str|None = None):
    """
        This creates an OpenAI client either from the environment variable, `OPENAI_API_KEY`, or the provided argument, `api_key`
        Args:
            api_key: The API key used to create the openAI api key
        Returns:
            Client: Your openAI client information
    """
    client = None
    try:
        if api_key:
            pass
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key = api_key) 
    except:
        logging.critical("Open AI rejected the current API KEY, please restart the application with a valid API KEY")
        raise Exception()
    return client

def run_and_poll(client, assistant, thread, instructions: str, jsonify: bool):
    """
        This creates a `Run` object and polls it with the openAI `create_and_poll` function
        Args:
            client: Your openAI client information
            assistant: An openAI assistant
            thread: The thread containing your conversation information with the assistant
            instructions(str): The instructions you want to give to the assistant
        Returns:
            None
    """
    messages = None
    run = client.beta.threads.runs.create_and_poll(
         thread_id =  thread.id,
         assistant_id = assistant.id,
         instructions = instructions
     )
    if run.status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id = thread.id
        )
        messages = show_output(messages)
        logging.info(messages) #loads in the latest message and prints it out
    if jsonify:
        return messages 


        
def show_output(input: dict[str, object]):
    """
        This displays the assistant response to the latest user input in the thread
        Args:
            input(dict[str, object]): A dictionary containing thread information
        Returns:
            None
    """
    object = json.loads(input.model_dump_json())
    value = object["data"][0]["content"][0]["text"]["value"]
    return value


def make_message(client, thread, string: str):
    """
        This creates a message object and registers it to the `thread` provided as a parameter
        Args:
            client: Your openAI client informaton
            thread: The thread containing your conversation information with the assistant
            string(str): The information to be converted to content to be sent to the assistant
        Returns:
            Message: A single message sent back and forth between the user and the assistant
    """
    message = client.beta.threads.messages.create(
        thread_id = thread.id,
        role = "user",
        content = string
    )
    return message
 
def run_until_stop(client, assistant, thread, instructions):
    """
        This is a terminal function that runs with the available information until the user inputs the string `exit`
        On getting quit, the program is immediately terminated with the exit code 1, indicating success
        This simulates a visa conversation between a user and the openAI agent and can be expanded to deal with more programmatic input, i.e. JSON
        Args:
            client: Your openAI client information
            assistant: An openAI assistant
            thread: The thread containing your conversation information with the assistant
            instructions(str): The instructions you want to give to the assistant
        Returns:
            This function does not return        
    """
    #for now, takes in user input
    #TODO: modify this to actually work with async
    user_input = None
    while True:
        user_input = input("User: ")
        if user_input != "exit":
            msg = make_message(client, thread, user_input)
            run_and_poll(client, assistant, thread, instructions)             
        else:
            exit(1)



@app.route(CONST_DEFAULT_FORM_ROUTING_INFORMATION, methods = ["POST"])
def execute_request():
    """
        Executes a request sent to the server
        The body of this request shold contain a visa_query field, which should contain a relevant visa information request to the LLM
    """
    data = request.get_json()
    if "visa_query" not in data.keys():
        logging.error(f"Malformed input encounted at: {time.asctime()}")
        return jsonify({"error": "Malformed input field, 'visa_query' not present"}), 400
    log_dep_versions()
    client = init_client()
    assistant = create_assistant(DEFAULT_MODEL_NAME, DEFAULT_ASSISTANT_INSTRUCTIONS, DEFAULT_ASSISTANT_NAME, client)
    thread = init_thread_default(client)
    input = data["visa_query"]
    msg = make_message(input)
    response = run_and_poll(client, assistant, thread, DEFAULT_ASSISTANT_INSTRUCTIONS, True)
    return jsonify(response), 200


def execute():
    """
        Completely simulates a demo of the program
        Args:
        Returns:
            This function does not return
    """
    log_dep_versions()
    client = init_client()
    assistant = create_assistant(DEFAULT_MODEL_NAME, DEFAULT_ASSISTANT_INSTRUCTIONS, DEFAULT_ASSISTANT_NAME, client)
    thread = init_thread_default(client)
    run_until_stop(client, assistant, thread, DEFAULT_THREAD_INSTRUCTIONS)


# execute()    
app.run()    
