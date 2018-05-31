#!/usr/bin/env python
import os, glob, sys, math

# Settings
# 
VARIANTS = ["minimal.cnf.lingeling","minimal.cnf.mapleSat","minimal.cnf.minisat","minimal.cnf.picosat","optimal.cnf.lingeling","optimal.cnf.mapleSat","optimal.cnf.picosat","optimal.cnf.minisat","approxapprox2.cnf.lingeling","approxapprox2.cnf.picosat","approxapprox2.cnf.minisat","approxapprox2.cnf.mapleSat","approxapprox3.cnf.lingeling","approxapprox3.cnf.picosat","approxapprox3.cnf.minisat","approxapprox3.cnf.mapleSat"]
VARIANT_GROUPS = [ ["minimal.cnf.lingeling","optimal.cnf.lingeling","approxapprox2.cnf.lingeling","approxapprox3.cnf.lingeling"],
["minimal.cnf.mapleSat","optimal.cnf.mapleSat","approxapprox2.cnf.mapleSat","approxapprox3.cnf.mapleSat"],
["minimal.cnf.picosat","optimal.cnf.picosat","approxapprox2.cnf.picosat","approxapprox3.cnf.picosat"],
["minimal.cnf.minisat","optimal.cnf.minisat","approxapprox2.cnf.minisat","approxapprox3.cnf.minisat"]]

WIDTH = 21
HEIGHT = 10
MAX_TIME = 120
OVERSHOOT=0.2
NOF_FILES_TICK = 10
MIN_TIME = 3
TIME_AXIS_MARKS = [3,5,10,30,60,120]

# Time axis computation
def timeToXCoordinate(time):
    time = max(time,MIN_TIME)
    return WIDTH*(math.log(time)-math.log(MIN_TIME)) / (math.log(MAX_TIME)-math.log(MIN_TIME))

# List Performance Files
performanceFiles = glob.glob(".res/*cnf*")
totalNofFiles = len(performanceFiles)/len(VARIANTS)

# Read computation time finds
performances = {a:[] for a in VARIANTS}
for inFile in performanceFiles:

    with open(inFile,"r") as inFileReader:
        for line in inFileReader.readlines():
            if line.find("FINISHED")!=-1:
                time = float(line.split(" ")[2])
                found = False
                for a in VARIANTS:
                    if inFile.endswith(a):
                        performances[a].append(time)
                        found = True
                print(inFile)
                sys.stdout.flush()
                if not found:
                    print >>sys.stderr, "Found no time in: ", inFile
                    assert found
                
for (a,b) in performances.iteritems():
    print >>sys.stderr, "Nof Files ",a, ":\t",len(b)
                
