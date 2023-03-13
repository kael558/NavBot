from typing import List

from simplechain.examples.AccessibilityBot.inputs.input import Input
from simplechain.examples.AccessibilityBot.inputs.keyboard import Keyboard
from simplechain.examples.AccessibilityBot.inputs.voice import Voice
from simplechain.examples.AccessibilityBot.outputs.audio import Audio
from simplechain.examples.AccessibilityBot.outputs.output import Output


def supported_langagues():
    return ["Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian", "Bulgarian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay", "Marathi", "Maori", "Nepali", "Norwegian", "Persian", "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian", "Spanish", "Swahili", "Swedish", "Tagalog", "Tamil", "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese", "Welsh"]

class Settings:
    def __init__(self):
        language: str = "English"
        inputs: List[Input] = [Voice()]
        outputs: List[Output] = [Audio()]
        keyword_detection: bool = True
        keyword: str = "Hey NavBot"

    def set_language(self, language: str):
        self.language = language

    def help(self):
        print("Settings help")
        print("language: " + self.language)
