"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The EXP_BASE is the base class with the common functionalitie shared between all
experiment types.

The experiments have three epochs: Initialization, Byte generation loop and
feedback, and Finalization.

Different experiments inherit from EXP_BASE, implementing their
own initialize_extra(), bytes_process(), and feedb_pvalue() functions.
"""

import logging
import datetime
import time
import hashlib

import numpy as np

from rng_rava import D_RNG_BIT_SRC


# FUNCTIONS

def hex_to_nibble(bytes):
    res = ''
    for b in bytes:
        high = (b >> 4)
        low = (b & 0x0F)
        res += '{}{}'.format(hex(high)[2:], hex(low)[2:])
    return res


def bytes_to_hash(bytes_array_a, bytes_array_b, hash_size):
    bytes = bytes_array_a.tobytes() + bytes_array_b.tobytes()
    hash_bytes = hashlib.blake2b(bytes, digest_size=hash_size).digest()
    return hex_to_nibble(hash_bytes)


# EXP_BASE

class EXP_BASE:

    def __init__(self, name, rng, win_feedb):
        self.name = name
        self.lg = logging.getLogger('rava_app')
        self.rng = rng
        self.win_feedb = win_feedb

        # Feedback vars
        self.feedb_mags = None


    def run(self, exp_init_data):
        # Debug
        self.lg.info('{}: Starting Exp Session'.format(self.name))

        #####
        ## 1) Initialize experiment
        exp_data = {}

        # Timing
        dt_start = datetime.datetime.now()
        t_start = time.perf_counter()

        # Exp config data
        rng_setup_pwm_freq = self.cfg['rng_setup_pwm_freq']
        rng_setup_pwm_duty = self.cfg['rng_setup_pwm_duty']
        rng_setup_si = self.cfg['rng_setup_si']
        rng_postproc_id = self.cfg['rng_postproc_id']
        rng_bytes_per_frame = self.cfg['rng_bytes_per_frame']
        sess_hash_n_bytes = self.cfg['sess_hash_n_bytes']
        sess_frame_dur_ms = self.cfg['sess_frame_dur_ms']
        sess_dur_min = self.cfg['sess_dur_min']
        feedb_n_avg = self.cfg['feedb_n_avg']
        feedb_mag_min = self.cfg['feedb_mag_min']

        # Initial data
        exp_data['dt_start'] = dt_start
        exp_data['rng_sn'] = self.rng.dev_serial_number
        exp_data['rng_bytes_per_frame'] = rng_bytes_per_frame

        # User provided data
        exp_data['part_id'] = exp_init_data['part_id']
        exp_data['part_name'] = exp_init_data['part_name']
        exp_data['sess_group'] = exp_init_data['sess_group']
        exp_data['sess_type'] = exp_init_data['sess_type']
        exp_data['sess_sham'] = exp_init_data['sess_sham']
        exp_data['part_hash_pointer'] = exp_init_data['part_hash_pointer']
        exp_data['feedb_rng_target'] = exp_init_data['feedb_rng_target']

        # Frame data
        frame_per_min = (1000 / sess_frame_dur_ms) * 60
        frame_n = int(sess_dur_min * frame_per_min)

        exp_data['frame_n'] = frame_n
        exp_data['frame_dur_ms'] = sess_frame_dur_ms

        # Initialize feedb arrays
        exp_data['feedb_mag'] = np.zeros(frame_n, dtype=np.uint8)
        exp_data['feedb_mag_avg'] = np.zeros(frame_n, dtype=np.uint8)
        self.feedb_mags = np.zeros(feedb_n_avg, dtype=np.float32)

        # Initialize bytes arrays
        exp_data['rng_bytes_a'] = np.zeros(shape=(frame_n, rng_bytes_per_frame), dtype=np.uint8)
        exp_data['rng_bytes_b'] = np.zeros(shape=(frame_n, rng_bytes_per_frame), dtype=np.uint8)

        # Configure RNG
        self.rng.snd_pwm_setup(rng_setup_pwm_freq, rng_setup_pwm_duty)
        self.rng.snd_rng_setup(rng_setup_si)

        # Reset RNG internal data structures
        self.rng.init_queue_data()

        # Define target stream in part sessions
        if exp_data['feedb_rng_target'] is None:
            feedb_rng_target = self.rng.get_rng_bits(D_RNG_BIT_SRC['AB_XOR']) # Generate bit
            exp_data['feedb_rng_target'] = 'A' if feedb_rng_target == 0 else 'B'

        # Initialization extra steps (exp 4)
        self.initialize_extra(exp_data)

        # Show Feedback Window
        self.win_feedb.show()

        # Start RNG byte stream
        self.rng.snd_rng_byte_stream_start(rng_bytes_per_frame, sess_frame_dur_ms, postproc_id=rng_postproc_id)

        #####
        ## 2) Byte acquisition loop / feedback
        for frame_i in range(frame_n):

            # Get and store Bytes
            bytes_a, bytes_b = self.rng.get_rng_byte_stream_data(output_type='array')

            exp_data['rng_bytes_a'][frame_i] = bytes_a
            exp_data['rng_bytes_b'][frame_i] = bytes_b

            # Process bytes (exp 4)
            bytes_a, bytes_b = self.bytes_process(exp_data, frame_i, bytes_a, bytes_b)

            # Select target bytes
            bytes_target = bytes_a if exp_data['feedb_rng_target'] == 'A' else bytes_b

            # Calculate p-value using target bytes
            p = self.feedb_pvalue(frame_i, exp_data, bytes_target)

            # Calculate feedback magnitude
            feedb_mag = 1. - np.sqrt(p)

            # Calculate Feedback average
            self.feedb_mags[frame_i % feedb_n_avg] = feedb_mag
            feedb_mag_avg = self.feedb_mags.mean()

            # Apply Feedback average minimum value
            if feedb_mag_avg < feedb_mag_min:
                feedb_mag_avg = feedb_mag_min

            # Store feedback values as int
            exp_data['feedb_mag'][frame_i] = int(round(feedb_mag * 255))
            exp_data['feedb_mag_avg'][frame_i] = int(round(feedb_mag_avg * 255))

            # Provide feedback
            self.win_feedb.draw(feedb_mag_avg)

        #####
        ## 3) Finalize Experiment

        # Stop RNG byte stream
        self.rng.snd_rng_byte_stream_stop()

        # Final data
        exp_data['sess_hash'] = bytes_to_hash(exp_data['rng_bytes_a'], exp_data['rng_bytes_b'], hash_size=sess_hash_n_bytes)
        exp_data['t_total_s'] = time.perf_counter() - t_start

        # Hide Feedback window
        self.win_feedb.hide()

        # Debug
        self.lg.info('{}: Exp Session finished'.format(self.name))
        self.lg.debug('{}: Results p_tgt={:.2f}%, mag={:.1f}%, mag_avg={:.1f}%'.format(self.name, p*100, feedb_mag*100, feedb_mag_avg*100))

        return exp_data, exp_init_data


    def initialize_extra(self, exp_data_dict):
        # Perform extra initialization steps
        # Implemented by inheriting classes
        pass


    def bytes_process(self, exp_data_dict, frame_i, bytes_a, bytes_b):
        # Process the generated bytes
        # Implemented by inheriting classes
        return bytes_a, bytes_b


    def feedb_pvalue(self, frame_i, exp_data_dict, bytes_array):
        # Transform random bytes into a single-tailed p-value
        # Implemented by inheriting classes
        pass