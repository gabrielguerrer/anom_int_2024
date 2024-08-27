"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This code evokes the Simulation application.
"""

from rng_rava.tk.ctrlp import rava_subapp_control_panel
from anom_int_2024.experiments import RAVA_APP_ANOM_INT, DB_SIM_LOCAL_FILENAME, rava_subapp_groups
from anom_int_2024.simulations import rava_subapp_simulations, rava_subapp_simulations_fast

TITLE = 'AnomInt: Simulations'
SUBAPPS = [rava_subapp_control_panel, rava_subapp_simulations, rava_subapp_simulations_fast, rava_subapp_groups]
rava_subapp_control_panel['show_button'] = False


def main():
    # RAVA main app
    tkapp = RAVA_APP_ANOM_INT(title=TITLE, db_filename=DB_SIM_LOCAL_FILENAME, subapp_dicts=SUBAPPS, cfg_log_name='anom_int_2024_sim')

    # Enter Tk loop
    tkapp.mainloop()


if __name__ == '__main__':
    main()