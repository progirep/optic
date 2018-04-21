#!/usr/bin/env python2
# Sudoku Example problem builder, uses minisat to check that there is really only one solution
import os, sys, math, subprocess, copy, glob, itertools

BLOCKSIZE = 3
SMART_ENCODING_CLAUSE_LIMIT = 3000


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



def buildSATInstance(inFileName,outputFilename,outputFilenameAnother,allDiffBuilder, solution): 
    # solution is the SAT instance solution

    # Read Sudoku
    sudoku = []
    with open(inFileName,"r") as inFile:
        for line in inFile.readlines():
            line = line.strip()
            if line!="":
                data = [int(a) for a in line.split(" ")]
                for i in range(0,len(data)):
                    if data[i]==-1:
                        data[i] = -1
                    elif data[i]==0:
                        data[i] = None
                    else:
                        data[i] = data[i]-1
            sudoku.append(data)

    # Encode Sudoku
    selectedSize = len(sudoku)
    oneHotVars = [[[None for k in range(0,BLOCKSIZE*BLOCKSIZE) ] for j in range(0,len(sudoku))] for i in range(0,len(sudoku))]
    
    STAIRLENGTH = (selectedSize/BLOCKSIZE)-BLOCKSIZE+1

    # Make vars
    nofVarsSoFar = 0
    for i in range(0,len(sudoku)):
        for j in range(0,len(sudoku)):
            if sudoku[i][j] is None:
                for k in range(0,BLOCKSIZE*BLOCKSIZE):
                    isPossible = True
                    baseBlockX = int(i/BLOCKSIZE)*BLOCKSIZE
                    baseBlockY = int(j/BLOCKSIZE)*BLOCKSIZE
                    # Look at Block
                    for i2 in range(0,BLOCKSIZE):
                        for j2 in range(0,BLOCKSIZE):
                            # print >>sys.stderr,"CHK:",i2,j2,baseBlockX,baseBlockY                        
                            if sudoku[i2+baseBlockX][j2+baseBlockY]==k:
                                isPossible = False
                    # Look at rows
                    rowBase = max(0,baseBlockX - (BLOCKSIZE-1)*BLOCKSIZE)
                    rowEnd = min(baseBlockX + BLOCKSIZE*BLOCKSIZE,len(sudoku))
                    for i2 in range(rowBase,rowEnd):
                        if sudoku[i2][j]==k:
                            isPossible = False
                    # Look at cols
                    colBase = max(0,baseBlockY - (BLOCKSIZE-1)*BLOCKSIZE)
                    colEnd = min(baseBlockY + BLOCKSIZE*BLOCKSIZE,len(sudoku))
                    for j2 in range(colBase,colEnd):
                        if sudoku[i][j2]==k:
                            isPossible = False
                    
                    if isPossible:
                        nofVarsSoFar += 1
                        oneHotVars[i][j][k] = nofVarsSoFar
                    
                    
    clauses = []

    # Rows
    if True:
        for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
            for i in range(0,BLOCKSIZE*BLOCKSIZE):
                print "Working on ROW:",i+baseBlockX

                # Find out which values are already taken
                fixedValues = set([])
                for j in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not sudoku[i+baseBlockX][j+baseBlockY] is None:
                        fixedValues.add(sudoku[i+baseBlockX][j+baseBlockY])

                # Build choice table
                theseChoices = [[] for a in range(0,BLOCKSIZE*BLOCKSIZE) if sudoku[i+baseBlockX][a+baseBlockY] is None]
                for k in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not k in fixedValues:
                        index = 0
                        for j in range(0,BLOCKSIZE*BLOCKSIZE):
                            if sudoku[i+baseBlockX][j+baseBlockY] is None:
                                # print >>sys.stderr,"GROK:",i,baseBlockX,j,baseBlockY,k,BLOCKSIZE,STAIRLENGTH,len(sudoku)
                                m = oneHotVars[i+baseBlockX][j+baseBlockY][k]
                                theseChoices[index].append(m)
                                index += 1

                # Construct clauses
                clauses.extend(allDiffBuilder(theseChoices))

    # Cols
    if True:
        for (baseBlockX,baseBlockY) in [(i*BLOCKSIZE,i*BLOCKSIZE) for i in range(0,STAIRLENGTH)]:
            for i in range(0,BLOCKSIZE*BLOCKSIZE):

                # Find out which values are already taken
                fixedValues = set([])
                for j in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not sudoku[j+baseBlockX][i+baseBlockY] is None:
                        fixedValues.add(sudoku[j+baseBlockX][i+baseBlockY])

                # Build choice table
                theseChoices = [[] for a in range(0,BLOCKSIZE*BLOCKSIZE) if sudoku[a+baseBlockX][i+baseBlockY] is None]
                for k in range(0,BLOCKSIZE*BLOCKSIZE):
                    if not k in fixedValues:
                        index = 0
                        for j in range(0,BLOCKSIZE*BLOCKSIZE):
                            if sudoku[j+baseBlockX][i+baseBlockY] is None:
                                m = oneHotVars[j+baseBlockX][i+baseBlockY][k]
                                theseChoices[index].append(m)
                                index += 1

                # Construct clauses
                clauses.extend(allDiffBuilder(theseChoices))

    # Blocks
    if True:
        nofBlocks = len(sudoku)/BLOCKSIZE
        for xBlock in range(0,nofBlocks):
            for yBlock in range(0,nofBlocks):
                if sudoku[xBlock*BLOCKSIZE][yBlock*BLOCKSIZE]!=-1:
                    allBlockNodes = enumerateOtherBlockPositions(xBlock*BLOCKSIZE,yBlock*BLOCKSIZE)+[(xBlock*BLOCKSIZE,yBlock*BLOCKSIZE)]
                    # print allBlockNodes

                    fixedValues = set([])
                    for (x,y) in allBlockNodes:
                        if not sudoku[x][y] is None:
                            fixedValues.add(sudoku[x][y])

                    # Build choice table
                    theseChoices = [[] for a in range(0,len(allBlockNodes)) if sudoku[allBlockNodes[a][0]][allBlockNodes[a][1]] is None]
                    for k in range(0,BLOCKSIZE*BLOCKSIZE):
                        if not k in fixedValues:
                            index = 0
                            for (x,y) in allBlockNodes:
                                if sudoku[x][y] is None:
                                    m = oneHotVars[x][y][k]
                                    theseChoices[index].append(m)
                                    index += 1

                    # Construct clauses
                    clauses.extend(allDiffBuilder(theseChoices))


    # Write
    with open(outputFilename,"w") as outFile:
        outFile.write("p cnf "+str(nofVarsSoFar)+" "+str(len([a for a in clauses if not str(a).startswith("c")]))+"\n")
        for c in clauses:
            outFile.write(" ".join([str(a) for a in c])+" 0\n")
        outFile.close()

    if True: # solution is None: ---> NEED structured solution
        # Make "Is there another solution?" Instance
        proc = subprocess.Popen(["picosat",outputFilename],stdout=subprocess.PIPE)

        # Read off solution
        solution = {}
        satisfiable = False
        for line in proc.stdout.readlines():
            print >>sys.stderr,"L: ",line
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

        assert satisfiable

        # Read solution
        # Read solution
        solutionSudoku = []
        for x in range(0,len(sudoku)):
            dis = []
            for y in range(0,len(sudoku)):
                if not sudoku[x][y] is None:
                    dis.append(sudoku[x][y])
                else:
                    for k in range(0,BLOCKSIZE*BLOCKSIZE):
                        if not oneHotVars[x][y][k] is None:
                            if solution[oneHotVars[x][y][k]]:
                                dis.append(k)
            solutionSudoku.append(dis)
        
        # Print Sudoku
        printSudoku(solutionSudoku)

    # Write new CNF
    clauses.append([-1*a for (a,b) in solution.iteritems() if b])
    with open(outputFilenameAnother,"w") as outFile:
        outFile.write("p cnf "+str(nofVarsSoFar)+" "+str(len([a for a in clauses if not str(a).startswith("c")]))+"\n")
        for c in clauses:
            outFile.write(" ".join([str(a) for a in c])+" 0\n")
        outFile.close()



    # Final Check: Really UNSAT?
    if True:
        # Make "Is there another solution?" Instance
        proc = subprocess.Popen(["picosat",outputFilenameAnother],stdout=subprocess.PIPE)

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
            return solutionSudoku

        # Read solution
        solutionSudoku = []
        for x in range(0,selectedSize):
            dis = []
            for y in range(0,selectedSize):
                if (not sudoku[x][y] is None) or sudoku[x][y]==-1:
                    dis.append(sudoku[x][y])
                else:
                    for k in range(0,BLOCKSIZE*BLOCKSIZE):
                        if not oneHotVars[x][y][k] is None:
                            if solution[oneHotVars[x][y][k]]:
                                dis.append(k)
            assert len(dis)==selectedSize
            solutionSudoku.append(dis)

        # Print Sudoku
        printSudoku(solutionSudoku)
        assert False
    else:
        return solution


