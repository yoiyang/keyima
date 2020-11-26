import contextlib
import time
import pyaudio
import wave
from typing import Callable, Tuple


@contextlib.contextmanager
def new_stream(*args, **kwds) -> Tuple[pyaudio.Stream, Callable]:
    p = pyaudio.PyAudio()
    stream = p.open(**kwds)

    def save_data(data: list, configs: dict, save_loc: str) -> str:
        file_path = f'{save_loc}/rec_{int(time.time())}.wav'

        with wave.open(file_path, 'wb') as wf:
            data = b''.join(data)
            wf.setnchannels(configs['channels'])
            wf.setsampwidth(p.get_sample_size(configs['format']))
            wf.setframerate(configs['rate'])
            wf.writeframes(data)

            return file_path

        raise RuntimeError(f'Fail to store {file_path}')

    yield stream, save_data
    stream.close()
    p.terminate()
