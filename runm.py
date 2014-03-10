#!/usr/bin/env python

import os
import sys
from multiprocessing.pool import Pool
from Queue import Queue
import subprocess
import yaml
import json
import csv
from collections import OrderedDict
from cStringIO import StringIO
from datetime import datetime
from decimal import Decimal
import random

def makePathRelativeTo(path, basePath):
	path = os.path.expanduser(path)
	if not os.path.isabs(path):
		path = os.path.abspath(os.path.join(os.path.dirname(basePath), path))
	return path
		
def writeJson(obj, filename):
	tmpFilename = filename + '~'
	jsonFile = open(tmpFilename, 'w')
	json.dump(obj, jsonFile, indent=2)
	jsonFile.write('\n')
	jsonFile.close()
	os.rename(tmpFilename, filename)

def readJson(filename):
	lines = list()
	with open(filename) as jsonFile:
		for line in jsonFile:
			lines.append(line.rstrip('\n').split('//')[0])
	jsonStr = '\n'.join(lines)
	obj = json.loads(jsonStr, object_pairs_hook=OrderedDict)
	return obj

def runShellCommand(command, path, env):
	process = subprocess.Popen(
		args=[command],
		shell=True,
		cwd=path,
		env=env,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)
	stdoutData, stderrData = process.communicate()
	error = process.returncode
	return (error, stdoutData, stderrData)

def runSubmitCommandAsync(submitCommand, runPath, env, errorFilename, stdoutFilename, stderrFilename):
	writeJson({'status' : 'SUBMITTED'}, os.path.join(runPath, 'runm_status.json'))
	
	error, stdoutData, stderrData = runShellCommand(submitCommand, runPath, env)
	
	if error != 0:
		errorFile = open(errorFilename, 'w')
		errorFile.write(str(error))
		errorFile.write('\n')
		errorFile.close()
	
	if len(stdoutData) > 0:
		stdoutFile = open(stdoutFilename, 'w')
		stdoutFile.write(stdoutData)
		stdoutFile.close()
	
	if len(stderrData) > 0:
		stderrFile = open(stderrFilename, 'w')
		stderrFile.write(stderrData)
		stderrFile.close()
	
	return (error, stdoutData, stderrData)

def isTrue(val):
	return val in (True, 'Yes', 'YES', 'yes', 'True', 'TRUE', 'true')

def isFalse(val):
	return val in (False, 'No', 'NO', 'no', 'False', 'FALSE', 'false')

def stringConstructor(loader, node):
	print node.value
	return node.value

def loadConfigFile(filename, args):
	linesOut = StringIO()
	linesOut.write('!runm\n')
	for line in open(filename):
		linesOut.write(line.expandtabs(1))
	linesOut.seek(0)
	
	yaml.add_constructor(u'!!str', stringConstructor)
	
	# Hack to make sure YAML treats ALL scalars as strings so
	# so we can do decimal math
	yaml.resolver.Resolver.yaml_implicit_resolvers = {}
	
	# Resolve paths
	def pathConstructor(loader, node):
		path = makePathRelativeTo(node.value, filename)
		return path
	yaml.add_constructor(u'!path', pathConstructor)
	
	config = yaml.load(linesOut)
	config.filename = os.path.abspath(filename)
	
	for arg in args:
		if arg == '--dry':
			config.dry = True

	return config

def getNumberFormatFromDecimals(xList):
	maxBefore = 1
	maxAfter = 0
	
	for x in xList:
		xTuple = x.as_tuple()
		digitCount = len(xTuple.digits)
		maxBefore = max(maxBefore, max(1, digitCount + xTuple.exponent))
		maxAfter = max(maxAfter, max(0, -xTuple.exponent))
	
	if(maxAfter == 0):
		width = maxBefore
	else:
		width = maxBefore + maxAfter + 1
	
	if maxAfter == 0:
		return '{0:' + '0{0}f'.format(width) + '}'
	else:
		return '{0:' + '0{0}.{1}f'.format(width, maxAfter) + '}'