def minimalSizeEncoding(variableGroups,addRedundantNoTwoElementsPerLineClauses):
    # First element for variable groups: the object number
    # Second element: what variant of the object has been selected
    allClauses = []

    # No two elements per line
    if addRedundantNoTwoElementsPerLineClauses:
        for i in range(0,len(variableGroups)):
            for j in range(i+1,len(variableGroups)):
                for k in range(0,len(variableGroups[i])):
                    if not (variableGroups[i][k] is None) and not (variableGroups[j][k] is None):
                       allClauses.append((-1*variableGroups[i][k],-1*variableGroups[j][k]))

    # No two elements per row
    for i in range(0,len(variableGroups)):
        for j in range(i+1,len(variableGroups)):
            for k in range(0,len(variableGroups[i])):
                # print >>sys.stderr,i,j,k, len(variableGroups[i]),variableGroups
                if not (variableGroups[k][i] is None) and not (variableGroups[k][j] is None):
                    allClauses.append((-1*variableGroups[k][i],-1*variableGroups[k][j]))

    # At least one element per column
    for k in range(0,len(variableGroups[0])):
        thisClause = []
        for i in range(0,len(variableGroups)):
            if not variableGroups[i][k] is None:
                thisClause.append(variableGroups[i][k])
        allClauses.append(thisClause)
    return allClauses


