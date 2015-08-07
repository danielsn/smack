#!/usr/bin/python

import sys
import re
from paramParser import *
from ToolRun import *
sys.dont_write_bytecode = True # prevent creation of .pyc files

### A ToolRun derived class for running SMACK in ParamILS framework
class SmackToolRun(ToolRun):
    ###For SMACK, returns a list of Param objects, with all params to be passed
    ###on to verifier collected into a single 
    ###--verifier-options="<allVerOptsHere>" parameter
    def argHelper(rawArgs):
        params = parseParams(extraArgs)
        #Get z3 args
        z3Params = filterParams('Z3', params)
        wrappedZ3Params = [wrapZ3param('BOOGIE',p) for p in z3Params]
        #Get boogie args, plus wrapped z3 args
        boogieParams = filterParams('BOOGIE', params) + wrappedZ3Params
        corralParams = filterParams('CORRAL', params)
        #Get smack specific args
        others = [p for p in params if (p not in z3Params     and
                                        p not in boogieParams and
                                        p not in corralParams)]
        #Join all boogie  corral params into a space delimited string
        verArgStr = " ".join([p.asStringList()[0] for p in (boogieParams + 
                                                            corralParams)])
        #Add verifier-options param (as switch, since it must be all one word)
        others.append(Param('SMACK', 'verifier-options="' + verArgStr + '"',
                            'True', True))
        return param2cmdArgList(others)
    
    def prepareCmd(self, inputFile, rest, cutoffTime, 
                    cutoffLength, seed, rawArgs):
        cmd =  ['smackverify.py', inputFile]
        cmd += ['--time-limit',   str(cutoffTime)]
        cmd += argHelper(rawArgs)
        return cmd

    ###Parse output of SMACK to determine whether we got the right outcome
    def parseOutput(inputFilename, output):
        #Get expected result
        expected = True
        if    (re.search(r'[fF]ail', inputFilename) or 
               re.search(r'[fF]alse', inputFilename)):
            expected = False
            #Get actual result
            passed = False
        reStr = r'[1-9]\d* time out|Z3 ran out of resources|z3 timed out'
        if re.search(reStr, output):
            return 'TIMEOUT'
        elif re.search(r'[1-9]\d* verified, 0 errors?|no bugs', output):
            passed = True
        elif re.search(r'0 verified, [1-9]\d* errors?|can fail', output):
            passed = False
        else:
            #return 'unknown'
            return 'WRONG'
        #Return SAT if passed matched expected
        return 'CORRECT' if passed==expected else 'WRONG'

if __name__ == "__main__":
    smackRun = SmackToolRun(sys.argv)
    smackRun.executeRun()
    smackRun.printResults()