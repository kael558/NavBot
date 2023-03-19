from typing import List, Any, Tuple, Literal

from IO.inputs import Input
from IO.outputs.output import Output


def supported_langagues():
    return ["Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian", "Bulgarian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay", "Marathi", "Maori", "Nepali", "Norwegian", "Persian", "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian", "Spanish", "Swahili", "Swedish", "Tagalog", "Tamil", "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese", "Welsh"]

class Settings:
    def __init__(self):
        self.language: str = "English"
        #self.inputs: List[Input] = []
        #self.outputs: List[Output] = []
        self.push_to_talk: bool = True
        self.push_to_talk_key: str = "space"
        self.keyword_detection: bool = True
        self.keyword: str = "Hey NavBot"
        self.verbose_mode: bool = False
        self.verbosity_length: Literal["Short", "Moderate", "Long"] = "Moderate"

    def set_language(self, language: str):
        self.language = language

    def help(self):
        print("Settings help")
        print("language: " + self.language)

    def change_setting(self, settings_change: Tuple[str, Any]):
        if settings_change[0] not in self.__dict__:
            raise Exception("Setting does not exist")


        self.__dict__[settings_change[0]] = settings_change[1]
        pass
