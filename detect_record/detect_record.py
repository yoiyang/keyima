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


def window_avg_intensity(window: deque) -> int:
    # sorted_window = sorted(window, reverse=True)
    # sample_size = int(len(window) * 0.2)
    # if sample_size:
    #     return sum(sorted_window[:sample_size]) / sample_size
    # return 0
    if window:
        return sum(list(window)) / len(window)
    return 0


def listen_for_sentences(max_num_sentences: Optional[int] = None,
                         queue: Queue = None) -> None:
    audio_configs = config.get_pyaudio_config()
    save_location = config.get_save_location()
    # open pyaudio record session
    with recorder.new_stream(**audio_configs) as (stream, save_data):
        durations = config.get_detector_durations()
        # window to detect noise
        window = deque(maxlen=durations['noise_window'])
        # window to cache sound before detecting human talking
        lead_in_size = durations['cached_window']
        lead_in = deque(maxlen=lead_in_size)
        lead_in_placeholder = [b''] * lead_in_size
        # data for cached noise + current sentence
        sentence = lead_in_placeholder[:]
        num_sentences = 0
        noise_thresholds = config.get_noise_thresholds()
        noise_threshold = noise_thresholds['initial']

        print('Listening..')
        i = 0
        threshold_adapt_counter = 0
        # busy loop detecting voices
        while True:
            cur_buffer = stream.read(config.frames_per_buffer)
            # TODO(yoiyang): why sqrt and 4
            window.append(sqrt(abs(audioop.avg(cur_buffer, 4))))

            # adapt environment noise levels
            i += 1
            # check window avg only at every second
            if i % config.buffers_per_sec == 0:
                avg = window_avg_intensity(window)
                # if intensity delta is enough to change
                if abs(avg - noise_threshold) > noise_thresholds['delta-min']:
                    threshold_adapt_counter += 1
                    # if noise level is stable
                    if threshold_adapt_counter >= config.min_sec_to_adapt:
                        # change threshold to adapt noise
                        noise_threshold = noise_threshold * 0.8 + avg * 0.2
                        noise_threshold = max(noise_threshold,
                                              noise_thresholds['min'])
                        threshold_adapt_counter = 0
                        # print(f'avg: {avg}, threshold {noise_threshold}')
                else:
                    threshold_adapt_counter = 0

            # speaking started
            voice_threshold = config.min_voice_noise_delta + noise_threshold
            if is_human_talking(voice_threshold, window):
                sentence.append(cur_buffer)
                continue
            # speaking not started
            elif len(sentence) == lead_in_size:
                lead_in.append(cur_buffer)
                continue
            # speaking ended; record at least 2 second
            if len(sentence) > durations['min_sentence']:
                sentence[lead_in_size-len(lead_in):lead_in_size] = lead_in
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