def approximatelyApproximatelyOptimallyPropagatingEncoding(variableGroups,propagationQuality):

    allClauses = minimalSizeEncoding(variableGroups,True)
    
    # At least one element per row
    for k in range(0,len(variableGroups)):
        thisClause = []
        for i in range(0,len(variableGroups[k])):
            if not variableGroups[k][i] is None:
                thisClause.append(variableGroups[k][i])
        allClauses.append(thisClause)
        
    # "External subsets" (where c is smaller by one) -- Col Case
    for rSize in range(2,len(variableGroups)-1):
        cSize = len(variableGroups)-rSize
        for RIndices in itertools.combinations(range(0,len(variableGroups)),rSize):
            for CIndices in itertools.combinations(range(0,len(variableGroups)),cSize):
                allClauses.append("c "+str(RIndices)+str(CIndices))
                localClauses = []
                for x1 in range(0,len(variableGroups)):
                    if not x1 in RIndices:
                        for x2 in range(0,len(variableGroups)):
                            if not x2 in CIndices:
                                if not variableGroups[x1][x2] is None:
                                    nextClause = [-1*variableGroups[x1][x2]]
                                    for i in RIndices:
                                        for j in CIndices:
                                            if not variableGroups[i][j] is None:
                                                nextClause.append(variableGroups[i][j])
                                    localClauses.append(nextClause)
                if rSize>cSize:
                    allClauses.extend(localClauses[propagationQuality-1:])
                else:
                    allClauses.extend(localClauses)

    if len(allClauses)<=SMART_ENCODING_CLAUSE_LIMIT:
        return allClauses
    return minimalSizeEncoding(variableGroups,False)

