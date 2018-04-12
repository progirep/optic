#!/usr/bin/env python2
# Sudoku Example problem builder, uses minisat to check that there is really only one solution
import os, sys, math, subprocess, random, copy, time

STAIRLENGTH = 20
BLOCKSIZE = 3

def getNewStairSudokuBluePrint():
    blocks = [[-1 for i in range(0,BLOCKSIZE*(BLOCKSIZE+STAIRLENGTH-1))] for j in range(0,BLOCKSIZE*(BLOCKSIZE+STAIRLENGTH-1))]
    for i in range(0,STAIRLENGTH):
        for x in range(0,BLOCKSIZE*BLOCKSIZE):
            for y in range(0,BLOCKSIZE*BLOCKSIZE):
                blocks[x+i*BLOCKSIZE][y+i*BLOCKSIZE] = None
    return blocks


def enumerateOtherBlockPositions(x,y):
    blockSize = BLOCKSIZE
    blockX = int(x/blockSize)
    blockY = int(y/blockSize)
    result = []
    for i in range(0,blockSize):
        for j in range(0,blockSize):
            (x2,y2) = (blockX*blockSize+i,blockY*blockSize+j)
            if (x2,y2)!=(x,y):
                result.append((x2,y2))
    return result


def printSudoku(solutionSudoku):
    print "+"+"-"*len(solutionSudoku)+"+"
    baseSize = len(solutionSudoku[0])
    for x in range(0,len(solutionSudoku)):
        sys.stdout.write("|")
        for y in range(0,len(solutionSudoku)):
            if solutionSudoku[x][y] is None:
                sys.stdout.write(".")
            else:
                sys.stdout.write(" 123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[solutionSudoku[x][y]+1])
        sys.stdout.write("|\n")
    print "+"+"-"*len(solutionSudoku)+"+"


def checkSudokuFeasibility(currentSudoku,checkIfDoubleSolution=False):
    oneHotVars = [[[None for k in range(0,BLOCKSIZE*BLOCKSIZE) ] for j in range(0,len(currentSudoku))] for i in range(0,len(currentSudoku))]

    print >>sys.stderr,"Checking feasibility for:"
    printSudoku(currentSudoku)
    sys.stdout.flush()

    # Check Sudoku rules on the "currentSudoku", as the SAT solver has a pretty hard time doing this.
    for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
        for i in range(0,BLOCKSIZE*BLOCKSIZE):
            for j in range(0,BLOCKSIZE*BLOCKSIZE):
                if not currentSudoku[i+baseBlockX][j+baseBlockY] is None:
                    for j2 in range(j+1,BLOCKSIZE*BLOCKSIZE):
                        if currentSudoku[i+baseBlockX][j+baseBlockY] == currentSudoku[i+baseBlockX][j2+baseBlockY]:
                            print "Ret",baseBlockX,baseBlockY,i,j,j2,currentSudoku[i+baseBlockX][j+baseBlockY]
                            return None
                    # Block
                    for (x,y) in enumerateOtherBlockPositions(i,j):
                        if currentSudoku[i+baseBlockX][j+baseBlockY] == currentSudoku[x+baseBlockX][y+baseBlockY]:
                            return None
                if not currentSudoku[j+baseBlockX][i+baseBlockY] is None:
                    for j2 in range(j+1,BLOCKSIZE*BLOCKSIZE):
                        if currentSudoku[j+baseBlockX][i+baseBlockY] == currentSudoku[j2+baseBlockX][i+baseBlockY]:
                            return None

    print >>sys.stderr, "Still here!"

    # Make vars
    nofVarsSoFar = 0
    for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
        for i in range(0,BLOCKSIZE*BLOCKSIZE):
            for j in range(0,BLOCKSIZE*BLOCKSIZE):
                if currentSudoku[i+baseBlockX][j+baseBlockY] is None:
                    for k in range(0,BLOCKSIZE*BLOCKSIZE):
                        # Only allocate variabes if necessary
                        isPossible = True
                        for i2 in range(0,BLOCKSIZE*BLOCKSIZE):
                            if currentSudoku[i2+baseBlockX][j+baseBlockY]==k:
                                isPossible = False
                            if currentSudoku[i+baseBlockX][i2+baseBlockY]==k:
                                isPossible = False
                        otherBlockPositions = enumerateOtherBlockPositions(i,j)
                        for (x2,y2) in otherBlockPositions:
                            if currentSudoku[x2+baseBlockX][y2+baseBlockY]==k:
                                isPossible = False
                        if isPossible:
                            if oneHotVars[i+baseBlockX][j+baseBlockY][k] is None:
                                nofVarsSoFar += 1
                                oneHotVars[i+baseBlockX][j+baseBlockY][k] = nofVarsSoFar

    clauses = []

    # One per cell
    for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
        for i in range(0,BLOCKSIZE*BLOCKSIZE):
            for j in range(0,BLOCKSIZE*BLOCKSIZE):
                if currentSudoku[i+baseBlockX][j+baseBlockY] is None:
                    thisClause = []
                    for k in range(0,BLOCKSIZE*BLOCKSIZE):
                        if not oneHotVars[i+baseBlockX][j+baseBlockY][k] is None:
                            thisClause.append(oneHotVars[i+baseBlockX][j+baseBlockY][k])
                    clauses.append(thisClause)

    # One per line
    for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
        for i in range(0,BLOCKSIZE*BLOCKSIZE):
            for k in range(0,BLOCKSIZE*BLOCKSIZE):
                for j in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not oneHotVars[i+baseBlockX][j+baseBlockY][k] is None:
                        for j2 in range(j+1,BLOCKSIZE*BLOCKSIZE):
                            if not oneHotVars[i+baseBlockX][j2+baseBlockY][k] is None:
                                clauses.append((-1*oneHotVars[i+baseBlockX][j+baseBlockY][k],-1*oneHotVars[i+baseBlockX][j2+baseBlockY][k]))

                gotOneClause = []
                foundOne = False
                for j in range(0,BLOCKSIZE*BLOCKSIZE):
                    if currentSudoku[i+baseBlockX][j+baseBlockY]==k:
                        foundOne = True
                    if not oneHotVars[i+baseBlockX][j+baseBlockY][k] is None:
                        gotOneClause.append(oneHotVars[i+baseBlockX][j+baseBlockY][k])
                if not foundOne:
                    clauses.append(gotOneClause)

    # One per column
    for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
        for i in range(0,BLOCKSIZE*BLOCKSIZE):
            for k in range(0,BLOCKSIZE*BLOCKSIZE):
                for j in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not oneHotVars[j+baseBlockX][i+baseBlockY][k] is None:
                        for j2 in range(j+1,BLOCKSIZE*BLOCKSIZE):
                            if not oneHotVars[j2+baseBlockX][i+baseBlockY][k] is None:
                                clauses.append((-1*oneHotVars[j+baseBlockX][i+baseBlockY][k],-1*oneHotVars[j2+baseBlockX][i+baseBlockY][k]))
                gotOneClause = []
                foundOne = False
                for j in range(0,BLOCKSIZE*BLOCKSIZE):
                    if currentSudoku[j+baseBlockX][i+baseBlockY]==k:
                        foundOne = True
                    if not oneHotVars[j+baseBlockX][i+baseBlockY][k] is None:
                        gotOneClause.append(oneHotVars[j+baseBlockX][i+baseBlockY][k])
                if not foundOne:
                    clauses.append(gotOneClause)

    # One per block
    for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
        blockSize = BLOCKSIZE*BLOCKSIZE
        for x in range(0,BLOCKSIZE*BLOCKSIZE):
            for y in range(0,BLOCKSIZE*BLOCKSIZE):
                for k in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not oneHotVars[x+baseBlockX][y+baseBlockY][k] is None:
                        for (x2,y2) in enumerateOtherBlockPositions(x,y):
                            if not oneHotVars[x2+baseBlockX][y2+baseBlockY][k] is None:
                                if (x2<x) or ((x2==x) and (y2<y)):
                                    clauses.append((-1*oneHotVars[x+baseBlockX][y+baseBlockY][k],-1*oneHotVars[x2+baseBlockX][y2+baseBlockY][k]))


    # Run PICOSAT on the problem
    proc = subprocess.Popen("picosat",stdout=subprocess.PIPE,stdin=subprocess.PIPE)
    proc.stdin.write("p cnf "+str(nofVarsSoFar)+" "+str(len(clauses))+"\n")
    for c in clauses:
        proc.stdin.write(" ".join([str(a) for a in c])+" 0\n")
    proc.stdin.close()

    # Sidechaining
    if False:
        with open("/tmp/test.cnf","w") as outFile:
            outFile.write("p cnf "+str(nofVarsSoFar)+" "+str(len(clauses))+"\n")
            for c in clauses:
                outFile.write(" ".join([str(a) for a in c])+" 0\n")
            outFile.close()

    # Read off solution
    solution = {}
    satisfiable = False
    for line in proc.stdout.readlines():
        # print line
        if line.startswith("s SATISFIABLE") or line.startswith("s 1"):
            satisfiable = True
        if line.startswith("v "):
            for a in line.strip().split(" "):
                if a!="v":
                    value = int(a)
                    if value<0:
                        solution[-1*value] = False
                    elif value>0:
                        solution[value] = True

    if not satisfiable:
        return None


    if checkIfDoubleSolution:
        # We are only interested in if there is another solution
        newClause = []
        for (a,b) in solution.iteritems():
            if not b:
                newClause.append(a)
            else:
                newClause.append(-1*a)
        clauses.append(newClause)

        # Run PICOSAT on the problem
        proc = subprocess.Popen("picosat",stdout=subprocess.PIPE,stdin=subprocess.PIPE)
        proc.stdin.write("p cnf "+str(nofVarsSoFar)+" "+str(len(clauses))+"\n")
        for c in clauses:
            proc.stdin.write(" ".join([str(a) for a in c])+" 0\n")
        proc.stdin.close()

        for line in proc.stdout.readlines():
            # print line
            if line.startswith("s SATISFIABLE") or line.startswith("s 1"):
                return True


        return False

    # Read solution
    solutionSudoku = []
    for x in range(0,len(currentSudoku)):
        dis = []
        for y in range(0,len(currentSudoku)):
            if not currentSudoku[x][y] is None:
                dis.append(currentSudoku[x][y])
            else:
                for k in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not oneHotVars[x][y][k] is None:
                        if solution[oneHotVars[x][y][k]]:
                            dis.append(k)
        solutionSudoku.append(dis)

    # Print
    # printSudoku(solutionSudoku)
    return solutionSudoku



def buildSudoku():
    currentSudoku = getNewStairSudokuBluePrint()
    # print currentSudoku
    # print [len(a) for a in currentSudoku]
    sys.stdout.flush()
    allPositions = [(x,y) for x in range(0,len(currentSudoku)) for y in range(0,len(currentSudoku))]
    # random.shuffle(allPositions)
    for (x,y) in allPositions:
        print "Processing position",x,y
        if currentSudoku[x][y]!=-1:
            possibleValues = list(range(0,BLOCKSIZE*BLOCKSIZE))
            random.shuffle(possibleValues)
            valuePos = 0
            found = False
            while not found:
                assert valuePos!=BLOCKSIZE*BLOCKSIZE
                nextSudoku = copy.deepcopy(currentSudoku)
                nextSudoku[x][y] = possibleValues[valuePos]
                solution = checkSudokuFeasibility(nextSudoku)
                if not (solution is None):
                    currentSudoku = nextSudoku
                    found = True
                    printSudoku(currentSudoku)
                else:
                    valuePos += 1

    print "Final Sudoku (solution):"
    printSudoku(currentSudoku)

    # Now remove elements while we can
    random.shuffle(allPositions)
    for i,(x,y) in enumerate(allPositions):
        if currentSudoku[x][y]!=-1:
            nextSudoku = copy.deepcopy(currentSudoku)
            nextSudoku[x][y] = None
            if not checkSudokuFeasibility(nextSudoku,True):
                currentSudoku = nextSudoku
                printSudoku(currentSudoku)
                print i,"/",len(allPositions)

    print "Final Sudoku:"
    printSudoku(currentSudoku)
    return currentSudoku


# Testing
if __name__ == '__main__':

    # Build a few examples
    def fileformat(a):
        if a is None:
            return "0"
        elif a==-1:
            return "-1"
        else:
            return str(a+1)

    for i in range(0,30):
        sudoku = buildSudoku()
        with open("../sudokus/s"+str(BLOCKSIZE*BLOCKSIZE)+str(STAIRLENGTH)+"_"+str(int(time.time()))+".txt","w") as outFile:
            for line in sudoku:
                outFile.write(" ".join([fileformat(a) for a in line])+"\n")
