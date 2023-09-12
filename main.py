import json
from fastapi import FastAPI
import openai
import os
from dotenv import load_dotenv
from collections import defaultdict
import youtube
from typing import List
import time

load_dotenv()
openai.api_key = os.environ.get("OPENAI_EXSMART")
app = FastAPI()
youtube_url_base = "https://www.youtube.com"


@app.get("/")
def home():
    return "Welcome to ExSmart"


# with open("context-prompt.txt", "r") as file:
#     system_prompts = [
#         {"role": "system", "content": line.strip()} for line in file.readlines()
#     ]

system_prompt = f"""You are a happy assistant whose name is Chatty that puts a positive spin on everything. 
You are a good and helpful assistant. Make stept-by-step comprehensive roadmaps for users when needed. Do not 
answer any question that not related to self growth."""

functions = [
    {
        "name": "create_roadmap",
        "description": "This function creates a setp-by-step roadmap for user to achive to be good at the field or proffession he/she wants.",
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {
                                "type": "integer",
                                "description": f"""This is the number or the index or the order of the step.""",
                            },
                            "step_title": {
                                "type": "string",
                                "description": f"""This is title for the current step.""",
                            },
                            "step_description": {
                                "type": "string",
                                "description": f"""This is the description for the step.""",
                            },
                            "youtube_search_string": {
                                "type": "string",
                                "description": f"""This string is used in youtube search to find sources for this exact step""",
                            },
                        },
                        "required": ["step_number", "step_title", "step_description"],
                    },
                }
            },
            "required": ["steps"],
        },
    }
]

conversations = defaultdict(list)


def generate_response(message):
    if not message.get("function_call", None):
        return message

    json_data = json.loads(message.function_call.arguments)

    for i in range(len(json_data["steps"])):
        search_response = {}

        MAX_RETRIES = 3
        TIME_DELAY = 4
        while not search_response.get("items", []) and MAX_RETRIES:
            search_response = youtube.search(
                json_data["steps"][i]["youtube_search_string"]
            )
            MAX_RETRIES -= 1
            time.sleep(TIME_DELAY)

        for j in range(len(search_response.get("items", []))):
            video_id = search_response["items"][j].get("id", {}).get("videoId", None)

            url = f"{youtube_url_base}/watch?v={video_id}"
            if not json_data["steps"][i].get("youtube_videos", None):
                json_data["steps"][i]["youtube_videos"] = []

            json_data["steps"][i]["youtube_videos"].append(url)
        # print(json_data["steps"][i], end="\n\n")

    message.function_call.arguments = json_data

    return message


def chatty(id: int, message: object):
    if not conversations[id]:
        conversations[id] = [{"role": "system", "content": system_prompt}]
        conversations[id].append(message)
    else:
        conversations[id].append(message)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=conversations[id],
        functions=functions,
        function_call="auto",
        temperature=0.8,
        stream=False,
    )

    # Here we add the response of the asisstant to the conversation
    conversations[id].append(response.choices[0].message)

    return response


@app.post("/roadmapDirectly")
def roadmap_directly(
    name: str,
    age: int,
    current_proffession: str,
    want_to_be: str,
    id: int,
    fields_of_knwld: List[str],
    fields_of_interest: List[str],
):
    name = f"My name is {name}."
    age = f"I am {age} years old."
    want_to_be = f"I want to be a very good {want_to_be}, having all the needed skills and knowledge."
    if current_proffession:
        current_proffession = f"My current profession is {current_proffession}."
    if fields_of_knwld:
        fields_of_knwld = (
            f"The fields I have knowlede in are {','.join(fields_of_knwld)}."
        )
    if fields_of_interest:
        fields_of_interest = (
            f"The fields interest me are {','.join(fields_of_interest)}."
        )

    message = {
        "role": "user",
        "content": name
        + age
        + current_proffession
        + fields_of_knwld
        + fields_of_interest
        + want_to_be,
    }

    response = chatty(id, message=message)

    return generate_response(response.choices[0].message)


@app.post("/roadmap")
def ask_chatty(id: int, content: str):
    message = {"role": "user", "content": content}

    response = chatty(id=id, message=message)

    return generate_response(response.choices[0].message)