def makeHierarchicalDict(d):
	hd = OrderedDict()
	
	for k, v in d.items():
		subks = k.split('.')
		subd = hd
		for i, subk in enumerate(subks):
			if i == len(subks) - 1:
				subd[subk] = v
			else:
				if not subk in subd:
					subd[subk] = OrderedDict()
				subd = subd[subk]
	
	return hd

class Config(yaml.YAMLObject):
	yaml_tag = u'!runm'
	
	# Parameters whose names are usable as field names are just fields
	name = 'runm'
	runs = 1
	dry = False
	filename = ''
	
	def getThreadCount(self):
		try:
			return getattr(self, 'thread-count')
		except:
			return 1
	threadCount = property(getThreadCount)
	
	constants = {}
	
	def getConstantsFilename(self):
		try:
			return getattr(self, 'constants-filename')
		except:
			return None
	constantsFilename = property(getConstantsFilename)
	
	_allConstants = None
	
	def getAllConstants(self):
		if self._allConstants is None:
			self._allConstants = OrderedDict()
			self._allConstants.update(self.constants)
			if self.constantsFilename is not None:
				constantsFromFile = readJson(self.constantsFilename)
				self._allConstants.update(constantsFromFile)
		return self._allConstants
	allConstants = property(getAllConstants)
		
	
	def getSubmitCommand(self):
		try:
			return getattr(self, 'submit-command')
		except:
			return None
	submitCommand = property(getSubmitCommand)
	
	def getResultsDirectory(self):
		try:
			return getattr(self, 'results-directory')
		except:
			return '.' 
	resultsDirectory = property(getResultsDirectory)
	
	def getMakeRunDirectory(self):
		try:
			return isTrue(getattr(self, 'make-run-directory'))
		except:
			return True
	makeRunDirectory = property(getMakeRunDirectory)

	def getMakeSubdirectory(self):
		try:
			return isTrue(getattr(self, 'make-subdirectory'))
		except:
			return True
	makeSubdirectory = property(getMakeSubdirectory)
	
	def getUseExistingDirectories(self):
		try:
			return isTrue(getattr(self, 'use-existing-directories'))
		except:
			return False
	useExistingDirectories = property(getUseExistingDirectories)

	def getCommandLineArgumentPrefix(self):
		try:
			return getattr(self, 'command-line-argument-prefix')
		except:
			return ''
	commandLineArgumentPrefix = property(getCommandLineArgumentPrefix)
	
	def getCommandLineArgumentDelimiter(self):
		try:
			return getattr(self, 'command-line-argument-delimiter')
		except:
			return '='
	commandLineArgumentDelimiter = property(getCommandLineArgumentDelimiter)
	
	def getUseEnvironmentVariables(self):
		try:
			return isTrue(getattr(self, 'use-environment-variables'))
		except:
			return False
	useEnvironmentVariables = property(getUseEnvironmentVariables)
	
	def getParametersFilename(self):
		try:
			return getattr(self, 'parameters-filename')
		except:
			return 'parameters.csv'
	parametersFilename = property(getParametersFilename)
	
	def getParametersFormat(self):
		try:
			return getattr(self, 'parameters-format')
		except:
			return os.path.splitext(self.parametersFilename)[1][1:]
	parametersFormat = property(getParametersFormat)
	
	def getRandomSeedParameterName(self):
		try:
			return getattr(self, 'random-seed-parameter-name')
		except:
			return 'seed'
	randomSeedParameterName = property(getRandomSeedParameterName)
	
	def getRandomSeedBits(self):
		try:
			return getattr(self, 'random-seed-bits')
		except:
			return 16
	randomSeedBits = property(getRandomSeedBits)
	
	def getRunNumberParameterName(self):
		try:
			return getattr(self, 'run-number-parameter-name')
		except:
			return 'run'
	runNumberParameterName = property(getRunNumberParameterName)
	
	def parameterDicts(self):
		topCombinationSweep = Combination(self.sweeps)
		for combination in topCombinationSweep.parameterDicts():
			yield combination
	
	def generateRootDirectory(self):
		pathComponents = []
		pathComponents.append(self.resultsDirectory)
		if self.makeSubdirectory:
			pathComponents.append(self.name)
		if self.makeRunDirectory:
			pathComponents.append(datetime.now().strftime('%Y.%m.%d-%H.%M.%S'))
		
		return makePathRelativeTo(os.path.join(*pathComponents), self.filename)


