# Anomalous Interactions 2024

This software framework supports the research titled "Investigating the Claim of Anomalous Psychophysical Interactions Using a Rigorous Metascientific Framework". It provides functionality for data collection, data analysis, and simulations.

Relevant links:
- [OSF Project](https://osf.io/vuscn) : It includes the two preregistration documents (PR1 and PR2) and the collected data.
- [OSF Preprint](https://osf.io/preprints/psyarxiv/wkjdu_v1) : A preprint describing the study’s findings; the article has been submitted to a scientific journal and is currently under peer review.
<!--- [Research Article]()  To be updated -->


## Installation

The operating system used in the mentioned research and on which this framework has been extensively tested is [Linux Debian v12](https://www.debian.org/releases/bookworm/).

Ensure that Python 3.11 is installed. If not, it can be downloaded [here](https://www.python.org/downloads/release/python-31115/).

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
python3 -m anom_int_2024.analysis
python3 -m anom_int_2024.simulations
```

### Requirements
- [RAVA Circuit v1.0](https://github.com/gabrielguerrer/rng_rava)
- [RAVA Firmware v1.0.0](https://github.com/gabrielguerrer/rng_rava_firmware)
- [RAVA Driver v1.2.1](https://github.com/gabrielguerrer/rng_rava_driver_py)
- [Python v3.11](https://www.python.org/downloads/release/python-31115/)
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

The image above shows the group definition used in the study’s first preregistration (PR1): 60 sessions were assigned to each of the four experiments, with experiment types randomly selected throughout the course of the study.


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

The SQLite `.db` database file generated by the data collection procedures is located in the following directory (assuming your username is *user*):
- Linux: `/home/user/.rava`
- Windows: `C:\Users\user\.rava`

This file serves as the input to the analysis module.

### Sessions Visualization

By clicking on “Results” in the main application panel, the experimenter can view a list of all collected participant sessions, including the date, group ID, participant ID, and corresponding star rating. This functionality is provided to allow the experimenter to track contributions - for example, to determine how many sessions a given participant has completed.

The actual p-values computed by the analysis procedure are not accessible to the experimenter.


## Analysis
The analysis module performs the preregistered analyses, computing p-values for individual participant and sham sessions based on the experiment type, and combining them into a p'-value using Fisher’s method.
To run it, activate the environment and execute:

```
python3 -m anom_int_2024.analysis
```

### Preregistered Analysis

To reproduce the preregistered study results, follow these steps:

- Download the study database from the [OSF Project](https://osf.io/vuscn) website
- As described above, activate the environment and run the analysis module using `python3 -m anom_int_2024.analysis`
- In the "Database" section, click "..." to select the `.db` file, then click "Connect"
- In the "Filter" section, the `sess_group` variable specifies whether the data correspond to the first or second preregistered study. The `sess_type` variable selects one of the four experiments 
  - Choose the desired study (PR1 or PR2) and one of the four experiments
  - In the "Data" field it is possible to see the the total number of sessions in the database; how many sessions remain after filtering; and which sessions are currently selected (indicated by the blue highlight). Multiple sessions can be chosen by using Shift + left mouse click, or by clicking "Select all"  
- In the "Analysis" section, under the "Prereg" tab, click "Analyze"
  - The analysis is performed on the sessions selected in the “Data” field, with a p-value computed for each selected session
  - The combined p' probability outcomes for participant and sham sessions are displayed in the "Results" box

![Preregistered Analysis](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/analysis.png)


### Fast Simulation analysis

The fast simulation results shown for the first preregistration (PR1) were obtained by running the fast simulation procedure described in the next section, generating 60,000 sessions for each experiment. The resulting `sim.db` file is then processed using the Anaylis module as follows:

- Activate the environment and run the analysis module `python3 -m anom_int_2024.analysis`
- In the "Database" section, click "..." to select the simulation `.db` file, then click "Connect"
- In the "Filter" section, select one of the four experiments in the `sess_type` field
- Navigate to the "Fast Sim" tab in the "Analysis section"
- Specify the number of sections to combine for each p'-value in the "Comb N" field. In this case, a value of 60 is provided, resulting in 1000 p'-values used to populate the output histogram
- Select the number of bins for the histogram
- Click "Uniformity p-values" to analyze the sessions, plot the histograms, and perform the chi-square test of the uniformity hypothesis.

Note: Plot generation fails in Python 3.14. Ensure that Python 3.11 is used.


## Simulations

This module coordinates the simulations used to assess potential systematic errors in both the randomness generation and the preregistered analytical procedures.
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

The group functionality governs the simulation process by specifying the number of sessions to be simulated for each experiment in both standard and fast modes.

The "Type = Auto" option is enforced in both simulation modes. This means that, even if it is not explicitly selected here, it will be applied during the simulations, ensuring a random selection of experiment types without replacement within each block of four experiments.

### Standard Mode

To conduct simulations in standard mode, click on "Simulations". Since data are generated in real time, a RAVA circuit must be connected.
Select the corresponding group ID, specify the desired additional time delay (in minutes) between sessions, and click “Start” to initiate the simulation procedure.

![Standard Simulation screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/simulation_standard.png)

In the example above, the first preregistration (PR1) group is selected, which defines 60 participant sessions for each experiment. 
The status bar at the bottom of the window displays the number of sessions remaining to be collected. In this case, the total is 2 x 4 x 60, as sham sessions are collected following each "participant" session - here in quotes, since in both cases no participant observes the feedback.

The procedure cannot be resumed if interrupted, so ensure sufficient time is available before starting. The session progress is displayed at the window title, indicating how many sessions have been completed out of the total.

Upon completion, a `sim.db` file will be created in `~/.rava`, containing all session data.

### Fast Mode

In Fast mode, simulations utilize pre-generated random data files produced at the RNG’s maximum throughput, and therefore do not require a RAVA device to be connected.

To conduct simulations in fast mode, click on "Fast Simulations". 
The selected group ID determines the total amount of random data required, which is displayed in the status bar. The "2x" factor indicates that each file must provide this amount of data, reflecting the dual-randomness core feature of the RAVA device.

Provide the randomness files for each core in the "RNG A" and "RNG B" fields by clicking the corresponding "..." buttons to select the files.
Multiple files can be selected for each field by using Shift + left-click in the file selection window; their contents are concatenated to form a single input stream for each core.
Then, click “Start” to initiate the fast simulation procedure.

The procedure cannot be resumed if interrupted, so ensure sufficient time is available before starting. The session progress is displayed at the status bar at the bottom, indicating the number of sessions to finish.

![Fast Simulation screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/simulation_fast.png)

In the example above, the group used in the first preregistration (PR1) is selected. As 1000 repetitions of the 4 x 60 sessions are targeted, this corresponds to a total of 240,000 sessions. In this mode, only sham sessions are used, rather than the “participant"–sham sequence employed in standard mode.
The status bar indicates that a total of 2 x 1.09 GB of RAVA-generated randomness is required.

Upon completion, a `sim.db` file will be created in `~/.rava`, containing all session data.

The generation of random byte files is described in the next section.

### RAVA Random File Generation

To generate files containing random bytes, use the data acquisition module of the [python driver](https://github.com/gabrielguerrer/rng_rava_driver_py) is used. To run it, activate the enviroment and run:

``` 
python3 -m rng_rava.tk.acq
```

Click on "Acquisition", then navigate to the "Bytes" tab.
Select the output path for the generated data and specify the ammount of random bytes to be generated.
No post-processing is required. Set "RNG Out" as "AB" to generate two separate files, one for each randomness core.
Click "Generate". A progress window will appear, showing the evolution of the data generation.

![RAVA byte generation screen](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/byte_file_generation.png)


## FAQ

### The instructions during the initial 3 minutes and in the star rating are in Portuguese. How can they be changed?

After downloading and extracting the v1.0 release: 
- Modify the `./src/anom_int_2024/experiments/exp_parameters.py` file by updating the `TXT_SESS_*` and `TXT_STAR_*` variables accordingly

Proceed with the build and installation as usual.
```
pip install build
python3 -m build
pip install dist/anom_int_2024-1.0-py3-none-any.whl
```

### Is it possible to use this software framework with RAVA firmware v2.0.0?

Yes. After downloading and extracting the v1.0 release: 
- Modify the `./pyproject.toml` file by updating the `rng_rava` dependency from version `1.2.1` to `2.0.0`
- Modify the `./src/anom_int_2024/experiments/exp_parameters.py` file by replacing `D_PWM_FREQ` to `D_PWM_BOOST_FREQ` in lines 17 and 67
- Modify the `./src/anom_int_2024/experiments/exp_base.py` file by replacing `self.rng.snd_pwm_setup` to `self.rng.snd_pwm_boost_setup` in line 114
- Modify the `./src/anom_int_2024/simulations/rng_from_file.py` file by replacing `def snd_pwm_setup` to `def snd_pwm_boost_setup` in line 46

Proceed with the build and installation as usual, the framework should then work as expected.
```
pip install build
python3 -m build
pip install dist/anom_int_2024-1.0-py3-none-any.whl
```

## Contact

gabrielguerrer [at] gmail [dot] com

![RAVA logo](https://github.com/gabrielguerrer/rng_rava/blob/main/images/rng_rava_logo.png)