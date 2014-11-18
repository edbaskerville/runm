runm
====
A script for running or submitting parameter sweeps for computational jobs.

Ed Baskerville

5 June 2014

## Warning

This code is updated rarely and sometimes hurriedly. This documentation may be incomplete.

## Pronunciation

"Run 'em."

## Purpose

The purpose of the runm script is to automate the running or submission of computational jobs with many combinations of different parameters, i.e., parameter sweeps. It is intended as a very lightweight replacement for GridSweeper, which I won't even link to because you should use this instead.

The script contains no dependencies whatsoever on any grid submission system, which means two things: (1) it hopefully won't stop working; and (2) it does not have sophisticated job monitoring/notification capabilities, although some of that is still possible, and more may be added.

## Requirements

Runm requires Python 2.7.x. Tested on Mac OS X and Linux with Python 2.7.x. Has not been tested with Python 3.x. Runm might work on Windows---it should use the appropriate platform-independent path tools---but has not been tested there.

## Installation

To install, copy `runm.py` wherever you like on the machine you submit jobs from. Then make sure it's executable using
```
chmod +x /path/to/runm.py
```

## Configuration Files

To set up a parameter sweep, you start by writing a configuration file. Runm uses configuration files in [JSON][] format. Single-line comments are allowed, starting with `//`.

[JSON]: http://json.org

A nearly useful configuration file looks like this:

```javascript
{
	"name" : "jobname",
	"runs" : 3,
	"resultsDirectory" : "results",
	"submitCommand" : "echo ${RUNM_CONSTANT_ARGS} ${RUNM_SWEEP_ARGS}",
	"parametersFilename" : "parameters.csv",
	
	"constants" : {
		"alpha" : 1
		"beta" : 2
	},
	
	"sweeps" : [
		{
			"type" : "sequence",
			"parameter" : "gamma",
			"from" : 0.0,
			"to" : 0.2,
			"by" : 0.1
		},
		{
			"type" : "sequence",
			"parameter": "delta",
			"from" : 0.1,
			"to" : 0.3,
			"by" : 0.1
		}
	]
}

```

This specifies a parameter sweep that changes `gamma` and `delta` while holding `alpha` and `beta` constant. Additionally, for every combination of parameter values, three runs will be performed, as specified by `runs`. Each run gets its own working directory, and the submission command will be run in that working directory.


### Parameter sweeps

Parameter sweeps are specified in a list of sub-sweeps, which are either sequences, lists of values, or parallel/combination meta-sweeps, e.g.,
```json
{
// ...
	"sweeps" : [
		{
			"type" : "sequence",
			"parameter" : "gamma",
			"from" : 0.0,
			"to" : 0.2,
			"by" : 0.1
		},
		{
			"type" : "sequence",
			"parameter": "delta",
			"from" : 0.1,
			"to" : 0.3,
			"by" : 0.1
		}
	]
}
```
At the top level, all possible combinations of values in the different sequences and lists are produced. The order of the parameters is maintained, and the parameter values change in that order: the last parameter "changes fastest."

### Sequences

