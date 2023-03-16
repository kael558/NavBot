
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

        # Thread-safe queue to save audio segments
        #self.audio_queue = queue.Queue()

        # Thread-safe queue to transcribe audio segments
        self.transcribe_queue = queue.Queue()
        self.i = 0

        self.start_threads()


    def start_threads(self):
        #saving_thread = threading.Thread(target=self.save)
        #saving_thread.start()

        #transcribing_thread = threading.Thread(target=self.transcribe)
        #transcribing_thread.start()

        listening_thread = threading.Thread(target=self.listen)
        listening_thread.start()

    def stop(self):
        self.transcribe_queue.put(None)
        #self.audio_queue.put(None)
        self._stop_event.set()


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
                    self.transcribe_queue.put(audio.get_wav_data())
                    #self.audio_queue.put(audio)
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
            nbr = NamedBufferedReader(f"audio_file_{self.i}.wav", segment.get_wav_data())
            self.transcribe_queue.put(nbr)
            self.i += 1
            path_to_audio_file = f"{directory}/audio_file_{self.i}.wav"
            with open(path_to_audio_file, "wb") as f:
                f.write(segment.get_wav_data())
                f.close()
            self.i += 1
            self.transcribe_queue.put(path_to_audio_file)

    
    def get_input(self):
        # Read a segment from the queue
        audio_file_wav_data = self.transcribe_queue.get(block=True)
        if audio_file_wav_data is None:
            return None
        
        byte_stream = io.BytesIO(audio_file_wav_data)
        audio_file = NamedBufferedReader(f"audio_file_{self.i}.wav", raw=byte_stream)
        #audio_file = open(path_to_audio_file, "rb")
        if self.settings.language != "English":
            transcript = openai.Audio.translate("whisper-1", audio_file)
        else:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        audio_file.close()
        print("--TRANSCRIPT--")
        print(transcript)
        return transcript

