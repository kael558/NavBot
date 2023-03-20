import multiprocessing
import queue
import threading
import time

import nltk
import pyttsx3
import keyboard

def sayFunc(phrase):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.say(phrase)
    engine.runAndWait()

def say(phrase):
	if __name__ == "__main__":
		p = multiprocessing.Process(target=sayFunc, args=(phrase,))
		p.start()
		while p.is_alive():
			if keyboard.is_pressed('q'):
				p.terminate()
			else:
				continue
		p.join()

#say("this process is running right now")


class TextToSpeech(threading.Thread):
    def __init__(self):
        super().__init__()

        self.engine = pyttsx3.init(driverName='sapi5')
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('voice', voices[1].id)
        self.queue = queue.Queue()

    def say(self, text):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            self.queue.put(sentence)
            print("put text: " + sentence)


    def stop(self):
        while not self.queue.empty():
            self.queue.get()

    def run(self):
        while True:
            text = self.queue.get(block=True)
            if text:
                self.engine.say(text)
                self.engine.startLoop(False)
                self.engine.iterate()
                self.engine.endLoop()
            else:
                break

    def exit(self):
        self.queue.put(None)

def on_press(key):
    if key.name == 'space':
        print('Space key held down')

keyboard.on_press_key('space', on_press, suppress=True)
keyboard.wait()