Sequences are specified via, e.g.,
```json
{
	"type" : "sequence",
	"parameter" : "delta",
	"from" : 0.1,
	"to" : 0.3,
	"by" : 0.1
}
```
and produce evenly spaced sequences from a starting value specified by `from` to an ending value specified by `to`, spaced evenly at a distance specified with `by`. If `from` is an integer multiple of `by` away from `to` (who's on first), it will be included. If not, it will be omitted. All values are parsed as strings, manipulated via decimal arithmetic, and outputted as strings to ensure that sequences are generated with exactly the precision specified.

The example will produce a sequence of values `(0.1, 0.2, 0.3)` for parameter `delta`.

### Lists

Lists are specified via
```json
{
	"type" : "list",
	"parameter" : "gamma",
	"values" : [5, 75, 89]
}
```
and produce the list exactly as specified.

### Parallel sweeps

Parallel sweeps are specified via, e.g.,
```json
{
	"type" : "parallel",
	"sweeps" : [
		{
			"type" : "list",
			"parameter" : "shoeColor",
			"values" : ["red", "green", "blue"]
		},
		{
			"type" : "sequence",
			"parameter" : "temperature",
			"from" : 75,
			"to" : 79,
			"by" : 2
		}
	]
}
```
Both of the sub-sweeps consist of three values; the parallel sweep assigns the value in each sub-sweep to a parameter combination at each index, so that there will be three parameter combinations produced: `["red", 75]`, `["green", 77"], and `["blue", 79]`.

### Combination sweeps

Combination sweeps behave like the top-level sweep, and produce all combinations of parameters provided. E.g.,
```json
{
	"type" : "combination",
	"sweeps" : [
		{
			"type" : "list",
			"parameter" : "shoeColor",
			"values" : ["red", "green"]
		},
		{
			"type" : "sequence",
			"parameter" : "temperature",
			"from" : 75,
			"to" : 77,
			"by" : 2
		}
	]
}
```
will produce four combinations of parameters: `["red", 75]`, `["red", 77]`, `["green", 75]`, and `["green", 77]`.

## Submitting jobs

If the filename of the configuration file is `config.json`, you can submit it using
```
runm.py submit config.json
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
```json
"submitCommand" : "simulate_the_universe.sh"
```

Furthermore, you can run multiple jobs in parallel by specifying the `threadCount` parameter in the configuration file. For example, if you have an 8-core machine, you can have 8 of your local jobs run at full speed at a time via:
```
"threadCount" : 8
```
As soon as a job finishes, the next waiting job will start.

### Submitting a job to a cluster

If you want to submit a parameter sweep to a cluster, the easiest way to do it is to write a job submission file in the usual format for your system, and then set the `submitCommand` to the submission command for your cluster, passing along important environment variables.

For example, if you use the PBS system, and have a job script file `run.pbs` in the same directory as your runm configuration file, you'd set `submit-command` to this:
```json
"submitCommand" : "qsub -N ${RUNM_RUN_NAME} -d ${RUNM_RUN_DIR} ${RUNM_CONFIG_DIR}/run.pbs"
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

### Job monitoring

Runm can also be used for very simple job monitoring, by having job scripts call `runm.py job start` when they start, and `runm.py job end` when they finish, e.g.,

```sh
#!/bin/sh
#PBS -m a
#PBS -M ed@example.org
#PBS -q eeb
#PBS -l nodes=1:ppn=8
#PBS -l walltime=0:00:10
#PBS -V

runm.py job start
echo ${RUNM_CONSTANT_ARGS} ${RUNM_SWEEP_ARGS}
runm.py job end
```

Then, running
```sh
runm.py status
```
in a run directory will recursively tally how many jobs are submitted, running, and complete and report information about each job as well as a summary.

### Configuration file options

See comments in example below for an explanation of all options:

```javascript
{
	// jobname
	// Job name, used as a basis for names of individual runs.
	// default: "runm"
	"name" : "jobname",
	
	// submitCommand
	// Command to run in each run directory, e.g. to submit the job to the cluster.
	"submitCommand" : "qsub -N ${RUNM_RUN_NAME} -d ${RUNM_RUN_DIR} ${RUNM_CONFIG_DIR}/run.pbs"
	
	// parametersFilename
	// Name of file to write parameters to in each run directory. File can be written in
	// JSON or CSV format.
	// default: "parameters.json"
	"parametersFilename" : "parameters.json",
	
	// parametersFormat
	// Format of file to write parameters to in each run directory.
	// default: as specified by file extension (json or csv)
	"parametersFormat" : "json",
	
	// runs
	// Number of runs to perform with different randm seeds.
	// default: 1
	"runs" : 1,
	
	// dry
	// If true, performs a "dry run": creates subdirectories for each run,
	// but does not actuall perform the submission command.
	// default: false
	"dry" : false,
	
	// resultsDirectory
	// Top-level directory to hold results, absolute or relative to location of configuration file.
	// default: "."
	"resultsDirectory" : "results",
	
	// makeRunNameDirectory
	// Whether or not to create a sub-directory in the results directory for this job.
	// default: true
	"makeRunNameDirectory" : true,
	
	// makeTimestampDirectory
	// Whether or not to create a sub-directory for each job submission named using the submission time.
	// default: true
	"makeTimestampDirectory" : true,
	
	// useExistingRootDirectory
	// Whether or not to use an existing root directory from a previously run job.
	// default: false
	"useExistingRootDirectory" : false,
	
	// existingRootDirectory
	// The path to an existing root directory from a previously run job.
	// default: null
	"existingRootDirectory" : "results/jobname/2014.06.06-01.08.05",
	
	// commandLineArgumentPrefix
	// For jobs specifying parameters using command-line arguments, a prefix before
	// parameter specifications.
	// default: ""
	"commandLineArgumentPrefix" : "",
	
	// commandLineArgumentDelimiter
	// For jobs specifying parameters using command-line-arguments, a delimiter to place
	// between parameter names and values.
	// default: "="
	"commandLineArgumentDelimiter" : "=",
	
	// randomSeedParameterName
	// Name of parameter in which to supply seed for a random number generator.
	// default: "randomSeed"
	"randomSeedParameterName" : "randomSeed",
	
	// randomSeedBits
	// Number of bits in generated random seed value.
	// default: 16
	"randomSeedBits" : "16",
	
	// runNumberParameterName
	// Name of parameter in which to supply the run number (1-indexed)
	// default: "run"
	"runNumberParameterName" : "run",
	
	// threadCount
	// Number of threads to run submission commands on. If the submission command
	// actually performs a long-running task on the local machine, up to threadCount
	// tasks can be performed simultaneously. That is, runm can be used to locally
	// parallelize multiple runs.
	// For submitting jobs to a cluster, this should be left set to 1.
	"threadCount" : 1,
	
	// useEnvironmentVariables
	// If true, sets an environment variable for each parameter.
	// default: false
	"useEnvironmentVariables" : false,
	
	// constants
	// Dictionary of parameters to give constant default values. These values can 
	// be overridden by parameter sweeps and by values provided in an external constants
	// file.
	"constants" : {
		"alpha" : 1,
		"beta" : 2
	}
	
	// constantsFilename
	// Filename of external JSON-formatted constants dictionary. These values will override
	// constants in the configuration file, and will be overridden by parameter sweeps.
	"constantsFilename" : "constant_parameters.json",
	
	// sweeps
	// Array of parameter sweeps.
	"sweeps" : [
		{
			"type" : "sequence",
			"parameter" : "gamma",
			"from" : 5,
			"to" : 10,
			"by" : "1"
		},
		{
			"type" : "list",
			"parameter" : "delta",
			"values" : [0.5, 0.9, 1.1]
		},
		{
			"type" : "parallel",
			"sweeps" : [
				{
					"type" : "list",
					"parameter" : "chi",
					"values" : [1, 2, 3, 4, 5]
				},
				{
					"type" : "list",
					"parameter" : "psi",
					"values" : [4, 9, 16, 25, 36]
				}
			]
		}
	]
}
```
