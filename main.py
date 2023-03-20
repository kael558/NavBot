#!/usr/bin/env python3
#
# natbot.py
#
# Set OPENAI_API_KEY to your API key, and then run this from a terminal.
#
import multiprocessing
import nltk
import playsound
import requests

from IO.inputs.keyboard import Keyboard

# Download the punkt tokenizer if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

import os
import queue
import re
import threading
from sys import argv
from threading import Thread
from typing import Optional, Tuple, Any, List

import openai
import pyttsx3
from dotenv import load_dotenv

from IO.inputs import Voice
from IO.inputs.input import Input
from IO.outputs.output import Output
from crawler import Crawler
from prompts import command_template, objective_or_question_template, response_template
from settings.settings import Settings

quiet = False
if len(argv) >= 2:
    if argv[1] == '-q' or argv[1] == '--quiet':
        quiet = True
        print(
            "Running in quiet mode (HTML and other content hidden); \n"
            + "exercise caution when running suggested commands."
        )


class TextToSpeech(threading.Thread):
    def __init__(self):
        super().__init__()

        self.engine = pyttsx3.init(driverName='sapi5')
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('rate', 120)
        self.engine.setProperty('voice', voices[1].id)
        self.queue = queue.Queue()

    def say(self, text):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            self.queue.put(sentence)

    def set_talking_speed(self, speed):
        if speed == "Fast":
            self.engine.setProperty('rate', 150)
        elif speed == "Slow":
            self.engine.setProperty('rate', 100)
        else:
            self.engine.setProperty('rate', 125)

    def set_voice(self, voice):
        voices = self.engine.getProperty('voices')
        if voice == "Male":
            self.engine.setProperty('voice', voices[0].id)
        else:
            self.engine.setProperty('voice', voices[1].id)
        print("set voice to " + voice + " -> "+ str(self.engine.getProperty('voice')))

    def stop(self):
        while not self.queue.empty():
            self.queue.get()

    def run(self):
        while True:
            text = self.queue.get(block=True)
            if not text:
                break

            self.engine.say(text)
            self.engine.startLoop(False)
            self.engine.iterate()
            self.engine.endLoop()


    def exit(self):
        self.queue.put(None)


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def __str__(self):
        return f"{self.role}: {self.content}"

def check_for_settings_change(settings: Settings, user_response) -> Optional[Tuple[str, str, Any]]:
    # Match to setting using vectordb
    # Match to setting values using vectordb
    possible_settings = {"enable push to talk", "disable push to talk",
                         "enable keyword detection", "disable keyword detection",
                         "enable verbose mode", "disable verbose mode",
                         "talk more", "talk less",
                         "change language",
                         "exit"
                         }

    setting = settings.get_setting(user_response.content)[0]
    print(setting)
    if setting[1] > 0.6:
        return None

    if setting[0] == "change language":
        setting_value = settings.get_setting_value(setting[0], user_response.content)[0]
        if setting_value[1] > 0.6:
            return None
        return setting[0], "language", setting_value[0]
    elif "man" in setting[0]:
        return setting[0], "voice", "Female" if "woman" in setting[0] else "Male"
    elif "fast" in setting[0]:
        return setting[0], "talking_speed", "Fast"
    elif "slow" in setting[0]:
        return setting[0], "talking_speed", "Slow"
    elif setting[0] == "exit":
        return setting[0], "", None
    else:
        key = "_".join(setting[0].split(" ")[1:])

        if setting[0].startswith("enable") or setting[0].startswith("talk"):
            return setting[0], key, True
        elif setting[0].startswith("disable"):
            return setting[0], key, False
    return None


def confirmed(user_response, settings: Settings):
    # match to yes/no using vectordb
    confirmation = settings.get_setting(user_response)[0]
    if confirmation[1] > 0.6:
        return None

    if confirmation[0] == "yes":
        return True

    return False


