#!/usr/bin/env python3
# Generate SAT instances for factoring integers
import sys, glob, os, math

VARIANTS = ["199OPs","299OPs","399OPs","991OPs","9999OPs","GreedyOPs"]
COLORS = ["red","blue","green!50!black","orange","black","red!50!blue"]
MAX_TIME = 2100 # For drawing
TIME_LIMIT = 1800.0
TIME_STEPS_DRAW = [0.1,1,10,100,1000,1800]
IMAGE_HEIGHT = 8.2
SOLVERVARIANTS = [("mapleSat","MapleSAT"),("lingeling","Lingeling"),("picosat","Picosat"),("minisat","Minisat")]
MAX_RESULTING_HASH = 4

def timeLogConverter(thetime):
    if (thetime)<0.05:
        return 0.0
    return IMAGE_HEIGHT/(math.log(MAX_TIME)-math.log(0.05))*(math.log(thetime)-math.log(0.05))  

allBenchmarkFiles = glob.glob(".res/*.stderr")
allBenchmarkParts = [a.split("_") for a in allBenchmarkFiles]
allNumbers = set([])
for a in allBenchmarkParts:
    if a[0]=='.res/reverse' and a[1].startswith('hash'):
        allNumbers.add(int(a[-1].split(".")[0]))
        
print("\\documentclass[halfparskip]{scrartcl}")
print("\\usepackage{tikz}")
print("\\title{Benchmark results}")
print("\\begin{document}\n\\maketitle")

# Draw data
maxNofBits = max(allNumbers)
minNofBits = min(allNumbers)
image_width = maxNofBits-minNofBits

for (solvername,solverTeXName) in SOLVERVARIANTS:
    print("\\section{Solver: "+str(solverTeXName)+"}")


    print("\\begin{tikzpicture}[xscale=0.5]")
    print("\\draw[->] (0,0) -- (0,"+str(IMAGE_HEIGHT)+");")
    print("\\draw[->] (0,0) -- ("+str(image_width)+",0) -- ("+str(image_width)+","+str(IMAGE_HEIGHT)+");")
    print("\\node[draw,anchor=south west] at ("+str(image_width+1)+",0) { \\begin{tabular}{l}")
    for numberOfEncoding,encodingName in enumerate(VARIANTS):
        if numberOfEncoding!=0:
            print("\\\\")
        print("{\\color{"+COLORS[numberOfEncoding]+"}"+encodingName+"}")
    print("\\end{tabular}};")

    # X Axis Description
    for i in range(minNofBits,maxNofBits+1):
        data = str(i)
        data = "\\textbf{"+data+"}"
        print("\\draw ("+str(i-minNofBits)+",0.1) -- +(0,-0.2) node[below] {"+data+"};")
        
    # Y Axis Description
    for i in TIME_STEPS_DRAW:
        y = timeLogConverter(i)
        data = str(i)
        print("\\draw (0.1,"+str(y)+") -- +(-0.2,0) node[left] {"+data+"};")  

        
    for numberOfEncoding,encodingName in enumerate(VARIANTS):

        # Read data
        if maxNofBits>0:    
            drawData = {}
            isSAT = {}
            for variant in VARIANTS:
                for i in range(minNofBits,maxNofBits+1):

                    thisTime = []
                    for fileNum in range(0,MAX_RESULTING_HASH):
                        thisFilename = ".res/reverse_hash"+str(fileNum)+"_"+encodingName+"_"+str(i)+".cnf"+solvername+".stderr"
                        thisFilenameResult = ".res/reverse_hash"+str(fileNum)+"_"+encodingName+"_"+str(i)+".txt"
                        # print(thisFilenameResult)
                        try:
                            with open(thisFilename,"r") as dataFile:
                                for line in dataFile:
                                    line = line.strip().split(" ")
                                    if line[0] == "FINISHED":
                                        assert line[1]=="CPU"
                                        currentTime = float(line[2])
                                        if currentTime>TIME_LIMIT:
                                            thisTime.append(TIME_LIMIT)
                                        else:
                                            thisTime.append(currentTime)
 
                            # Ok, then also check if SAT
                            with open(thisFilenameResult,"r") as dataFile:
                                for line in dataFile:
                                    if line.strip()=="s SATISFIABLE" or line.strip()=="SATISFIABLE":
                                        assert not i in isSAT or isSAT[i]==True
                                        isSAT[i] = True              
                                    elif line.strip()=="s UNSATISFIABLE" or line.strip()=="UNSATISFIABLE":
                                        assert not i in isSAT or isSAT[i]==False
                                        isSAT[i] = False
                        except OSError:
                            pass # Ok, so no data.
                            # Time limit reached
                        if len(thisTime)<=fileNum:
                            thisTime.append(TIME_LIMIT)

                    drawData[(variant,i)] = sum(thisTime)/len(thisTime)
                            
            # Draw data
            for j,variant in enumerate(VARIANTS):
                lastPoints = []
                for i in range(minNofBits,maxNofBits+1):
                    if drawData[(variant,i)]==None:
                        # Draw if not yet done
                        if lastPoints!=[]:
                            if len(lastPoints)==1:
                                # Single point
                                print ("\\draw[color="+COLORS[numberOfEncoding]+"] (",i-minNofBits-1,",",str(timeLogConverter(lastPoints[0]))+") circle (0.1cm);")
                            else:
                                print ("\\draw[thick,color="+COLORS[numberOfEncoding]+"] "+" -- ".join(["("+str(i-minNofBits-len(lastPoints)+k)+","+str(timeLogConverter(lastPoints[k]))+")" for k in range(0,len(lastPoints))])+";")
                            lastPoints = []
                    else:
                        lastPoints.append(drawData[(variant,i)])
                # Finalize...
                if len(lastPoints)==1:
                    # Single point
                    print ("\\draw[color="+COLORS[numberOfEncoding]+"] (",maxNofBits-minNofBits,",",str(timeLogConverter(lastPoints[0]))+") circle (0.1cm);")
                elif len(lastPoints)>1:
                    print ("\\draw[thick,color="+COLORS[numberOfEncoding]+"] "+" -- ".join(["("+str(maxNofBits-minNofBits-len(lastPoints)+k+1)+","+str(timeLogConverter(lastPoints[k]))+")" for k in range(0,len(lastPoints))])+";")
            
    print("\\end{tikzpicture}")
print("\\end{document}")
