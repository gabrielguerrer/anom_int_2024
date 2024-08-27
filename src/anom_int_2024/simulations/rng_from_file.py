"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The RNG_FROM_FILE class is defined to provide randomness using pregenerated
files, specifically for the Fast simulations module.
"""

import numpy as np

from rng_rava import D_RNG_BIT_SRC


class RNG_FROM_FILE:

    def __init__(self, filenames_bytes_a, filenames_bytes_b, bytes_start_idx=0):
        self.dev_serial_number = 0
        self.rng_bytes_per_frame = None

        self.bytes_idx = bytes_start_idx

        # Load bytes from file
        self.bytes_a = b''
        self.bytes_b = b''

        for f_bytes_a in filenames_bytes_a:
            with open(f_bytes_a, 'rb') as fa:
                self.bytes_a += fa.read()

        for f_bytes_b in filenames_bytes_b:
            with open(f_bytes_b, 'rb') as fb:
                self.bytes_b += fb.read()

        # Convert to numpy
        self.bytes_a = np.frombuffer(self.bytes_a, dtype=np.uint8)
        self.bytes_b = np.frombuffer(self.bytes_b, dtype=np.uint8)


    def init_queue_data(self):
        pass


    def snd_pwm_setup(self, pwm_freq, pwm_duty):
        pass


    def snd_rng_setup(self, rng_si):
        pass


    def get_rng_bits(self, bit_source):
        bytes_a = self.bytes_a[self.bytes_idx: self.bytes_idx + 1]
        bytes_b = self.bytes_b[self.bytes_idx: self.bytes_idx + 1]
        self.bytes_idx += 1

        bit_a = bytes_a & 1
        bit_b = bytes_b & 1

        if bit_source == D_RNG_BIT_SRC['AB']:
            return bit_a, bit_b

        elif bit_source == D_RNG_BIT_SRC['AB_XOR']:
            return bit_a ^ bit_b


    def snd_rng_byte_stream_start(self, rng_bytes_per_frame, sess_frame_dur_ms, postproc_id=0):
        self.rng_bytes_per_frame = rng_bytes_per_frame


    def snd_rng_byte_stream_stop(self, data_clear_delay_s=0):
        pass


    def get_rng_byte_stream_data(self, output_type='array'):
        bytes_a = self.bytes_a[self.bytes_idx: self.bytes_idx + self.rng_bytes_per_frame]
        bytes_b = self.bytes_b[self.bytes_idx: self.bytes_idx + self.rng_bytes_per_frame]
        self.bytes_idx += self.rng_bytes_per_frame

        return bytes_a, bytes_b


    def bytes_available(self):
        return len(self.bytes_a), len(self.bytes_b)