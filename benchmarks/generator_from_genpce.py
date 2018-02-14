#!/usr/bin/env python2
import os, sys, glob

sourceFiles = "../lib/genpce/circuits/reference/*.cnf"
allFiles = glob.glob(sourceFiles)

for thisFile in allFiles:

    # Get Destination file name
    destFile = thisFile
    while "/" in destFile:
        destFile = destFile[1:]
    assert destFile[len(destFile)-4:] == ".cnf"
    
    # Read input file
    clauses = []
    infoLine = ""
    with open(thisFile,"r") as inFile:
        for line in inFile.readlines():
            line = line.strip()
            if line.startswith("c i"):
                infoLine = line[3:]
            elif line.startswith("c") or line.startswith("p"):
                pass
            else:
                if len(line)>0:
                    clauses.append(line)
    
    # Which are explicit and implicit vars?
    explicitVars = []
    implicitVars = []
    parsedClauses = []
    infoLine = infoLine.split(" ")
    for a in infoLine:
        if len(a)>0:
            explicitVars.append(int(a))
    for c in clauses:
        thisClause = []
        for a in c.split(" "):
            if len(a)>0:
                thisClause.append(int(a))
                thisVar = abs(int(a))
                if not thisVar in explicitVars:
                    if not thisVar in implicitVars:
                        implicitVars.append(thisVar)
        parsedClauses.append(thisClause)
                        
    # Write output file
    with open("gen_"+destFile[0:len(destFile)-4]+".txt","w") as outFile:
        print >>outFile,"// "+destFile
        
        for a in explicitVars:
            print >>outFile,"var v"+str(a)
        for a in implicitVars:
            print >>outFile,"var v"+str(a)
            
        print >>outFile,"clauses = true"

        #  Write clauses in the order of minimal implicit variable occurring
        print parsedClauses
        doneList = [False for a in clauses]
        for i in implicitVars:
            for j,c in enumerate(parsedClauses):
                if not doneList[j]:
                    if (i in c) or (-1*i in c):
                        print >>outFile,"clauses = clauses & (false",
                        for thisLit in c:
                            if (thisLit<0):
                                print >>outFile,"| !v"+str(abs(thisLit)),
                            elif (thisLit>0):
                                print >>outFile,"| v"+str(abs(thisLit)),
                        print >>outFile,")"
                        doneList[j] = True
            print >>outFile,"clauses = v"+str(i)+" $ clauses"

        # Clauses only over I/O vars                    
        for j,c in enumerate(parsedClauses):
            if not doneList[j]:
                print >>outFile,"clauses = clauses & (false",
                for thisLit in c:
                    if (thisLit<0):
                        print >>outFile,"| !v"+str(abs(thisLit)),
                    elif (thisLit>0):
                        print >>outFile,"| v"+str(abs(thisLit)),
                print >>outFile,")"
    
        print >>outFile,"\nencode = clauses"
