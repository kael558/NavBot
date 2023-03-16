#!/usr/bin/env python3
#
# natbot.py
#
# Set OPENAI_API_KEY to your API key, and then run this from a terminal.
#

import queue
import time
from sys import argv, exit, platform
import openai
import os

from dotenv import load_dotenv

from crawler import Crawler
from inputs import Voice
from prompts import prompt_template
from settings import Settings

quiet = False
if len(argv) >= 2:
    if argv[1] == '-q' or argv[1] == '--quiet':
        quiet = True
        print(
            "Running in quiet mode (HTML and other content hidden); \n"
            + "exercise caution when running suggested commands."
        )

class NavBot:
    def __init__(self) -> None:
        self._crawler = Crawler()
        self._settings = Settings()
        self._output_queue = queue.Queue()


        self._voice = Voice(self._settings)
        self._voice.set_output_queue(self)


def send_command():
    pass


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
        prompt = prompt_template
        prompt = prompt.replace("$objective", objective)
        prompt = prompt.replace("$url", url[:100])
        prompt = prompt.replace("$previous_command", previous_command)
        prompt = prompt.replace("$browser_content", browser_content[:4500])
        prompt = prompt.replace("$page_desc", page_desc[:4500])
        response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0.5, best_of=10, n=3,
                                            max_tokens=50)
        return response.choices[0].text

    def run_cmd(cmd):
        cmd = cmd.split("\n")[0]

        if cmd.startswith("SCROLL UP"):
            _crawler.scroll("up")
        elif cmd.startswith("SCROLL DOWN"):
            _crawler.scroll("down")
        elif cmd.startswith("CLICK"):
            commasplit = cmd.split(",")
            id = commasplit[0].split(" ")[1]
            _crawler.click(id)
        elif cmd.startswith("TYPE"):
            spacesplit = cmd.split(" ")
            id = spacesplit[1]
            text = spacesplit[2:]
            text = " ".join(text)
            # Strip leading and trailing double quotes
            text = text[1:-1]

            if cmd.startswith("TYPESUBMIT"):
                text += '\n'
            _crawler.type(id, text)

        time.sleep(2)

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
