import yaml
import pyaudio


frames_per_buffer = 1024


def get_pyaudio_config():
    pyaudio_config = {
        'format': pyaudio.paInt16,
        'channels': 1,
        'input': True,
        'frames_per_buffer': frames_per_buffer
    }
    with open('config.yaml', 'r') as config_file:
        c = yaml.safe_load(config_file)
        pyaudio_config['rate'] = c['sample-rate']

    return pyaudio_config


def get_silence_buffer_sizes():
    buffer_sizes = {}
    with open('config.yaml', 'r') as config_file:
        c = yaml.safe_load(config_file)
        buffers_per_sec = c['sample-rate'] // frames_per_buffer
        sec_before = c['silence-before-voice']
        sec_after = c['silence-after-voice']
        buffer_sizes['before'] = int(sec_before * buffers_per_sec)
        buffer_sizes['after'] = int(sec_after * buffers_per_sec)
    return buffer_sizes


def get_initial_noise_threshold():
    with open('config.yaml', 'r') as config_file:
        c = yaml.safe_load(config_file)
        return c['initial-threshold']


def get_save_location():
    with open('config.yaml', 'r') as config_file:
        c = yaml.safe_load(config_file)
        return c['save-to']