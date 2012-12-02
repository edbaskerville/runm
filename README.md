runm
====
A script for running or submitting parameter sweeps for computational jobs.

Ed Baskerville
2 December 2012

## Pronunciation

"Run 'em."

## Purpose

The purpose of the runm script is to automate the running or submission of computational jobs with many combinations of different parameters, i.e., parameter sweeps. It is intended as a very lightweight replacement for GridSweeper, which I won't even link to because you should use this instead.

The script contains no dependencies whatsoever on any grid submission system, which means two things: (1) it hopefully won't stop working; and (2) it does not have sophisticated job monitoring/notification capabilities, although some of that is still possible, and more may be added.

## Requirements

Runm requires Python 2.7.x and PyYAML. Tested on Mac OS X and Linux with [Python 2.7.1][] and [PyYAML 3.1.0][]. Has not been tested with Python 3.x. PyYAML is installed by default in the [Enthought Python Distribution][]. Runm might work on Windows---it uses the appropriate platform-independent path tools---but has not been tested there.

[Python 2.7.x]: http://python.org/download/releases/2.7.1
[PyYAML]: http://pyyaml.org/wiki/PyYAML
[Enthought Python Distribution]: http://www.enthought.com/products/epd.php

## Installation

To install, copy `runm.py` wherever you like on the machine you submit jobs from. I recommend somewhere in your search path with the `.py` extension removed. Then make sure it's executable using
```
chmod +x /path/to/runm
```

## Configuration Files

To set up a parameter sweep, you start by writing a configuration file. Runm uses configuration files in [YAML][] format, which is a general-purpose structured data format designed to be easy to read and write.

[YAML]: http://en.wikipedia.org/wiki/YAML#Sample_document

A nearly minimal runm configuration file looks like this:

```yaml
name: jobname
results-directory: results
submit-command: "echo ${RUNM_CONSTANT_ARGS} ${RUNM_SWEEP_ARGS}"
parameters-filename: parameters.csv

constants:
	alpha: 1
	beta: 2

sweeps:
- !sequence
	parameter: gamma
	from: 0.0
	to: 0.2
	by: 0.1
- !sequence
	parameter: delta
	from: 0.1
	to: 0.3
	by: 0.1
```

The constant variables are specified under `constants`, and the variables to produce combinations of are specified under `sweeps`. YAML is a pretty flexible format, so there are many other ways of specifying the same structure. For example, you can use this compact notation instead for the `sweeps` section:
```
sweeps:
- !sequence { parameter: gamma, from: 0.0, to: 0.2, by: 0.1 }
- !sequence { parameter: delta, from: 0.1, to: 0.3, by: 0.1
```

If the filename of this configuration file was `config.yaml`, you can submit it using
```
runm config.yaml
```
and this would result in the creation of a directory hierarchy for results, and would cause the command specified by `submit-command` (in this case, `echo...`) to be run for every combination of parameter values specified inside a directory corresponding to that combination of parameter values. Parameters specified by `constants` will be held the same for every run.

The directory hierarchy will be rooted at `[results-directory]/[name]/[timestamp]`, where `[timestamp]` is the submission date and time in the format `YYYY.MM.DD-HH.MM.SS`. The hierarchy for this job would thus look like, e.g.,
```
/path/to/results/jobname/2012.11.26-12.10.54/
  gamma=0.0-delta=0.1/
  gamma=0.0-delta=0.2/
  gamma=0.0-delta=0.3/
  gamma=0.1-delta=0.1/
  gamma=0.1-delta=0.2/
  gamma=0.1-delta=0.3/
  gamma=0.2-delta=0.1/
  gamma=0.2-delta=0.2/
  gamma=0.2-delta=0.3/
```



## Running a parameter sweep locally

If you have a bunch of relatively quick jobs that you don't want to go through the trouble of submitting to a cluster, you can use runm to run them locally by setting `submit-command` to a command that actually runs the job. If your command reads in the parameters from a file as described above, this might be as simple as a single script:
```
submit-command: simulate_the_universe.sh
```

Furthermore, you can run multiple jobs in parallel by specifying the `thread-count` parameter in the configuration file. For example, if you have an 8-core machine, you can have 8 of your local jobs run at a time via:
```
thread-count: 8
```
As soon as a job finishes, the next waiting job will start.

## Running 

