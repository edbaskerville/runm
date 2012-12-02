runm
====

## Pronunciation

"Run 'em."

## Purpose

The purpose of the runm script is to automate the submission of computational jobs with many combinations of different parameters, i.e., parameter sweeps. It is intended as a very lightweight replacement for GridSweeper, which I won't even link to because you should use this instead.

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
	from: 0
	to: 0.3
	by: 0.1
- !sequence
	parameter: delta
	from: 0.1
	to: 0.3
	by: 0.1
```

