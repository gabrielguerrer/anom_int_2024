# Anomalous Interactions 2024

This software framework supports the research titled "Investigating the Claim of Anomalous Psychophysical Interactions Using a Rigorous Metascientific Framework".  
It provides functionality for simulations, data collection, and data analysis.

Relevant links:
- [OSF Project](https://osf.io/vuscn) : It includes the two preregistration documents, the collected data, and a preprint describing the study’s findings.
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

The database files are located in the `~/.rava` directory.

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


## Results

To reproduce the results obtained in the preregistered studies:

- Download the study data from the [OSF Project](https://osf.io/vuscn) website
- As described above, activate the environment and run the analysis module using `python3 -m anom_int_2024.analysis`
- In the "database" section, click "..." to select the `.db` file, then click "Connect"
- In the "filter" section, the `sess_group` variable specifies whether the data correspond to the first or second preregistered study. The `sess_type` variable selects one of the four experiments 
  - Choose the desired study (PR1 or PR2) and experiment
- In the "analysis" section, under the "prereg" tab, click "Analyze". The probability outcomes for participant and sham sessions are displayed in the "results" box

![Analysis](https://github.com/gabrielguerrer/anom_int_2024/blob/main/images/analysis.png)

## Contact

gabrielguerrer [at] gmail [dot] com

![RAVA logo](https://github.com/gabrielguerrer/rng_rava/blob/main/images/rng_rava_logo.png)