class Sequence(yaml.YAMLObject):
	yaml_tag = u'!sequence'
	
	def getStart(self):
		try:
			return getattr(self, 'from')
		except:
			return None
	start = property(getStart)
	
	def getEnd(self):
		try:
			return getattr(self, 'to')
		except:
			return None
	end = property(getEnd)
	
	def parameterDicts(self):
		startDec = Decimal(self.start)
		endDec = Decimal(self.end)
		byDec = Decimal(self.by)
		
		formatStr = getNumberFormatFromDecimals([startDec, endDec, byDec])
		
		value = startDec
		while value <= endDec:
			yield { self.parameter : formatStr.format(value) }
			value = value + byDec

class List(yaml.YAMLObject):
	yaml_tag = u'!list'
	
	def parameterDicts(self):
		for value in self.values:
			yield { self.parameter : value }

class Parallel(yaml.YAMLObject):
	yaml_tag = u'!parallel'
	
	def parameterDicts(self):
		# One iterator for each sweep
		iterators = [sweep.parameterDicts() for sweep in self.sweeps]
		
		# Iterate in parallel across sweeps
		# If one of them comes up short, the final entry will just be repeated
		combination = OrderedDict()
		while(True):
			doneCount = 0
			for iterator in iterators:
				try:
					combination.update(iterator.next())
				except StopIteration:
					doneCount += 1
			if doneCount == len(iterators):
				break
			yield combination.copy()

class Combination(yaml.YAMLObject):
	yaml_tag = u'!combination'
	
	def __init__(self, sweeps):
		self.sweeps = sweeps
	
	def parameterDicts(self):
		# One iterator for each sweep
		iterators = [sweep.parameterDicts() for sweep in self.sweeps]
		
		# Iterate across all combinations
		level = 0
		combination = OrderedDict()
		while(True):
			try:
				combination.update(iterators[level].next())
				
				if level == len(self.sweeps) - 1:
					yield combination.copy()
				else:
					level += 1
			except StopIteration:
				if level == 0:
					break
				iterators[level] = self.sweeps[level].parameterDicts()
				level -= 1

