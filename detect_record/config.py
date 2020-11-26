import os
import yaml
from math import ceil
import pyaudio


frames_per_buffer = 1024
buffers_per_sec = 16000 / frames_per_buffer
# for adapting to environment noise level
min_sec_to_adapt = 2
min_voice_noise_delta = 100

__location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
config_file_path = os.path.join(__location__, 'config.yaml')


def get_pyaudio_config():
    pyaudio_config = {
        'format': pyaudio.paInt16,
        'channels': 1,
        'input': True,
        'frames_per_buffer': frames_per_buffer
    }
    with open(config_file_path, 'r') as config_file:
        c = yaml.safe_load(config_file)
        pyaudio_config['rate'] = c['sample-rate']

    return pyaudio_config


def get_detector_durations():
    configs = {}
    with open(config_file_path, 'r') as config_file:
        c = yaml.safe_load(config_file)
        global buffers_per_sec
        buffers_per_sec = ceil(c['sample-rate'] / frames_per_buffer)
        noise_sec = c['silence-before-voice']
        cached_sec = c['silence-after-voice']
        configs['cached_window'] = int(cached_sec * buffers_per_sec)
        # number of seconds to distinguish noise from voice
        configs['noise_window'] = int(noise_sec * buffers_per_sec)
        configs['min_sentence'] = int(c['min-voice-time'] * buffers_per_sec)
    return configs


def get_noise_thresholds():
    configs = {}
    with open(config_file_path, 'r') as config_file:
        c = yaml.safe_load(config_file)
        configs['initial'] = c['initial-threshold']
        configs['min'] = c['min-threshold']
        configs['delta-min'] = c['min-delta-threshold']
    return configs


def get_save_location():
    '''
    returns absolute path
    '''
    with open(config_file_path, 'r') as config_file:
        path = yaml.safe_load(config_file)['save-to']
        if os.path.isabs(path):
            return path
        return os.path.abspath(path)
