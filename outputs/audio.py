import pyttsx3

from outputs.output import Output

class Audio(Output):
    def __init__(self):
        self.engine = pyttsx3.init()

    def output(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()

    def run(self, text):
        pass