def get_properties_of_(element: str):

    elem_type = re.search(r'(?<=<)\w+(?=\s)', element).group()

    regex_pattern = r'(?<=\>)[^<>\"]+(?=<)|(?<=alt=\")[^<>\"]+(?=\")|(?<=aria-label=\")[^<>\"]+(?=\")'

    text = " ".join(re.findall(regex_pattern, element))
    if text and text != "":
        return elem_type, text

    # Hopefully the llm doesnt choose an element with no inner text or alt text l0l
    return elem_type, None


def map_command_to_msg(command: str, elements_of_interest: List[str]):
    if command == "SCROLL UP":
        return "I am scrolling up on the page to see more content."
    if command == "SCROLL DOWN":
        return "I am scrolling down on the page to see more content."
    if command.startswith("CLICK"):
        commasplit = command.split(",")
        id = commasplit[0].split(" ")[1]
        elem_type, text = get_properties_of_(elements_of_interest[int(id)])

        output = "I am clicking on a " + elem_type
        if text:
            output += " labeled as " + text + "."
        return output

    if command.startswith("TYPE"):
        spacesplit = command.split(" ")
        id = spacesplit[1]
        text = spacesplit[2:]
        text = " ".join(text)

        # Strip leading and trailing double quotes
        text = text[1:-1]
        elem_type, elem_text = get_properties_of_(elements_of_interest[int(id)])
        output = "I am typing " + text + " into the " + elem_type
        if elem_text:
            output += "labeled as " + elem_text

        if command.startswith("TYPESUBMIT"):
            output += " and then submitting."
        return output
    if command == "FINISH":
        return "I am done navigating."
    return ""


def get_response(url: str, chat_history: List[Message], page_desc: str, elements_of_interest: str, settings: Settings):
    prompt = response_template(
        url=url,
        chat_history="\n".join(map(str, chat_history)),
        page_desc=page_desc,
        elements_of_interest=elements_of_interest,
        verbosity=settings.verbosity_length
    )

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n", "User:"]
    )
    return response.choices[0].text



def receive_input(input_queue: queue, chat_history: List[Message], output_thread: TextToSpeech, block: bool) -> \
        Optional[Message]:

    try:
        user_input_text = input_queue.get(block=block)
    except queue.Empty:
        return None

    if user_input_text is None:
        return None

    if user_input_text == "" or user_input_text == ". . . . .":
        return None

    msg = Message("user", user_input_text)
    if len(chat_history) > 4:
        chat_history.pop(0)
    chat_history.append(msg)
    output_thread.stop()
    return msg


def send_output(text: str, chat_history: List[Message], output_thread: TextToSpeech):
    output_thread.say(text)
    if len(chat_history) > 4:
        chat_history.pop(0)
    chat_history.append(Message("NavBot", text))


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
                                        max_tokens=50,
                                        timeout=20)
    return response.choices[0].text


def get_objective_or_question(chat_history):
    prompt = objective_or_question_template(
        chat_history="\n".join(map(str, chat_history)),
    )

    response = openai.Completion.create(model="text-davinci-003",
                                        prompt=prompt,
                                        temperature=0.5,
                                        best_of=10,
                                        n=1,
                                        max_tokens=50,
                                        timeout=20)
    return response.choices[0].text


def test_voice():
    load_dotenv()
    from settings.settings import Settings

    output_queue = queue.Queue()
    settings = Settings()
    v = Voice(settings, output_queue)
    v.start()
    input("Press enter to stop")
    v.stop()


