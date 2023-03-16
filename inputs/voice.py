import os
import queue
import threading

import openai
import speech_recognition as sr

from inputs.input import Input
import io


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
    def __init__(self, settings, output_queue: queue.Queue):
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
                    r.adjust_for_ambient_noise(source, duration=0.2)

                    # listens for the user's input
                    audio = r.listen(source, timeout=60)

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

    def _get_input(self):
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
        print("--TRANSCRIPT--")
        print(transcript)
        return transcript
