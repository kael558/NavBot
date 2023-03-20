import os
import queue
import threading
import time
import winsound
import openai
import speech_recognition as sr
from dotenv import load_dotenv
import playsound

from IO.inputs.input import Input
import io

from settings.settings import Settings
import keyboard


class NamedBufferedReader(io.BufferedReader):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class Voice(Input):
    _instance = None

    def __new__(cls, queue: queue.Queue, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings, output_queue: queue.Queue):
        super().__init__(output_queue)
        openai.api_key = os.environ.get("OPENAI_API_KEY")

        self.settings = settings

        # Thread-safe queue to transcribe audio segments
        self.transcribe_queue = queue.Queue()

    def _start(self):
        listening_thread = threading.Thread(target=self.listen)
        listening_thread.start()

    def _stop(self):
        self.transcribe_queue.put(None)

    def listen(self):
        r = sr.Recognizer()

        while not self._stop_event.is_set():
            try:
                # use the microphone as source for input.
                with sr.Microphone() as source:

                    # wait for a second to let the recognizer
                    # adjust the energy threshold based on
                    # the surrounding noise level
                    r.adjust_for_ambient_noise(source, duration=0.5)

                    if self.settings.push_to_talk:
                        keyboard.wait(self.settings.push_to_talk_key, suppress=True)

                    #playsound.playsound("mic_on.wav", block=True)
                    # listens for the user's input
                    audio = r.listen(source)

                    # Put audio segment in queue
                    self.transcribe_queue.put(audio.get_wav_data())
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
            except sr.UnknownValueError:
                print("unknown error occurred")
            except sr.WaitTimeoutError:
                print("Timeout")
                self.transcribe_queue.put(None)
                break

    def _input(self):
        # Read a segment from the queue
        audio_file_wav_data = self.transcribe_queue.get(block=True)
        if audio_file_wav_data is None:
            return None

        byte_stream = io.BytesIO(audio_file_wav_data)
        audio_file = NamedBufferedReader(f"audio_file.wav", raw=byte_stream)
        # audio_file = open(path_to_audio_file, "rb")
        if self.settings.language != "English":
            transcript = openai.Audio.translate("whisper-1", audio_file)
        else:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        audio_file.close()

        text = str(transcript.text).strip()
        if not isEnglish(text) or text.startswith("Thank") or text == ". . . . .":
            return None

        if self.settings.keyword_detection:
            if text.startswith(self.settings.keyword):
                text = text[len(self.settings.keyword):]
            else:
                return None

        print("Transcript: " + text)
        return text

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
