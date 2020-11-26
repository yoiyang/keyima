#!/usr/bin/env python3
import os
import yaml
import wave
import numpy as np
from pathlib import Path
from multiprocessing import Queue
from typing import Tuple
from multiprocessing import Process
from collections import Counter
import azure.cognitiveservices.speech as speechsdk

from detect_record import detect_record


__location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
config_file_path = os.path.join(__location__, 'config.yaml')


# refactored from https://github.com/nl8590687/ASRT_SDK_Python3
def read_wav_data(file_path: str) -> Tuple[str, int]:
    if not os.path.isabs(file_path):
        raise ValueError(f'file path {file_path} is not absolute')

    with wave.open(file_path, "rb") as wav:
        num_frame = wav.getnframes()
        str_data = wav.readframes(num_frame)
        wave_data = np.frombuffer(str_data, dtype=np.short)
        wave_data.shape = -1, wav.getnchannels()
        wave_data = wave_data.T
        return wave_data, wav.getframerate()

    raise RuntimeError(f"Error reading {file_path}")


def process_recorded_data(file_q: Queue) -> None:
    # load server configs
    configs = {}
    with open(config_file_path, 'r') as config_file:
        c = yaml.safe_load(config_file)
        configs['key'] = c['azure_subscription_key']
        configs['endpoint'] = c['azure_endpoint']
        configs['region'] = c['azure_region']

    speech_config = speechsdk.SpeechConfig(
        region=configs['region'], subscription=configs['key'])
    source_language_config = speechsdk.languageconfig.SourceLanguageConfig(
        "zh-CN", configs['endpoint'])

    counter = Counter({"可以": 0, "吗": 0})
    while True:
        new_file_path = file_q.get()
        # send it to microsoft
        audio_input = speechsdk.AudioConfig(filename=new_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            source_language_config=source_language_config,
            audio_config=audio_input)
        result = speech_recognizer.recognize_once()
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            print(result)
        print(result.text)
        for k in counter:
            if k in result.text:
                counter[k] += 1
        print(f'keyima counter {min(counter.values())}')
        # remove the processed file
        Path(new_file_path).unlink()


if __name__ == "__main__":
    '''assuming a server on local host is running on port 20000'''

    file_q = Queue()

    p1 = Process(target=detect_record.listen_for_sentences,
                 kwargs={'queue': file_q})
    p2 = Process(target=process_recorded_data, args=(file_q, ))
    p1.start()
    p2.start()
    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        print('Cleaning up..')
        p1.terminate()
        p2.terminate()
        while not file_q.empty():
            # remove unprocessed files
            Path(file_q.get()).unlink()
    finally:
        print('Done')