class RunmSubmit:
	def __init__(self, config):
		self.config = config
		self.runNumFormat = '{0:0' + '{0}d'.format(len(self.config.runs)) + '}'
		self.pool = Pool(int(self.config.threadCount))
	
	def run(self):
		# Create root directory inside results directory
		rootDir = self.config.generateRootDirectory() 
		
		# Set up results queue
		self.results = Queue()
		
		# Create directory and submit job for each parameter combination X run 
		for pDict in self.config.parameterDicts():
			baseJobName = '-'.join(['{0}={1}'.format(param, value) for param, value in pDict.items()])
			self.runJobsForParams(pDict, baseJobName, rootDir)
		
		print('---\nWaiting for submission to complete...---')
		while not self.results.empty():
			jobName, result = self.results.get()
			
			returnCode, stdoutData, stderrData = result.get()
			print 'Completed submission {0}'.format(jobName)
			
			if returnCode != 0:
				print 'ERROR: submission returned nonzero code {0}'.format(returnCode)
			if len(stdoutData) > 0:
				sys.stdout.write(stdoutData)
			if len(stderrData) > 0:
				sys.stdout.write(stderrData)
			print '---'
		
		self.pool.close()
		self.pool.join()
		print("Submission complete.")

	def rerun(self, runPath):
		env = OrderedDict(os.environ)
		env['RUNM_RUN_NAME'] = '{0}-{1}'.format(self.config.name, 'rerun')
		env['RUNM_RUN_DIR'] = str(runPath)

		env['RUNM_CONFIG_FILE'] = self.config.filename
		env['RUNM_CONFIG_DIR'] = os.path.dirname(self.config.filename)
		
		print 'Submitting job {0}...'.format(self.config.name)
		
		errorFilename = os.path.join(runPath, 'runm_submit_returncode')
		stdoutFilename = os.path.join(runPath, 'runm_submit_stdout')
		stderrFilename = os.path.join(runPath, 'runm_submit_stderr')
		
		runSubmitCommandAsync(self.config.submitCommand, runPath, env, errorFilename, stdoutFilename, stderrFilename)

	def runJobsForParams(self, pDict, baseJobName, rootDir):
		basePath = os.path.join(rootDir, baseJobName)
		for i in range(int(self.config.runs)):
			runNumStr = self.runNumFormat.format(i+1)
			
			if int(self.config.runs) == 1:
				runPath = basePath
				jobName = baseJobName
			else:
				runPath = os.path.join(basePath, runNumStr)
				jobName = '{0}-{1}'.format(baseJobName, runNumStr)
			
			# Generate output directory for job
			try:
				os.makedirs(runPath)
			except os.error as e:
				if not self.config.useExistingDirectories:
					print 'Error creating directory\n  {0}\nAborting.'.format(runPath)
					print e
					sys.exit(1)
			
			# Get random seed with however many bits were requested
			seedStr = self.generateSeed()
			
			# Write out parameter file
			self.writeParams(runPath, pDict, runNumStr, seedStr)
			
			# Actually submit the job
			self.submitJob(jobName, runPath, pDict, runNumStr, seedStr)
	
	def writeParams(self, runPath, pDict, runNumStr, seedStr):
		paramFilename = os.path.join(runPath, self.config.parametersFilename)
		
		runPDict = OrderedDict()
		runPDict.update(self.config.allConstants)
		runPDict[self.config.runNumberParameterName] = runNumStr
		runPDict[self.config.randomSeedParameterName] = seedStr
		runPDict.update(pDict)
		
		if self.config.parametersFormat == 'json':
			runPDictHierarchical = makeHierarchicalDict(runPDict)
			
			jsonFile = open(paramFilename, 'w')
			json.dump(runPDictHierarchical, jsonFile, indent=2)
			jsonFile.write('\n')
			jsonFile.close()
		elif self.config.parametersFormat == 'csv':
			csvFile = open(paramFilename, 'w')
			csvWriter = csv.writer(csvFile)
			for key, value in runPDict.items():
				csvWriter.writerow((key, value))
			csvFile.close()
		elif self.config.parametersFormat == 'txt':
			csvFile = open(paramFilename, 'w')
			csvWriter = csv.writer(csvFile, delimiter='\t')
			for key, value in runPDict.items():
				csvWriter.writerow((key, value))
			csvFile.close()
	
	
	def makeCommandLineArguments(self, pDict):
		argList = list()
		for k, v in pDict.items():
			argList.append(str('{0}{1}{2}{3}'.format(
				self.config.commandLineArgumentPrefix,
				k,
				self.config.commandLineArgumentDelimiter,
				v
			)))
		return ' '.join(argList)

	def submitJob(self, jobName, runPath, pDict, runNumStr, seedStr):
		env = OrderedDict(os.environ)
		env['RUNM_RUN_NAME'] = '{0}-{1}'.format(self.config.name, str(jobName))
		env['RUNM_RUN_DIR'] = str(runPath)

		if runNumStr is not None:
			env['RUNM_RUN_NUM'] = str(runNumStr)
		if seedStr is not None:
			env['RUNM_RUN_SEED'] = str(seedStr)
		env['RUNM_CONFIG_FILE'] = self.config.filename
		env['RUNM_CONFIG_DIR'] = os.path.dirname(self.config.filename)
		if self.config.useEnvironmentVariables:
			for k, v in pDict.items():
				env[k] = v
		
		if pDict is not None:
			env['RUNM_CONSTANT_ARGS'] = self.makeCommandLineArguments(self.config.constants)
			env['RUNM_SWEEP_ARGS'] = self.makeCommandLineArguments(pDict)
		
		print 'Submitting job {0}...'.format(jobName)
		
		errorFilename = os.path.join(runPath, 'runm_submit_returncode')
		stdoutFilename = os.path.join(runPath, 'runm_submit_stdout')
		stderrFilename = os.path.join(runPath, 'runm_submit_stderr')
		
		if isFalse(self.config.dry):
			result = self.pool.apply_async(runSubmitCommandAsync,
				(self.config.submitCommand, runPath, env,
				errorFilename, stdoutFilename, stderrFilename))
			self.results.put((jobName, result), block=True)
	
	def generateSeed(self):
		return str(random.SystemRandom().getrandbits(int(self.config.randomSeedBits)))

