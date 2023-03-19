#!/usr/bin/env python3
#
# natbot.py
#
# Set OPENAI_API_KEY to your API key, and then run this from a terminal.
#

import queue
import time
from sys import argv, exit
from typing import Optional, Tuple, Any

import openai
import os

from dotenv import load_dotenv

from IO.inputs.input import Input
from IO.outputs.output import Output
from crawler import Crawler, get_page_description
from IO.inputs import Voice, __all__
from IO.outputs import Audio
from prompts import command_template, objective_template

quiet = False
if len(argv) >= 2:
    if argv[1] == '-q' or argv[1] == '--quiet':
        quiet = True
        print(
            "Running in quiet mode (HTML and other content hidden); \n"
            + "exercise caution when running suggested commands."
        )


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content




def check_for_settings_change(user_response) -> Optional[Tuple[str, Any]]:
    # Match to setting using vectordb
    # Match to setting values using vectordb

    pass


def confirmed(user_response):
    # match to yes/no using vectordb
    pass

def run():
    load_dotenv()
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    crawler = Crawler()
    settings = Settings()

    input_queue = queue.Queue()  # Input from users
    output_queue = queue.Queue()  # Output to users

    inputs = {"Voice": Voice(settings, input_queue)}
    outputs = {"Audio": Audio(settings, output_queue)}

    chat_history = []
    response = "Hi, I'm NavBot. I will be your guide on the web. How can I help you today?"
    navbot_response = Message("navbot", response)
    output_queue.put(navbot_response)

    try:
        while True:
            # Get user input
            user_response = receive_input(input_queue, block=True)
            settings_change = check_for_settings_change(user_response)
            if settings_change is not None:
                # Ask the user to confirm the settings change
                send_output(output_queue, settings_change)
                settings_change_confirmation = receive_input(input_queue, block=True)
                if confirmed(settings_change_confirmation):
                    # Change the settings
                    settings.change_setting(settings_change)
                    continue


            chat_history.append(user_response)
            objective = get_objective(chat_history)

            while True:
                # Generate command, given objective, current web desc, current web url
                elements_of_interest, page_desc = crawler.get_page_contents()
                command = get_command(crawler, objective, elements_of_interest, page_desc)

                if command == "Finish" or command.startswith("Question"):
                    # Objective is achieved, ask user what is next
                    break

                # Run command
                if settings.verbose:
                    # Map actions to string outputs
                    send_output(output_queue, command)
                crawler.run_command(command)

                # Check if user has said anything
                optional_user_input = receive_input(input_queue, block=False)
                chat_history.append(optional_user_input)

                if optional_user_input is not None:
                    # Clear the output queue
                    while not output_queue.empty():
                        output_queue.get()

                    # Update the objective
                    objective = get_objective(chat_history)
            # Given web description, given options for user. Summarize them and ask user what to do next
            send_output(output_queue, "What would you like to do next?", )




    except KeyboardInterrupt:
        send_output(output_queue, "Thank you for using NavBot. Goodbye!")
        print("\n[!] Ctrl+C detected, exiting gracefully.")
        exit(0)


def toggle_input(input_name: str, inputs: dict[str, Input]):
    if input_name in inputs:
        inputs[input_name].toggle()
    else:
        print(f"Input {input_name} not found.")


def toggle_output(output_name: str, outputs: dict[str, Output]):
    if output_name in outputs:
        outputs[output_name].toggle()
    else:
        print(f"Output {output_name} not found.")


def receive_input(input_queue: queue, block: bool) -> Optional[Message]:
    user_input = input_queue.get(block=block)
    if user_input is None:
        return None
    return Message("user", user_input)


def send_output(output_queue: queue, text: str):
    output_queue.put(text)


def get_command(crawler: Crawler, objective: str, elements_of_interest: str, page_description):
    prompt = command_template(
        objective=objective,
        browser_content=elements_of_interest,
        page_description=page_description,
        url=crawler.get_current_url(),
        previous_command=crawler.get_previous_command(),
    )

    response = openai.Completion.create(model="text-davinci-003",
                                        prompt=prompt,
                                        temperature=0.5,
                                        best_of=10,
                                        n=3,
                                        max_tokens=50)
    return response.choices[0].text


def get_objective(chat_history):
    prompt = objective_template.format(
        chat_history=chat_history,
    )

    return openai.Completion.create(model="text-davinci-003",
                                    prompt=prompt,
                                    temperature=0.5,
                                    best_of=10,
                                    n=3,
                                    max_tokens=50)


def test_voice():
    load_dotenv()
    settings = Settings()

    v = Voice(settings)
    v.start()

    input("Press enter to stop")
    v.stop()


def main():
    load_dotenv()
    _crawler = Crawler()
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    def print_help():
        print(
            "(g) to visit url\n(u) scroll up\n(d) scroll down\n(c) to click\n(t) to type\n" +
            "(h) to view commands again\n(r/enter) to run suggested command\n(o) change objective"
        )

    def get_gpt_command(objective, url, previous_command, browser_content, page_desc):
        prompt = objective
        prompt = prompt.replace("$objective", objective)
        prompt = prompt.replace("$url", url[:100])
        prompt = prompt.replace("$previous_command", previous_command)
        prompt = prompt.replace("$browser_content", browser_content[:4500])
        prompt = prompt.replace("$page_desc", page_desc[:4500])
        response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0.5, best_of=10, n=3,
                                            max_tokens=50)
        return response.choices[0].text

    settings = Settings()

    input_processing_queue = queue.Queue()
    input_type = settings.get_input_type()
    input_type.set_output_queue(input_processing_queue)

    output_type = settings.get_output_type()

    llm_response = "Hi, I'm NavBot. I will be your guide on the web. How can I help you today?"

    try:

        while True:
            output_type.output(llm_response)
            input_type.start()

            pass
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected, exiting gracefully.")
        exit(0)

    objective = "Make a reservation for 2 at 7pm at bistro vida in menlo park"
    print("\nWelcome to natbot! What is your objective?")
    i = input()
    if len(i) > 0:
        objective = i

    gpt_cmd = ""
    prev_cmd = ""
    _crawler.go_to_page("google.com")
    try:
        while True:
            browser_content = "\n".join(_crawler.get_elements_of_interest())
            browser_desc = _crawler.get_page_description()
            prev_cmd = gpt_cmd
            gpt_cmd = get_gpt_command(objective, _crawler.page.url, prev_cmd, browser_content)
            gpt_cmd = gpt_cmd.strip()

            if not quiet:
                print("URL: " + _crawler.page.url)
                print("Objective: " + objective)
                print("----------------\n" + browser_content + "\n----------------\n")
            if len(gpt_cmd) > 0:
                print("Suggested command: " + gpt_cmd)

            command = input()
            if command == "r" or command == "":
                run_cmd(gpt_cmd)
            elif command == "g":
                url = input("URL:")
                _crawler.go_to_page(url)
            elif command == "u":
                _crawler.scroll("up")
                time.sleep(1)
            elif command == "d":
                _crawler.scroll("down")
                time.sleep(1)
            elif command == "c":
                id = input("id:")
                _crawler.click(id)
                time.sleep(1)
            elif command == "t":
                id = input("id:")
                text = input("text:")
                _crawler.type(id, text)
                time.sleep(1)
            elif command == "o":
                objective = input("Objective:")
            else:
                print_help()
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected, exiting gracefully.")
        exit(0)


if __name__ == "__main__":
    load_dotenv()
    from settings import Settings

    output_queue = queue.Queue()
    settings = Settings()
    v = Voice(settings, output_queue)
    v.start()
    input("Press enter to stop")
    v.stop()
