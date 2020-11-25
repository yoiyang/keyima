#!/usr/bin/env python3
import operator
import audioop
from functools import reduce
from math import sqrt
from collections import deque
from typing import Optional
from multiprocessing import Queue

from . import recorder
from . import config


def is_human_talking(threshold: int, window: deque) -> bool:
    return reduce(operator.add, map(lambda x: x > threshold, window)) > 0


def listen_for_sentences(max_num_sentences: Optional[int] = None,
                         queue: Queue = None) -> None:
    audio_configs = config.get_pyaudio_config()
    save_location = config.get_save_location()
    # open pyaudio record session
    with recorder.new_stream(**audio_configs) as (stream, save_data):
        window_sizes = config.get_silence_buffer_sizes()
        # window to detect noise
        window = deque(maxlen=window_sizes['after'])
        # window to cache sound before detecting human talking
        lead_in_capacity = window_sizes['before']
        lead_in = deque(maxlen=lead_in_capacity)
        lead_in_placeholder = [b''] * lead_in_capacity
        # data for cached noise + current sentence
        sentence = lead_in_placeholder[:]
        num_sentences = 0
        noise_threshold = config.get_initial_noise_threshold()

        print('Listening..')
        # busy loop detecting voices
        while True:
            cur_buffer = stream.read(config.frames_per_buffer)
            # TODO(yoiyang): why sqrt and 4
            window.append(sqrt(abs(audioop.avg(cur_buffer, 4))))
            if is_human_talking(noise_threshold, window):
                sentence.append(cur_buffer)
                continue
            elif len(sentence) == lead_in_capacity:
                lead_in.append(cur_buffer)
                continue

            # stop when no one is speaking
            sentence[lead_in_capacity-len(lead_in):lead_in_capacity] = lead_in
            file_path = save_data(sentence, audio_configs, save_location)
            if queue:
                queue.put_nowait(file_path)
            num_sentences += 1
            if max_num_sentences and num_sentences >= max_num_sentences:
                break

            window.clear()
            lead_in.clear()
            sentence = lead_in_placeholder[:]

    print("Done")


if __name__ == "__main__":
    q = Queue()
    listen_for_sentences(queue=q)
