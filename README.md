# Anomalous Interactions 2024

This software framework supports the research titled "Investigating the Claim of Anomalous Psychophysical Interactions Using a Rigorous Metascientific Framework". It provides functionality for simulations, data collection, and data analysis.

Relevant links:
- [OSF Project](https://osf.io/vuscn) : It includes the two preregistration documents and the collected data.
- [OSF Preprint](https://osf.io/preprints/psyarxiv/wkjdu_v1) : A preprint describing the study’s findings; the article has been submitted to a scientific journal and is currently under peer review.
<!--- [Research Article]()  To be updated -->


## Installation

The operating system used in the mentioned research and on which this framework has been extensively tested is [Linux Debian v12](https://www.debian.org/releases/bookworm/).

Ensure that Python version 3.11.2 is installed. If not, you can download and install it [here](https://www.python.org/downloads/release/python-3112/).

Create and activate a virtual environment, replacing `~/env/anom_int_2024` with your preferred directory name:
```
python3 -m venv ~/env/anom_int_2024
source ~/env/anom_int_2024/bin/activate
```

Download and extract the [v1.0 release](https://github.com/gabrielguerrer/anom_int_2024/archive/refs/tags/v1.0.zip) to a directory, which we'll refer to as `~/Downloads/anom_int_2024-1.0/`.

To build and install the `anom_int_2024` package, run the following commands. The necessary dependencies will be automatically installed in your environment:
```
cd ~/Downloads/anom_int_2024-1.0/
pip install build
python3 -m build
pip install dist/anom_int_2024-1.0-py3-none-any.whl
```

With the `~/env/anom_int_2024` environment activated, the three modules can be executed using the following commands:
```
python3 -m anom_int_2024.experiments
python3 -m anom_int_2024.simulations
python3 -m anom_int_2024.analysis
```

### Requirements
- [RAVA Circuit v1.0](https://github.com/gabrielguerrer/rng_rava)
- [RAVA Firmware v1.0.0](https://github.com/gabrielguerrer/rng_rava_firmware)
- [RAVA Driver v1.2.1](https://github.com/gabrielguerrer/rng_rava_driver_py)
- [Python v3.11.2](https://www.python.org/downloads/release/python-3112/)
- [pyserial v3.5](https://github.com/pyserial/pyserial)
- [numpy v1.26.4](https://github.com/numpy/numpy)
- [scipy v1.14.0](https://github.com/scipy/scipy)
- [matplotlib v3.9.1](https://github.com/matplotlib/matplotlib)
- [sqlalchemy v2.0.31](https://github.com/sqlalchemy/sqlalchemy)


## Experiments

This module coordinates data collection by applying the methodology specified in the preregistration documents. 
To run it, activate the environment as described above and execute:

```
python3 -m anom_int_2024.experiments
```

![Experiments screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/experiments.png)

### Groups

The first step is to create an experimental group, which defines which experiments (1–4) will be run, in what order, and how many sessions are assigned to each.

To create a group, click on “Groups”, and in the “Add” tab:
- Assign a numeric identifier to the group
- Select the experiments to include (multiple selections can be made by holding the left mouse button and dragging, or by using Shift + mouse left click)
- Specify the number of sessions to be conducted for each experiment
- Set “Type = Auto” if you want the system to automatically select the experiment type for each new session: At the start of each participant session, the system uses the record of prior contributions to randomly select an experiment type without replacemen (see the function `mgr_part_sess_type_auto()` in `experiment_manager.py`). If this option is not enabled, the experiment type must be selected manually in the new session menu.
- Click “Add” to create the group

All created groups can be viewed in the “View” tab.

![Groups example](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/groups.png)

The image above shows the group definition used in the study’s first preregistration: 60 sessions were assigned to each of the four experiments, with experiment types randomly selected throughout the course of the study.


### Participant Sessions

To start data collection, click on “New Session.” To run a participant session, navigate to the “Participant” tab and provide the following:
- Enter the participant’s name and a unique numeric identifier
- Select the group identifier (created in the previous section)
- If in the group creating, experiment type was set to automatic (Type = Auto), no further action is required; Otherwise, the user must specify the experiment type under “Sess Type”

The bottom panel displays how many participant sessions remain to complete the selected group.

![New session example](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/new_session.png)

To start the experiment, click on "Start". The first 3 minutes are dedicated to participant relaxation.
This is followed by 5 minutes of visual feedback (a circle with varying diameter), during which the participant is instructed to mentally intend an increase in the circle's diameter. At the end of the session, a star rating (from 1 to 3) is displayed, reflecting the rarity of the outcome.

### Sham Sessions

After each participant session, the experimenter must run a sham session in the “Sham” tab, during which no one observes the feedback.

A one-to-one sequence is mandatory: each participant session must be followed by a sham session. If a new participant session is started without a preceding sham session, the system will display an error message. An error is also triggered if two consecutive sham sessions are attempted.

### Database

The database file generated by the data collection procedures is located in the following directory (assuming your username is *user*):
- Linux: `/home/user/.rava`
- Windows: `C:\Users\user\.rava`

### Sessions Visualization

By clicking on “Results,” the experimenter can view a list of all collected participant sessions, including the date, group ID, participant ID, and corresponding star rating. This functionality is provided to allow the experimenter to track contributions - for example, to determine how many sessions a given participant has completed.

The actual p-values computed by the analysis procedure are not accessible to the experimenter.


## Simulations

This module coordinates the simulations used to assess potential systematic errors in both the randomness generation and the analytical procedures.
To run it, activate the environment and execute:

```
python3 -m anom_int_2024.simulations
```

![Simulations screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/simulations.png)

Two different simulation methods are employed, each differing in their randomness input mechanism. 
In the *standard mode*, data is collected following the predefined methodology, without participants observing the real-time feedback. 
In this approach, the 8-minute sessions are conducted sequentially, allowing for the collection of up to 180 sessions per day.
 
In the *fast mode*, the randomness input is provided by random bytes files generated by the RAVA device at its maximum throughput.
This approach used the same code as standard sessions, with the differences being the randomness input and the real-time feedback. Although feedback magnitudes are computed, they are not visually displayed as a dynamically varying circle.
By replacing real-time byte generation (every 100 ms) with pregenerated data, the fast mode enabled the production of numerous sham sessions within a reasonable time frame.

### Groups

The group functionality in the simulations module is used to steer the simulations: it indicates how many sessions should be conducted for the experiments.

The “Type = Auto” option

### Standard Mode

To conduct simulations in standard mode, click on "Simulations".

Requires the RAVA circuit to be connected


![Standard Simulation screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/simulation_standard.png)


### Fast Mode

Fast utilizzes random data files collected at the maximum troughput, though nbot requiring a RAVA device to be connected


![Fast Simulation screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/simulation_fast.png)


## Analysis

This module contains the analysis tools used to produce t. 
To run it, activate the environment and execute:

```
python3 -m anom_int_2024.analysis
```

![Analysis screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/analysis.png)

### Preregistered studies results

To reproduce the results obtained in the preregistered studies:

- Download the study data from the [OSF Project](https://osf.io/vuscn) website
- As described above, activate the environment and run the analysis module using `python3 -m anom_int_2024.analysis`
- In the "database" section, click "..." to select the `.db` file, then click "Connect"
- In the "filter" section, the `sess_group` variable specifies whether the data correspond to the first or second preregistered study. The `sess_type` variable selects one of the four experiments 
  - Choose the desired study (PR1 or PR2) and experiment
- In the "analysis" section, under the "prereg" tab, click "Analyze". The probability outcomes for participant and sham sessions are displayed in the "results" box

![Preregistered Analysis](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/analysis.png)


## Contact

gabrielguerrer [at] gmail [dot] com

![RAVA logo](https://github.com/gabrielguerrer/rng_rava/blob/main/images/rng_rava_logo.png)