def runmSubmit(argv):
	config = loadConfigFile(argv[0], argv[1:])
	RunmSubmit(config).run()

def runmResubmit(argv):
	config = loadConfigFile(argv[0], argv[2:])
	RunmSubmit(config).rerun(argv[1])

def runmJobStart(argv):
	writeJson({'status' : 'RUNNING'}, 'runm_status.json')
	
def runmJobEnd(argv):
	writeJson({'status' : 'DONE'}, 'runm_status.json')

def runmJobError(argv):
	resultDict = OrderedDict()
	resultDict['status'] = 'ERROR'
	if len(argv) > 0:
		resultDict['message'] = argv[0]
	writeJson(resultDict, 'runm_status.json')

def runmStatus(argv):
	if len(argv) > 0:
		path = argv[0]
	else:
		path = '.'
	
	# Walk directory to look at status for each job
	count = 0
	submittedCount = 0
	runningCount = 0
	doneCount = 0
	errorCount = 0
	for dirpath, dirnames, filenames in os.walk(path):
		statusPath = os.path.join(dirpath, 'runm_status.json')
		
		if os.path.exists(statusPath):
			print dirpath
			try:
				count += 1
				statusDict = readJson(statusPath)
				status = statusDict['status']
				if status == 'SUBMITTED':
					submittedCount += 1
					print 'Waiting.'
				elif status == 'RUNNING':
					runningCount += 1
					print 'Running.'
				elif status == 'DONE':
					doneCount += 1
					print 'Successful.'
				elif status == 'ERROR':
					errorCount += 1
					if 'message' in statusDict:
						print 'Error: {0}'.format(statusDict['message'])
					else:
						print 'Error.' 
			except:
				print 'Unable to read status'
			print '---'
	
	# Report status summary
	countWidth = len(str(count))
	tableFormat = '{0} ' + '{1:' + str(countWidth) + 'd} ' + '{2}'
	percentFormat = '({0:.0f}%)'
	print tableFormat.format(
		'Successful:'.rjust(11),
		doneCount, percentFormat.format(100*float(doneCount)/count).rjust(6)
	)
	print tableFormat.format(
		'Error:'.rjust(11),
		errorCount, percentFormat.format(100*float(errorCount)/count).rjust(6)
	)
	print tableFormat.format(
		'Waiting:'.rjust(11),
		submittedCount, percentFormat.format(100*float(submittedCount)/count).rjust(6)
	)
	print tableFormat.format(
		'Running:'.rjust(11),
		runningCount, percentFormat.format(100*float(runningCount)/count).rjust(6)
	)
	print '-' * (12 + countWidth + 7)
	print tableFormat.format(
		'Total:'.rjust(11),
		count, '(100%)'
	) 

def printUsage():
	print('Usage:')
	print('  {0} submit <config-file>').format(sys.argv[0])
	print('  {0} resubmit <config-file> <run-dir>').format(sys.argv[0])
	print('  {0} status <dir>').format(sys.argv[0])

if __name__ == '__main__':
	if len(sys.argv) < 2:
		printUsage()
		sys.exit(1)
	
	command = sys.argv[1]
	
	if command == 'submit':
		runmSubmit(sys.argv[2:])
	elif command == 'resubmit':
		runmResubmit(sys.argv[2:])
	elif command == 'status':
		runmStatus(sys.argv[2:])
	elif command == 'job':
		if(len(sys.argv) < 3):
			printUsage()
			sys.exit(1)
		subCommand = sys.argv[2]
		if subCommand == 'start':
			runmJobStart(sys.argv[3:])
		elif subCommand == 'end':
			runmJobEnd(sys.argv[3:])
		elif subCommand == 'error':
			runmJobError(sys.argv[3:])
	elif command == 'continue':
		runmContinue(sys.argv[2:])
	else:
		printUsage()
