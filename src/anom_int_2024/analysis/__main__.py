"""
Copyright (c) 2024 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This code evokes the Data Analysis application.
"""

from anom_int_2024.analysis import WINDOW_ANALYSIS

TITLE = 'AnomInt: Data Analysis'


def main():
    # RAVA main app
    tkapp = WINDOW_ANALYSIS(TITLE)

    # Enter Tk loop
    tkapp.mainloop()


if __name__ == '__main__':
    main()