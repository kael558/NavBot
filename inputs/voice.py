
import os
import queue
import threading

import openai
import speech_recognition as sr

from inputs.input import Input


class Voice(Input):
    def __init__(self, settings):
        openai.api_key = os.environ.get("OPENAI_API_KEY")

        self.settings = settings

        # Thread-safe queue to save audio segments
        self.audio_queue = queue.Queue()

        # Thread-safe queue to transcribe audio segments
        self.transcribe_queue = queue.Queue()
        self.i = 0

        self._stop_event = threading.Event()

    def start(self):
        saving_thread = threading.Thread(target=self.save)
        saving_thread.start()

        transcribing_thread = threading.Thread(target=self.transcribe)
        transcribing_thread.start()

        listening_thread = threading.Thread(target=self.listen)
        listening_thread.start()

    def stop(self):
        self.transcribe_queue.put(None)
        self.audio_queue.put(None)
        self._stop_event.set()

    def input(self):
        pass

    def listen(self):
        r = sr.Recognizer()

        while not self._stop_event.is_set():
            try:

                # use the microphone as source for input.
                with sr.Microphone() as source:

                    # wait for a second to let the recognizer
                    # adjust the energy threshold based on
                    # the surrounding noise level
                    r.adjust_for_ambient_noise(source, duration=0.2)

                    # listens for the user's input
                    audio = r.listen(source)

                    # Put audio segment in queue
                    self.audio_queue.put(audio)
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))

            except sr.UnknownValueError:
                print("unknown error occurred")
        pass

    def save(self):
        directory = "recordings"
        if not os.path.exists(directory):
            os.makedirs(directory)

        while not self._stop_event.is_set():
            # Read a segment from the queue
            segment = self.audio_queue.get(block=True)
            if segment is None:
                break

            path_to_audio_file = f"{directory}/audio_file_{self.i}.wav"
            with open(path_to_audio_file, "wb") as f:
                f.write(segment.get_wav_data())
                f.close()
            self.i += 1
            self.transcribe_queue.put(path_to_audio_file)

    def transcribe(self):
        while not self._stop_event.is_set():
            # Read a segment from the queue
            path_to_audio_file = self.transcribe_queue.get(block=True)
            if path_to_audio_file is None:
                break

            audio_file = open(path_to_audio_file, "rb")
            if self.settings.language != "English":
                transcript = openai.Audio.translate("whisper-1", audio_file)
            else:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
            audio_file.close()
            print("--TRANSCRIPT--")
            print(transcript)
