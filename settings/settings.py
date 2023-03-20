import os
from typing import Any, Tuple, Literal

from simplechain.stack import Annoy
from simplechain.stack.text_embedders.openai import TextEmbedderOpenAI


def supported_langagues():
    return ["Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian", "Bulgarian", "Catalan",
            "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", "Galician",
            "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese",
            "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay", "Marathi", "Maori", "Nepali",
            "Norwegian", "Persian", "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian",
            "Spanish", "Swahili", "Swedish", "Tagalog", "Tamil", "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese",
            "Welsh"]


class Settings:
    def __init__(self):

        # self.inputs: List[Input] = []
        # self.outputs: List[Output] = []
        self.push_to_talk: bool = False
        self.push_to_talk_key: str = "space"

        self.keyword_detection: bool = True
        self.keyword: str = "Hey NavBot"

        self.verbose_mode: bool = True

        self.language: Literal["Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian", "Bulgarian",
        "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish",
        "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic",
        "Indonesian", "Italian", "Japanese", "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian",
        "Macedonian", "Malay", "Marathi", "Maori", "Nepali", "Norwegian", "Persian", "Polish",
        "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian", "Spanish", "Swahili",
        "Swedish", "Tagalog", "Tamil", "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese", "Welsh"] = "English"

        self.verbosity_length: Literal["Short", "Moderate", "Long"] = "Short"
        self.talking_speed: Literal["Slow", "Moderate", "Fast"] = "Moderate"
        self.voice: Literal["Male", "Female"] = "Female"

        self.text_embedder = TextEmbedderOpenAI()
        self.base_index, self.languages_index = self.get_indexes()

    def set_language(self, language: str):
        self.language = language

    def help(self):
        print("Settings help")
        print("language: " + self.language)

    def change_setting(self, settings_change: Tuple[str, str, Any]):
        if settings_change[1] not in self.__dict__:
            raise Exception("Setting does not exist")

        self.__dict__[settings_change[1]] = settings_change[2]

    def get_indexes(self):
        if not os.path.exists("settings/base.ann"):
            return set_up_verifier(self.text_embedder)

        return Annoy(1536, "settings/base.ann", "settings/base.json"), \
            Annoy(1536, "settings/languages.ann", "settings/languages.json")

    def get_setting(self, text: str):
        return self.base_index.get_nearest_neighbors(self.text_embedder.embed(text), 1)

    def get_setting_value(self, setting, text):
        if setting == "Change language":
            return self.languages_index.get_nearest_neighbors(self.text_embedder.embed(text), 1)
        return None


def set_up_verifier(text_embedder):
    vectordb = {
        "yes": ["Yes", "Yes that works", "Yes that is what I asked", "Yes that sounds good", "Yes that is what I want"],
        "no": ["No", "No that is not what I asked", "No can you do this instead?", "No that is not what I want"],

        "enable push to talk": ["Can you enable push to talk?", "I want to use push to talk",
                                "Why is it picking up other sounds",
                                "I want to control when the audio picks up my voice",
                                "Please stop listening to others"],
        "disable push to talk": ["Can you enable conversation mode?", "Start conversation mode.",
                                 "I want to disable push to talk", "Can you disable push to talk?",
                                 "Disable push to talk",
                                 "Hey Navbot, can you disable push to talk?"],

        "enable keyword detection": ["I want you to listen to me only when I say the keyword",
                                     "Can you enable keyword detection?", "I want keyword detection",
                                     "Please only record me when I say the keyword"],
        "disable keyword detection": ["Can you change to mode where you listen to me all the time?",
                                      "Can you disable keyword detection?", "I don't want keyword detection",
                                      "Please record me all the time"],

        "enable verbose mode": ["Can you enable verbose mode?", "I want to hear how the bot is navigating each page.",
                                "I want to hear descriptions of what the bot is doing",
                                "Can you tell me what the bot is doing?", "PLease let me know what the bot is doing"],
        "disable verbose mode": ["Can you disable verbose mode?", "I don't want to hear what the bot is doing",
                                 "I don't want to hear descriptions of what the bot is doing"],

        "talk more": ["Can you talk more?", "I want more information about the page",
                      "Can you give longer descriptions?",
                      "Give me longer descriptions"],
        "talk less": ["Can you talk less?", "I don't want so much information", "Can you give shorter descriptions?"],
        "talk faster": ["Can you talk faster?", "Can you increase your talking speed?", "Talk faster please",
                        "I want you to talk faster"],
        "talk slower": ["Can you talk slower?", "Can you decrease your talking speed?", "Talk slower please",
                        "I want you to talk slower"],
        "change to woman's voice": ["Can I talk to a woman?", "I want to hear a womans voice.", "Please change your voice to a womans voice"],
        "change to man's voice": ["Can I talk to a man?", "I want to hear a mans voice.", "Please change your voice to a mans voice"],
        "change language": ["Can you record other languages?", "Can you change the language to French?",
                            "I want to talk in a different language", "I want to speak in a different language",
                            "Can you the change the language?", "Can I talk in a different language?"],
        "exit": ["I am finished", "Shut down the bot", "Stop", "Thank you for your help, I am finished"]
    }

    base_index = Annoy(1536, "settings/base.ann", "settings/base.json")
    metadatas, keys = [], []
    for metadata, matches in vectordb.items():
        for match in matches:
            metadatas.append(metadata)
            keys.append(match)

    embeds = text_embedder.embed(keys)
    for embed, metadata in zip(embeds, metadatas):
        base_index.add(embed, metadata)
    base_index.save()

    languages_index = Annoy(1536, "settings/languages.ann", "settings/languages.json")
    supported_langs = ["Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian", "Bosnian", "Bulgarian",
                       "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish",
                       "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic",
                       "Indonesian", "Italian", "Japanese", "Kannada", "Kazakh", "Korean", "Latvian", "Lithuanian",
                       "Macedonian", "Malay", "Marathi", "Maori", "Nepali", "Norwegian", "Persian", "Polish",
                       "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian", "Spanish", "Swahili",
                       "Swedish", "Tagalog", "Tamil", "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese", "Welsh"]
    embeds = text_embedder.embed(supported_langs)
    for embed, lang in zip(embeds, supported_langs):
        languages_index.add(embed, lang)
    languages_index.save()

    return base_index, languages_index