# Write cactus plot   
with open("summary.tex","w") as outFile:    
    print >>outFile,"\\documentclass[a4paper]{scrartcl}"
    print >>outFile,"\\usepackage{tikz}"
    print >>outFile,"\\usepackage[left=1cm,right=1cm,top=2cm,bottom=2cm]{geometry}"
    print >>outFile,"\\title{Sudoku Bechmark}"
    
    # Color def
    print >>outFile,"\\definecolor{plotColor1}{RGB}{215,25,28}"
    print >>outFile,"\\definecolor{plotColor2}{RGB}{253,174,97}"
    print >>outFile,"\\definecolor{plotColor3}{RGB}{225,225,161}"
    print >>outFile,"\\definecolor{plotColor4}{RGB}{131,221,164}"
    print >>outFile,"\\definecolor{plotColor5}{RGB}{43,131,186}"
    print >>outFile,"\\definecolor{plotGrayColor1}{RGB}{170,170,170}"
    print >>outFile,"\\definecolor{plotGrayColor2}{RGB}{170,170,170}"
    print >>outFile,"\\definecolor{plotGrayColor3}{RGB}{170,170,170}"
    print >>outFile,"\\definecolor{plotGrayColor4}{RGB}{170,170,170}"
    print >>outFile,"\\definecolor{plotGrayColor5}{RGB}{170,170,170}"
        
    print >>outFile,"\\begin{document}"
    print >>outFile,"\\maketitle"

    # Print legend
    print >>outFile,"\\subsection*{Legend}"
    
    # Print cactus plot
    for variantGroup in VARIANT_GROUPS:
    
        print >>outFile,"\\subsection*{Cactus plot marked for "+" and ".join(variantGroup)+ "}"
        print >>outFile,"\\centering\\begin{tikzpicture}[scale=0.4]"
        
        # Draw the gray lines
        for j in range(0,len(variantGroup)):
        
            print >>outFile,"\\node at (-3,",(0.5+j)*HEIGHT,") {\\rotatebox{90}{\\underline{"+variantGroup[j].split(".")[0]+"}}};"
        
            for j2 in range(0,len(variantGroup)):
                if j!=j2:
                    allTimes = performances[variantGroup[j2]]
                    allTimes.sort()
                    
                    print >>outFile,"\\draw[semithick,color=plotGrayColor1]",
                    drawnFirst = "(0,"+str(j*HEIGHT)+")"
                    nofFilesSoFar = 0
                    for t in allTimes:
                        nofFilesSoFar += 1
                        xPos = timeToXCoordinate(t)
                        yPos = (HEIGHT/float(totalNofFiles))*nofFilesSoFar + j*HEIGHT
                        if (xPos)<=0:
                            drawnFirst = "(0,"+str(yPos)+")"
                        else:
                            if not drawnFirst is None:
                                print >>outFile,drawnFirst;
                                drawnFirst = None
                            print >>outFile,"-| (",xPos,",",yPos,")",
                    print >>outFile,";"

                # Finally, draw the red line!        
                allTimes = performances[variantGroup[j]]
                allTimes.sort()
                
                print >>outFile,"\\draw[thick,color=plotColor1]",
                drawnFirst = "(0,"+str(j*HEIGHT)+")"
                nofFilesSoFar = 0
                for t in allTimes:
                    nofFilesSoFar += 1
                    xPos = timeToXCoordinate(t)
                    yPos = (HEIGHT/float(totalNofFiles))*nofFilesSoFar + j*HEIGHT
                    if (xPos)<=0:
                        drawnFirst = "(0,"+str(yPos)+")"
                    else:
                        if not drawnFirst is None:
                            print >>outFile,drawnFirst;
                            drawnFirst = None
                        print >>outFile,"-| (",xPos,",",yPos,")",
                print >>outFile,";"


        # -> Boundary lines    
        print >>outFile,"\\draw[very thick,->] (0,0) -- (",WIDTH+OVERSHOOT,",0) node[anchor=south] {Time (s)};"
        print >>outFile,"\\draw[very thick,->] (0,0) -- (0,",HEIGHT*len(variantGroup)+OVERSHOOT,") node[anchor=west] {\# Files};"
        for j in range(1,len(variantGroup)):
            print >>outFile,"\\draw[very thick,->] (0,",HEIGHT*j,") -- +(",WIDTH+OVERSHOOT,",0);"

        # -> Nof files tick
        for j in range(0,len(variantGroup)):
            for i in range(NOF_FILES_TICK,totalNofFiles+1,NOF_FILES_TICK):
                pos = (HEIGHT/float(totalNofFiles))*i
                print >>outFile,"\\draw[semithick] (0.1,",pos+j*HEIGHT,") -- +(-0.2,0) node[anchor=east] {\small "+str(i)+"};"

        # -> Time tick
        for i in TIME_AXIS_MARKS:
            pos = timeToXCoordinate(i)
            print >>outFile,"\\draw[semithick] (",pos,",0.1) -- +(0,-0.2) node[anchor=north] {\small "+str(i)+"};"
        for j in range(1,len(variantGroup)):
            for i in TIME_AXIS_MARKS:
                pos = timeToXCoordinate(i)
                print >>outFile,"\\draw[semithick] (",pos,",",j*HEIGHT+0.1,") -- +(0,-0.2);"

                
        print >>outFile,"\\end{tikzpicture}\n\n"        
        
        
        
        
        
    
    
    print >>outFile,"\\end{document}"
    
                
    


if False:

        # -> Cactus plot ---> Gray Parts        
        for i,filename in enumerate(performances):
            allTimes = performances[filename]
            style = PAINTSTYLES[VARIANTS.index(filename)]
            allTimes.sort()
            
            if not filename in variantGroup:
                style = style.replace("plotColor","plotGrayColor")
                print >>outFile,"\\draw["+style+"] (0,0)",
                nofFilesSoFar = 0
                for t in allTimes:
                    nofFilesSoFar += 1
                    xPos = timeToXCoordinate(t)
                    yPos = (HEIGHT/float(totalNofFiles))*nofFilesSoFar
                    print >>outFile,"-| (",xPos,",",yPos,")",
                print >>outFile,";"
                

        # -> Cactus plot ---> Red Parts        
        for i,filename in enumerate(performances):
            allTimes = performances[filename]
            style = PAINTSTYLES[VARIANTS.index(filename)]
            allTimes.sort()
            
            if filename in variantGroup:
                print >>outFile,"\\draw["+style+"] (0,0)",
                nofFilesSoFar = 0
                for t in allTimes:
                    nofFilesSoFar += 1
                    xPos = timeToXCoordinate(t)
                    yPos = (HEIGHT/float(totalNofFiles))*nofFilesSoFar
                    print >>outFile,"-| (",xPos,",",yPos,")",
                print >>outFile,";"
             