def optimallyPropagatingEncoding(variableGroups):

    allClauses = minimalSizeEncoding(variableGroups,True)
    
    
    # At least one element per row
    for k in range(0,len(variableGroups)):
        thisClause = []
        for i in range(0,len(variableGroups[k])):
            if not variableGroups[k][i] is None:
                thisClause.append(variableGroups[k][i])
        allClauses.append(thisClause)
        

    # For all row subsets R and column subsets C of equal size such that n-|R|>n,
    # one of the positions in (r,c) with r\in R and c \in C must be true.
    # We none need to consider the smallest |R| such that |R|>n-|R|
    # TODO: DO WE NEED THIS AT ALL? APPARENTLY NOT FOR n=4 AND n=5 CASES. WHAT ABOUT 6?
    rSize = int(len(variableGroups)/2.0)
    if float(rSize)==len(variableGroups)/2.0 and rSize>2:
        for RIndices in itertools.combinations(range(0,len(variableGroups)),rSize):
            for CIndices in itertools.combinations(range(0,len(variableGroups)),rSize):
                nextClause = []
                for i in RIndices:
                    for j in CIndices:
                        if not variableGroups[i][j] is None:
                            nextClause.append(variableGroups[i][j])
                allClauses.append(nextClause)
                            
    # "External subsets" (where c is smaller by one) -- Col Case
    for rSize in range(2,len(variableGroups)-1):
        cSize = len(variableGroups)-rSize
        for RIndices in itertools.combinations(range(0,len(variableGroups)),rSize):
            for CIndices in itertools.combinations(range(0,len(variableGroups)),cSize):
                allClauses.append("c "+str(RIndices)+str(CIndices))
                for x1 in range(0,len(variableGroups)):
                    if not x1 in RIndices:
                        for x2 in range(0,len(variableGroups)):
                            if not x2 in CIndices:
                                if not variableGroups[x1][x2] is None:
                                    nextClause = [-1*variableGroups[x1][x2]]
                                    for i in RIndices:
                                        for j in CIndices:
                                            if not variableGroups[i][j] is None:
                                                nextClause.append(variableGroups[i][j])
                                    allClauses.append(nextClause)

    # "External subsets" (where c is smaller by one) -- Row
    if False:
        for rSize in range(2,len(variableGroups)-1):
            cSize = len(variableGroups)-rSize
            if rSize!=cSize: # We already had this case above.
                for RIndices in itertools.combinations(range(0,len(variableGroups)),rSize):
                    for CIndices in itertools.combinations(range(0,len(variableGroups)),cSize):
                        allClauses.append("c 2 "+str(RIndices)+str(CIndices))
                        for x1 in range(0,len(variableGroups)):
                            if not x1 in RIndices:
                                for x2 in range(0,len(variableGroups)):
                                    if not x2 in CIndices:
                                        if not variableGroups[x2][x1] is None:
                                            nextClause = [-1*variableGroups[x2][x1]]
                                            for i in RIndices:
                                                for j in CIndices:
                                                    if not variableGroups[j][i] is None:
                                                        nextClause.append(variableGroups[j][i])
                                            allClauses.append(nextClause)
                            
    # Done!        
    if len(allClauses)<=SMART_ENCODING_CLAUSE_LIMIT:
        return allClauses
    return minimalSizeEncoding(variableGroups,False)


# Testing
ENCODINGS = [("_minimal.cnf",lambda x: minimalSizeEncoding(x,False)),("optimal.cnf",optimallyPropagatingEncoding),("approxapprox2.cnf",lambda x: approximatelyApproximatelyOptimallyPropagatingEncoding(x,2)),("approxapprox3.cnf",lambda x: approximatelyApproximatelyOptimallyPropagatingEncoding(x,3))]

if __name__ == '__main__':

    # Test
    # groups = [[1,2,3,4,5],[6,7,8,9,10],[11,12,13,14,15],[16,17,18,19,20],[21,22,23,24,25]]
    # groups = [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]]
    # groups = [[1,2,3,4,5,6],[7,8,9,10,11,12],[13,14,15,16,17,18],[19,20,21,22,23,24],[25,26,27,28,29,30],[31,32,33,34,35,36]]
    # clauses = approximatelyApproximatelyOptimallyPropagatingEncoding(groups,3)
    # print "p cnf "+str(max([max(a) for a in groups]))+" "+str(len([a for a in clauses if not str(a).startswith("c")]))
    # for c in clauses:
    #     print " ".join([str(a) for a in c])+" 0"
    # sys.exit(0)
    
    os.chdir("../sudokus")
    for fileName in glob.glob("s*.txt"):
        prefix = fileName[0:len(fileName)-4]
        sudokuSolution = None
        for (suffix,encoder) in ENCODINGS:
            print "Working on: ",suffix
            sys.stdout.flush()
            sudokuSolution = buildSATInstance(fileName,"../satEncodings/"+prefix+suffix,"../satEncodings/"+prefix+"_another"+suffix,encoder,sudokuSolution)
