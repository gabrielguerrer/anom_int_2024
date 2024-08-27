"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This code evokes the Data Acquisition application.
"""

from rng_rava.tk.ctrlp import rava_subapp_control_panel
from anom_int_2024.experiments import RAVA_APP_ANOM_INT, DB_LOCAL_FILENAME
from anom_int_2024.experiments import rava_subapp_groups, rava_subapp_experiments, rava_subapp_results

TITLE = 'AnomInt: Data Acquisition'
SUBAPPS = [rava_subapp_control_panel, rava_subapp_experiments, rava_subapp_groups, rava_subapp_results]
rava_subapp_control_panel['show_button'] = False


def main():
    # RAVA main app
    tkapp = RAVA_APP_ANOM_INT(title=TITLE, db_filename=DB_LOCAL_FILENAME, subapp_dicts=SUBAPPS, cfg_log_name='anom_int_2024')

    # Enter Tk loop
    tkapp.mainloop()


if __name__ == '__main__':
    main()