#!/usr/bin/env python3
# Reads a HASH encoding program in single static assignment form and
# spits out a SAT instance for trying to get an input string for a hash value
#
# Interprets the code between "STARTSSA" and "ENDSSA" commands
# 
# All commands in between must be assignments - either to some INT or HEX constants
# or using the result of some function starting with "fn_".
#
# There are few special functions.
# All other function implementations are read from their implementation files

import sys

# SAT encoding parameters
ADDER_GRANUALARITIES = [3]
ADDER_GRANUALARITIES_NO_CARRY_IN = [3,4]
ADDER_GRANUALARITIES_NO_CARRY_OUT = [2,3,4]

# Where to store the encoding
clauses = []
satVarsInput = []
satVarsOutput = []
satVarsSoFar = 1
satFalseLiteral = -1
satTrueLiteral = 1
ssaVars = {}
symbolicInputSSAVars = []
symbolicInputSSAVarsData = {}
varNamesOutput = None

# Allocate constant SAT variable for constants
clauses = [[1]]

# Parse command line input: directory with bitwise implementations.
if len(sys.argv)<2:
    print("Error: Need as parameter the directory with the CNF encodings of the operators.",file=sys.stderr)
    sys.exit(1)
cnfDir = sys.argv[1]

# Parse input file
# All variables are 32-bit int by default!
isInInterestingPartOfTheInputFile = False
allLines = list(sys.stdin.readlines())
for line in allLines:
    line = line.strip()
    if line=="#->STARTSSA":
        isInInterestingPartOfTheInputFile = True
    elif line=="#->ENDSSA":
        isInInterestingPartOfTheInputFile = False
    elif len(line)==0:
        pass
    else:
        # Ok, a line to be parsed
        if line.startswith("#->SYMBOLICBYTE:"):
            varName = line[16:].strip()
            # Allocate Vars
            data = [satVarsSoFar+i for i in range(1,9)]
            satVarsSoFar += 8
            ssaVars[varName] = data
            symbolicInputSSAVars.append(varName)
        if line.startswith("#->BITFIX:"):
            varNamesOutput = line[10:].strip().split(" ")
        elif line.startswith("#"):
            # Other comments
            pass
        elif isInInterestingPartOfTheInputFile:
            # Parse the other lines only in between STARTSSA and ENDSSA
            # ... but it must be an assignment!
            posEquals = line.find("=")
            if posEquals==-1:
                print("Error: Found a command line without equality operator:\n"+line,file=sys.stderr)
                sys.exit(1)
            varName = line[0:posEquals].strip()
            assignee = line[posEquals+1:].strip()
            
            # Don't overwrite "Input Bytes"
            if varName in symbolicInputSSAVars:

                #...instead store their values            
                assert not assignee.startswith("0x")
                assert assignee[0] in ["0","1","2","3","4","5","6","7","8","9"]
            
                dataValueInt = int(assignee)
                dataValuesBool = [1 if (dataValueInt & (1 << i))>0 else -1 for i in range(0,32)]
                symbolicInputSSAVarsData[varName] = dataValuesBool
            
            else: # if not varName in symbolicInputSSAVars:
                
                if varName in ssaVars:
                    print("Error: Multiple assignments of variable "+varName,file=sys.stderr)
                    sys.exit(1)
                
                # There are a couple of cases what an assignment can do
                # Case 1: Assigning a HEX constant
                if assignee.startswith("0x"):
                    dataValueInt = int(assignee[2:],base=16)
                    dataValuesBool = [1 if (dataValueInt & (1 << i))>0 else -1 for i in range(0,32)]
                    ssaVars[varName] = dataValuesBool
                # Case 2: Assigning an INT constant
                elif assignee[0] in ["0","1","2","3","4","5","6","7","8","9"]:
                    dataValueInt = int(assignee)
                    dataValuesBool = [1 if (dataValueInt & (1 << i))>0 else -1 for i in range(0,32)]
                    ssaVars[varName] = dataValuesBool
                # Case 3: A variable
                elif assignee in ssaVars:
                    ssaVars[varName] = ssaVars[assignee] # Shallow copy is OK, since SSA
                # Case 4: Apply function
                elif assignee.startswith("fn_"):
                
                    clauses.append(["c "+assignee])
                    
                    # Parse parameters (syntactically)
                    assert "(" in assignee
                    parameters = assignee[assignee.find("(")+1:]
                    assert ")" in parameters
                    parameters = parameters[0:parameters.find(")")]
                    parameters = [a.strip() for a in parameters.split(",")]
                    
                    # Parse parameters (semantically)
                    parsedParameters = []
                    for parameter in parameters:
                        # Case 1: INT constant
                        if parameter[0] in ["0","1","2","3","4","5","6","7","8","9"]:
                            dataValueInt = int(parameter)
                            dataValuesBool = [1 if (dataValueInt & (1 << i))>0 else -1 for i in range(0,32)]
                        # Case 2: A variable
                        else:
                            if not parameter in ssaVars:
                                print("Error: The parameter "+parameter+" does not define an assigned variable!",file=sys.stderr)
                                sys.exit(1)
                            dataValuesBool = ssaVars[parameter]
                        parsedParameters.append(dataValuesBool)
                        
                    # Get function name
                    functionName = assignee[0:assignee.find("(")]
                    
                    # Special function: fn_fourBytesToInt
                    if functionName=="fn_fourBytesToInt":
                        assert len(parsedParameters)==4
                        allBits = []
                        for i in [0,1,2,3]:
                            print(parameters[i])
                            assert len(parsedParameters[i])>=8
                            allBits = allBits + parsedParameters[i][0:8]
                        ssaVars[varName] = allBits
                    
                    # Special function: Rotation
                    elif functionName=="fn_leftrotate":
                        # Assumes that the parameter is int
                        nofRotateBits = int(parameters[1])
                        output = parsedParameters[0]
                        # Inefficient, but simple solution
                        for i in range(0,32-nofRotateBits):
                            output = output[1:] + [output[0]]
                        ssaVars[varName] = output    
                        
                    # Bitwise functions
                    elif functionName.startswith("fn_bitwise_"):
                        
                        # 1. Parse CNF description
                        fileNameEncoding = cnfDir+"/"+functionName[11:]+".cnf"
                        with open(fileNameEncoding,"r") as inFile:
                            localClauses = [[int(u) for u in line.strip().split(" ")] for line in inFile.readlines()]
                        
                        # 2. Allocate output bits
                        lenOutput = len(parsedParameters[0])
                        for a in parsedParameters:
                            assert len(a)==lenOutput
                        data = [satVarsSoFar+i for i in range(1,lenOutput+1)]
                        satVarsSoFar += lenOutput
                        ssaVars[varName] = data
                        
                        # Implement bitwise
                        for i in range(0,lenOutput):
                            satVarNumbers = [p[i] for p in parsedParameters]
                            satVarNumbers.append(ssaVars[varName][i])
                            
                            for clause in localClauses:
                                newClause = []
                                for literal in clause:
                                    if literal!=0:
                                        if literal<0:
                                            newLit = -1*satVarNumbers[-1*literal-1]
                                        else:
                                            newLit = satVarNumbers[literal-1]
                                    newClause.append(newLit)
                                clauses.append(newClause)
                                
                    # Specially implemented functions: fn_add_32
                    elif functionName.startswith("fn_add_"):

                        # How many bits
                        lenOutput = len(parsedParameters[0])
                        assert len(parsedParameters)==2
                        assert len(parsedParameters[1])==lenOutput
                        
                        # Allocate target bits
                        data = [satVarsSoFar+i for i in range(1,lenOutput+1)]
                        satVarsSoFar += lenOutput
                        
                        # Now perform addition, using Carry bit
                        carryBit = None
                        bitPos = 0
                        bitsLeft = lenOutput
                        while bitsLeft>0:
                        
                            # Select which adder to use
                            if carryBit==None:
                                thisBitNumber = max([a for a in ADDER_GRANUALARITIES_NO_CARRY_IN if a<=bitsLeft])
                                carryOut = True
                            else:
                                if bitsLeft in ADDER_GRANUALARITIES_NO_CARRY_OUT:
                                    carryOut = False
                                    thisBitNumber = bitsLeft
                                else:
                                    carryOut = True
                                    thisBitNumber = max([a for a in ADDER_GRANUALARITIES if a<=bitsLeft])

                            # Prepare filename prefix
                            fileNameEncoding = cnfDir+"/adder_"
                            
                            # Collect bits for encoding
                            bitCollection = []
                            if carryBit!=None:
                                fileNameEncoding += "ci"
                                bitCollection.append(carryBit)
                            bitCollection += parsedParameters[0][bitPos:thisBitNumber+bitPos]
                            bitCollection += parsedParameters[1][bitPos:thisBitNumber+bitPos]
                            bitCollection += data[bitPos:thisBitNumber+bitPos]
                            if carryOut:
                                fileNameEncoding += "co"
                                carryBit = satVarsSoFar+1
                                satVarsSoFar+=1
                                bitCollection.append(carryBit)
                                
                            
                            # Encode
                            clauses.append(["c Adder inst: "+fileNameEncoding + str(thisBitNumber)+" over "+str(bitCollection)])
                            fileNameEncoding = fileNameEncoding + str(thisBitNumber) + ".cnf"
                            with open(fileNameEncoding,"r") as inFile:
                                localClauses = [[int(u) for u in line.strip().split(" ")] for line in inFile.readlines()]
                            for clause in localClauses:
                                newClause = []
                                for literal in clause:
                                    if literal!=0:
                                        if literal<0:
                                            newLit = -1*bitCollection[-1*literal-1]
                                        else:
                                            newLit = bitCollection[literal-1]
                                    newClause.append(newLit)
                                clauses.append(newClause)
                            
                            
                            # Update bit position
                            bitPos += thisBitNumber
                            bitsLeft -= thisBitNumber
                            
                            
                        # Done with adding
                        ssaVars[varName] = data
                            
                            
                   
                    # Non-bitwise function...
                    else:
                        print("Error: Unknown function: '" +functionName+"'")
                        sys.exit(1)
                       
                # No other cases possible
                else:
                    print("Error: Found a command line with no valid equality operator line:\n"+line,file=sys.stderr)
                    sys.exit(1)
                    
                    