def run():
    load_dotenv()
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    crawler = Crawler()
    crawler.go_to_page("google.com")
    settings = Settings()

    input_queue = queue.Queue()  # Input from users
    output_thread = TextToSpeech()  # Output to users
    output_thread.start()

    i = Keyboard(input_queue)
    i.start()
    #i = Voice(settings, input_queue)
    #i.start()

    chat_history = []

    response = "Hi, I'm NavBot. I will be your guide on the web. How can I help you today?"
    send_output(response, chat_history, output_thread)

    try:
        while True:
            # Get user input
            user_response = receive_input(input_queue, chat_history, output_thread, block=True)
            settings_change = check_for_settings_change(settings, user_response)
            print("Settings change: " + str(settings_change))
            if settings_change is not None:
                if settings_change[0] == "exit":
                    break

                # Ask the user to confirm the settings change
                if settings_change[1] == "language":
                    output = "Shall I change my language to " + settings_change[2] + "?"
                else:
                    output = "Shall I " + settings_change[0] + "?"

                send_output(output, chat_history, output_thread)
                settings_change_confirmation = receive_input(input_queue, chat_history, output_thread, block=True)

                if confirmed(settings_change_confirmation.content, settings):
                    # Change the settings
                    settings.change_setting(settings_change)
                    if settings_change[1] == "voice":
                        output_thread.set_voice(settings_change[2])
                    elif settings_change[1] == "talking_speed":
                        output_thread.set_talking_speed(settings_change[2])

                    response = "Great. I have changed the settings. What would you like to do next?"
                    send_output(response, chat_history, output_thread)
                    continue
                else:
                    response = "Okay. I will not change the settings. What would you like to do next?"
                    send_output(response, chat_history, output_thread)
                    continue
            try:
                send_output("I am figuring out the best way to handle your request. Please give me a second.", chat_history, output_thread)
                objective_or_question = get_objective_or_question(chat_history)

                print("Objective or Question: " + objective_or_question)
                while objective_or_question != "The user does not appear to have an objective or question.":
                    # Generate command, given objective, current web desc, current web url
                    elements_of_interest, page_desc = crawler.get_page_contents(settings.verbosity_length)
                    output_thread.stop()

                    if "google" in crawler.get_current_url():
                        send_output("You are currently on Google.", chat_history, output_thread)
                    else:
                        send_output(page_desc, chat_history, output_thread)

                    #print("\n".join(elements_of_interest))
                    print(page_desc)

                    if objective_or_question.endswith("?"):
                        output_thread.stop()
                        send_output("I am finding an answer for your question.", chat_history, output_thread)
                        question = objective_or_question
                        # Answer the question
                        chat_history.append(Message("User", question))
                        response = get_response(crawler.get_current_url(), chat_history, page_desc,
                                                "\n".join(elements_of_interest), settings)
                        output_thread.stop()
                        send_output(response, chat_history, output_thread)
                        break
                    else:
                        output_thread.stop()
                        send_output("I am finding an appropriate command for your objective.", chat_history, output_thread)
                        objective = objective_or_question
                        #print("Objective: " + objective)
                        command = get_command(crawler, objective, "\n".join(elements_of_interest)[:1500],
                                              page_desc[:1000])
                        command = command.strip()
                        #print(command)
                        if settings.verbose_mode:
                            # Make response explaining what the bot is doing and send it to the user
                            output_thread.stop()
                            send_output(map_command_to_msg(command, elements_of_interest), chat_history,
                                        output_thread)

                        if command == "FINISH":
                            break

                        # Run command
                        crawler.run_command(command)


                        # Check if user has said anything
                        optional_user_input = receive_input(input_queue, chat_history, output_thread, block=False)

                        if optional_user_input is not None:
                            # Update the objective
                            objective_or_question = get_objective_or_question(chat_history)
            except requests.exceptions.Timeout:
                send_output(
                    "I'm sorry, I'm having trouble connecting to the large language model. Please try again later.",
                    chat_history, output_thread)

            # Given web description, given options for user. Summarize them and ask user what to do next
            send_output("What would you like to do next?", chat_history, output_thread)
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected, exiting gracefully.")
    crawler.close()
    i.stop()
    output_thread.exit()
    send_output("Thank you for using NavBot. Goodbye!", chat_history, output_thread)


if __name__ == "__main__":
    run()

