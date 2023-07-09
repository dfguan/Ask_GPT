import os,json

from urllib.parse import urlencode

import requests
import azure.cognitiveservices.speech as speechsdk

from azure.cognitiveservices.speech.audio import AudioOutputConfig


pre_prompts = []
temp_prompt = {"user":"", "robot":""} 

# speech_recognizer = speechsdk.SpeechRecognizer(
        # speech_config=speech_config, 
        # auto_detect_source_language_config=auto_detect_source_language_config, 
        # audio_config=audio_config)
# result = speech_recognizer.recognize_once()
# auto_detect_source_language_result = speechsdk.AutoDetectSourceLanguageResult(result)
# detected_language = auto_detect_source_language_result.language
def record(speech_config, auto_detect_source_language_config):
    # Creates a recognizer with the given settings
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, auto_detect_source_language_config = auto_detect_source_language_config)

    print("say something...")
    result = speech_recognizer.recognize_once()

    # Checks result.
    flag = 0
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        flag = 1
        temp_prompt["user"] = result.text
        print("Recognized: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

    # auto_detect_source_language_result = speechsdk.AutoDetectSourceLanguageResult(result)
    # detected_language = auto_detect_source_language_result.language


    return [flag, result.text]


def chat(text_words, api_key):
    api_key = api_key 
    api_url = "https://www.chatlink.com.cn/api/wcx_app"
    headers = {"Content-Type":"application/x-www-form-urlencoded"}

    data = { "api_key": api_key, "pre_prompts": json.dumps(pre_prompts), "prompt": text_words, "mode": 0, "adds": []}


    # req["perception"]["inputText"]["text"] = text_words
    response = requests.request("post", api_url, data=urlencode(data), headers=headers)
    # print(response)
    response_dict = json.loads(response.text)
    resp_text = ""
    if response_dict["runtime"]["exitcode"] == 0:
        resp_text = response_dict["content"] 
        temp_prompt["robot"] = resp_text
        pre_prompts.append(temp_prompt)
    else:
        resp_text = response_dict["runtime"]["error"]
    print("AI Robot said: " + resp_text)
    return resp_text

#判断字符串是否包含中文
def str_contain_chinese(str):
    for ch in str:
        if u'\u4e00'<=ch<=u'\u9fff':
            return True
    return False

def speak(text_words):
    speech_config.speech_synthesis_language = "en-US" 
    if str_contain_chinese(text_words):
        speech_config.speech_synthesis_language = "zh-CN" 

    audio_config = AudioOutputConfig(use_default_speaker=True)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = speech_synthesizer.speak_text_async(text_words).get()

    # Checks result.
    # if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # print("Speech synthesized to speaker for text [{}]".format(text_words))
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
        print("Did you update the subscription info?")

def is_intend_to_leave(text):
    for t in ["退出","再见","回聊"]:
        if t in text:
            return True
    up_text = text.upper()
    for t in ["BYE", "SEE YOU", "NIGHT"]:
        if t in up_text:
            return True
    return False


if __name__ == '__main__':
    # config azure speech service 
    if os.path.isfile("config.json"): 
        with open("config.json") as f:
            d = json.load(f)
            if not "speech_key" in d or d["speech_key"] == ""  or not "service_region" in d or d["service_region"] == "" or not "api_key"  in d or d["api_key"] == "" :
                print ("请在config.json中配置speech_key, service_region和api_key")
            else:
                speech_key, service_region = d["speech_key"], d["service_region"]

                speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region) 
                auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "zh-CN"])
                api_key = d["api_key"]
                while True:
                    [flag, text] = record(speech_config, auto_detect_source_language_config)
                    if flag == 1:
                        if  is_intend_to_leave(text):
                            speak("see you.")
                            print ("AI Robot said: see you")
                            break
                        res = chat(text, api_key)
                        speak(res)
            f.close()
    else:
        print ("无法找到config.json")