# Now write the output files
overallOutputBits = []
for a in varNamesOutput:
    overallOutputBits += ssaVars[a]
    
for nofFixedBits in range(0,25):
    with open("reverse_hash_"+str(cnfDir)+"_"+str(nofFixedBits)+".cnf","w") as outputFile:
    
        # Count clauses (without comments)
        realNofClauses = 0
        filteredClauses = []
        for a in clauses:
            try:
                if a[0][0:2]=="c ":
                    filteredClauses.append(a)
                else:
                    raise "Unexpected: The only nested indexable clauses array elements should be comments."
            except TypeError:
                if a==[1]: # keep the only-1-clause needs to be copied
                    filteredClauses.append(a)
                    realNofClauses += 1
                elif not 1 in a:
                
                    # Check if trivially true
                    tester = set(a)
                    superfluous = False
                    for v in tester:
                        if -1*v in tester:
                            superfluous = True
                    if not superfluous:
                        filteredClauses.append(tester)
                        realNofClauses += 1
                    

    
        # Write header (including the 
        # Test: add 256...
        outputFile.write("p cnf "+str(satVarsSoFar)+" "+str(realNofClauses+nofFixedBits)+"\n")
        outputFile.write("c Input:")
        for a in symbolicInputSSAVars:
            for b in ssaVars[a]:
                outputFile.write(" "+str(b))
        outputFile.write("\nc Output: "+" ".join([str(u) for u in overallOutputBits])+"\n")
        
        for clause in filteredClauses:
            outputFile.write(" ".join([str(a) for a in clause if a!=-1])+" 0\n")
        for i in range(0,nofFixedBits):
            outputFile.write(str(-1*overallOutputBits[i])+" 0\n")
            
        # Old: Fix input. Need to add 256 to the length of the input in this case.
        # for a in symbolicInputSSAVars:
        #     for i,b in enumerate(ssaVars[a]):
        #         if symbolicInputSSAVarsData[a][i] == -1:
        #             outputFile.write("-"+str(b)+" 0\n")
        #         else:
        #             assert symbolicInputSSAVarsData[a][i]==1
        #             outputFile.write(str(b)+" 0\n")
                


