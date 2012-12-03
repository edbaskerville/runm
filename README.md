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

A nearly useful configuration file looks like this:

```yaml
name: jobname
runs: 3
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

This specifies a parameter sweep that changes `gamma` and `delta` with `alpha` and `beta` held constant. Additionally, for every combination of parameter values, three runs will be performed, as specified by `runs`. Each run gets its own working directory, and the submission command will be run in that working directory.

YAML is a pretty flexible format, so there are many other ways of specifying the same structure. For example, you can use this compact notation instead for the `sweeps` section:
```
sweeps:
- !sequence { parameter: gamma, from: 0.0, to: 0.2, by: 0.1 }
- !sequence { parameter: delta, from: 0.1, to: 0.3, by: 0.1
```

More details:

### Top-level configuration file options

(TODO: generate all these automatically from source file?)

### Parameter sweeps

Parameter sweeps are specified as a list of sub-sweeps, which are either sequences or lists of values, e.g.,
```yaml
sweeps:
- !sequence
	...
- !sequence
	...
- !list
	...
```
All possible combinations of values in the different sequences and lists are produced. The order of the parameters is maintained, and the parameter values change in that order: the last parameter "changes fastest."

### Sequences

Sequences are specified via
```yaml
- !sequence
	parameter: [param-name]
	from: [starting-value]
	to: [ending-value]
	by: [spacing]
```
and produce evenly spaced sequences from a starting value specified by `from` to an ending value specified by `to`, spaced evenly at a distance specified with `by`. If `from` is an integer multiple of `by` away from `to` (who's on first), it will be included. If not, it will be omitted. All values are parsed as strings, manipulated via decimal arithmetic, and outputted as strings to ensure that sequences are generated with exactly the precision specified.

For example,
```yaml
- !sequence
	parameter: alpha
	from: 0.1
	to: 0.3
	by: 0.2
```
will produce a sequence of values `(0.1, 0.2, 0.3)` for parameter `alpha`. Compact notation is also supported:
```yaml
- !sequence { parameter: alpha, from: 0.1, to: 0.3, by: 0.2 }
```

### Lists

Lists are specified via
```yaml
- !list
	parameter: [param-name]
	values:
	- [value1]
	- [value2]
	- [value3]
	- ...
```
and produce the list exactly as specified.

For example,
```yaml
- !list
	parameter: favoriteColor
	values:
	- 5
	- 75
	- santaClaus
	- ...
```
will produce the sequence `(5, 75, santaClaus)` for parameter `favoriteColor`. Compact notation is also supported:
```yaml
- !list { parameter: favoriteColor, values: [5, 75, santaClaus]
```

## Submitting jobs

Here's the configuration file from above, in compact notation:

```yaml
name: jobname
runs: 3
results-directory: results
submit-command: "echo ${RUNM_CONSTANT_ARGS} ${RUNM_SWEEP_ARGS}"
parameters-filename: parameters.csv

constants: {alpha: 1, beta: 2}

sweeps:
- !sequence { parameter: gamma, from: 0.0, to: 0.2, by: 0.1 }
- !sequence { parameter: delta, from: 0.1, to: 0.3, by: 0.1 }
```

If the filename of the configuration file is `config.yaml`, you can submit it using
```
runm submit config.yaml
```
and this results in the creation of a directory hierarchy for results, and causes the command specified by `submit-command` (in this case, `echo...`) to be run for every combination of parameter values specified inside a directory corresponding to that combination of parameter values. Parameters specified by `constants` will be held the same for every run; parameters specified by `sweeps` will be produced in all possible combinations with each other.

The directory hierarchy will be rooted at `[results-directory]/[name]/[timestamp]`, where `[timestamp]` is the submission date and time in the format `YYYY.MM.DD-HH.MM.SS`. The results directory can be an absolute path. If it is a relative path, it will be interpreted relative to the directory that the configuration file resides in.

The hierarchy for this job would thus look like, e.g.,
```
/path/to/results/jobname/2012.11.26-12.10.54/
  gamma=0.0-delta=0.1/
    1/
    2/
    3/
  gamma=0.0-delta=0.2/
    1/
    2/
    3/
  gamma=0.0-delta=0.3/
    1/
    2/
    3/
  gamma=0.1-delta=0.1/
    1/
    2/
    3/
  gamma=0.1-delta=0.2/
    1/
    2/
    3/
  gamma=0.1-delta=0.3/
    1/
    2/
    3/
  gamma=0.2-delta=0.1/
    1/
    2/
    3/
  gamma=0.2-delta=0.2/
    1/
    2/
    3/
  gamma=0.2-delta=0.3/
    1/
    2/
    3/
```

Furthermore, inside each directory a file called `parameters.csv` will be created, and will contain parameter values in CSV format:
```csv
alpha,0.0
beta,0.1
run,1
seed,983584970
```

If the parameters filename has a `.txt` extension, the file will be tab-delimited instead of comma-delimited. And if it has a `.json` extension, it will be produced in [JSON][] format:
```json
{
  "alpha": "0.0", 
  "beta": "0.1", 
  "run": "1", 
  "seed": "1597096899", 
  "gamma": "0.1", 
  "delta": "0.1"
}
```
[JSON]: http://json.org

Note that in addition to the constant parameters and sweep parameters, there is a `run` parameter, which is the "run number" for this run, and a `seed` parameter, which a seed for a random number generator.

Additionally, the submission command will be run with a number of environment variables set to contain information about the run:
* `RUNM_RUN_NAME`: a name for this particular run, which includes parameter values and run number, e.g., `jobname-gamma=0.0-delta=0.1-3`
* `RUNM_RUN_DIR`: the directory for this particular run, e.g., * `/path/to/results/jobname/2012.11.26-12.10.54/gamma=0.0-delta=0.1/3`
* `RUNM_RUN_NUM` = the number of this run
* `RUNM_CONFIG_FILE`: the fully-resolved path of the configuration file
* `RUNM_CONFIG_DIR`: the fully-resolved path of the directory the configuration file resides in
* `RUNM_CONSTANT_ARGS`: a string containing the constant parameter values, in the format, e.g., `alpha=0.0 beta=0.1`, primarily provided for the convenience of programs created for Drone or GridSweeper
* `RUNM_SWEEP_ARGS`: a string containing the sweep parameter values, in the format, e.g., `gamma=0.1 delta=0.2`

### Running a parameter sweep locally

If you have a bunch of relatively quick jobs that you don't want to go through the trouble of submitting to a cluster, you can use runm to run them locally by setting `submit-command` to a command that actually runs the job. If your command reads in the parameters from a file as described above, this might be as simple as a single script:
```yaml
submit-command: simulate_the_universe.sh
```

Furthermore, you can run multiple jobs in parallel by specifying the `thread-count` parameter in the configuration file. For example, if you have an 8-core machine, you can have 8 of your local jobs run at full speed at a time via:
```
thread-count: 8
```
As soon as a job finishes, the next waiting job will start.

### Submitting a job to a cluster

If you want to submit a parameter sweep to a cluster, the easiest way to do it is to write a job submission file in the usual format for your system, and then set the `submit-command` to the submission command for your cluster, passing along important environment variables.

For example, if you use the PBS system, and have a job script file `run.pbs` in the same directory as your runm configuration file, you'd set `submit-command` to this:
```yaml
submit-command: "qsub -N ${RUNM_RUN_NAME} -d ${RUNM_RUN_DIR} ${RUNM_CONFIGDIR}/run.pbs"
```
This will pass the run name along to PBS as the name for the submitted job, and will ensure that the job executes in its specified directory.

If you included the appropriate PBS option (`-V`) to pass along environment variables to the job, you can use runm environment variables there too:
```sh
#!/bin/sh
#PBS -m a
#PBS -M ed@example.org
#PBS -q eeb
#PBS -l nodes=1:ppn=8
#PBS -l walltime=0:00:10
#PBS -V

echo ${RUNM_CONSTANT_ARGS} ${RUNM_SWEEP_ARGS}
```

Note that runm submits a job for every single run, so if you're sweeping three parameters with 10 values each and 10 runs per parameter combination, runm will submit 10,000 jobs to your cluster, which might not be precisely what you want.
