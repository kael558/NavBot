#!/usr/bin/env python3
#
# natbot.py
#
# Set OPENAI_API_KEY to your API key, and then run this from a terminal.
#

import queue
import time
from sys import argv, exit
import openai
import os

from dotenv import load_dotenv

from crawler import Crawler
from IO.inputs import Voice
from IO.outputs import Audio
from prompts import question_objective_prompt_template, objective_prompt_template, command_prompt_template, \
    command_template

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

        self._input_queue = queue.Queue()  # Input from users
        self._output_queue = queue.Queue()  # Output to users

        self.chat_history = ""
        self.commands = []
        self.objective = None

        self._inputs = {"Voice": Voice(self._settings, self._input_queue)}
        self._outputs = {"Audio": Audio(self._settings, self._output_queue)}

    def toggle_input(self, input_name: str):
        if input_name in self._inputs:
            self._inputs[input_name].toggle()
        else:
            print(f"Input {input_name} not found.")

    def toggle_output(self, output_name: str):
        if output_name in self._outputs:
            self._outputs[output_name].toggle()
        else:
            print(f"Output {output_name} not found.")

    def receive_input(self, block: bool):
        if self._input_queue.empty():
            return None

        res = self._input_queue.get(block=block)
        self.chat_history += "User: " + res + "\n"
        return res

    def send_output(self, text: str):
        self.chat_history += "NavBot: " + text + "\n"
        self._output_queue.put(text)

    def get_command(self, objective: str, elements_of_interest: str, page_description):
        # chat history
        # current web desc
        # current web url
        # url tree (list of urls)

        prompt = command_template(
            browser_content=elements_of_interest,
            page_description=page_description,
            url=self._crawler.get_current_url(),
            previous_command=self._crawler.get_previous_command(),
        )

        response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0.5, best_of=10, n=3,
                                            max_tokens=50)
        return response.choices[0].text

        pass

    def handle_command(self, command):
        """
        run the command
        update the url tree, web desc, and web url
        """
        self._crawler.run_command(command)

    def get_objective(self, user_response):
        prompt = objective_prompt_template.format(
            chat_history=self.chat_history,
        )

        return openai.Completion.create(model="text-davinci-003",
                                        prompt=prompt,
                                        temperature=0.5,
                                        best_of=10,
                                        n=3,
                                        max_tokens=50)

    def run(self):
        response = "Hi, I'm NavBot. I will be your guide on the web. How can I help you today?"
        self._output_queue.put(response)
        user_response = self.receive_input(block=True)
        self.objective = get_objective(user_response)
        try:
            while True:
                # Generate a question or generate a command
                """

                1. user input
                2. use vector db to check if input wants to change settings
                3. given the chat history, generate a question or a command (could be nothing)
     
                1. if ask user question
                2. generate response with question and web desc, send the response to the user
                3. wait for their input

                4. if no question
                5. get objective of 
                2. generate response with command and web desc and send response to user
                3. send the command to the handler and crawl the new page
                4. check if the user has said anything
                
                
                1. if the user has said something, then clear the output queue
                2. and go back to step 1 Question or command
                """

                # Check if latest user response wants to change settings

                # Generate question or command, given chat history, current web desc, current web url, url tree
                question, command = self.get_question_or_command()

                # If question, wait for user input
                if question:
                    self.send_output(question)
                    user_response = self.receive_input(block=True)
                # If command, send command to handler and crawl the new page
                elif command:
                    self.send_output(command)
                    self.handle_command(command)

                # Check if user has said anything
                res = self.receive_input(block=False)
                if res is not None:
                    # Clear the output queue
                    while not self._output_queue.empty():
                        self._output_queue.get()


        except KeyboardInterrupt:
            print("\n[!] Ctrl+C detected, exiting gracefully.")
            exit(0)


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
