"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
The RAVA_APP_ANOM_INT class extends RAVA_APP by incorporating a shared EXP_MGR
instance, which is utilized by all RAVA_SUBAPPS.
"""

import platform
import os
import fcntl

import tkinter.messagebox as tkm

from rng_rava import RAVA_RNG
from rng_rava.tk import RAVA_APP

from anom_int_2024.experiments import EXP_MGR, FILES_PATH


class RAVA_APP_ANOM_INT(RAVA_APP):

    def __init__(self, title, db_filename, subapp_dicts=[], cfg_log_name='anom_int'):
        # Linux? Ensure single instance. Todo: implement for windows as well
        if 'linux' in platform.system().lower():
            pid_file = os.path.join(FILES_PATH, cfg_log_name + '.pid')
            self.file_single_lock = open(pid_file, 'w')
            try:
                fcntl.lockf(self.file_single_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                exit('Another instance already running!')

        # Initialize RAVA_APP
        super().__init__(title=title, geometry='480x300', subapp_dicts=subapp_dicts, rava_class=RAVA_RNG, cfg_log_name=cfg_log_name)

        # Experiment Manager
        self.exp_mgr = EXP_MGR(self, db_filename)