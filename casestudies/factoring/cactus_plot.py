#!/usr/bin/env python
import os, glob, sys, math

# Settings
# 

#d7191c
#fdae61
#ffffbf
#abdda4
#2b83ba


PAINTSTYLES = ["color=plotColor1,thick","color=plotColor1,semithick,densely dashed","color=plotColor2,thick","color=plotColor2,semithick,densely dashed","color=plotColor3,thick","color=plotColor3,semithick,densely dashed","color=plotColor4,thick","color=plotColor4,semithick,densely dashed","color=plotColor5,thick","color=plotColor5,semithick,densely dashed"]

# PAINTSTYLES = ["black,solid", "black,dotted", "black,densely dotted", "black,dashed", "black,densely dashed", "black,dashdotted", "black,densely dashdotted", "thick,solid"] #"black,dasdotdotted",

VARIANTS = ["Minimal.cnflingeling","Minimal.cnfmapleSat","OP.cnflingeling","OP.cnfmapleSat","9999.cnflingeling","9999.cnfmapleSat","33.cnflingeling","33.cnfmapleSat","Greedy.cnflingeling","Greedy.cnfmapleSat"]
WIDTH = 22
HEIGHT = 9
MAX_TIME = 1800
OVERSHOOT=0.2
NOF_FILES_TICK = 10
MIN_TIME = 0.1
MIN_FILES = 20
TIME_AXIS_MARKS = [0.1,1,5,10,100,600,1800]

# Time axis computation
def timeToXCoordinate(time):
    time = max(time,MIN_TIME)
    return WIDTH*(math.log(time)-math.log(MIN_TIME)) / (math.log(MAX_TIME)-math.log(MIN_TIME))

# List Performance Files
performanceFiles = glob.glob(".res/*.stderr")
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
                    if inFile.endswith(a+".stderr"):
                        performances[a].append(time)
                        found = True
                assert found
                
print performances
                
# Write cactus plot   
with open("summary.tex","w") as outFile:    
    print >>outFile,"\\documentclass[a4paper]{scrartcl}"
    print >>outFile,"\\usepackage{tikz}"
    print >>outFile,"\\usepackage[left=1cm,right=1cm,top=2cm,bottom=2cm]{geometry}"
    print >>outFile,"\\usepackage{pgfplots}"
    print >>outFile,"\\title{Version comparison of reluv2}"
    
    
    # Color def
    print >>outFile,"\\definecolor{plotColor1}{RGB}{215,25,28}"
    print >>outFile,"\\definecolor{plotColor2}{RGB}{253,174,97}"
    print >>outFile,"\\definecolor{plotColor3}{RGB}{225,225,161}"
    print >>outFile,"\\definecolor{plotColor4}{RGB}{131,221,164}"
    print >>outFile,"\\definecolor{plotColor5}{RGB}{43,131,186}"
   
    print >>outFile,"\\begin{document}"
    print >>outFile,"\\maketitle"

    # Print legend
    print >>outFile,"\\subsection*{Legend}"
    print >>outFile,"\\begin{tikzpicture}"
    for i, a in enumerate(performances):
        print >>outFile, "\\draw["+PAINTSTYLES[VARIANTS.index(a)]+"] (0,",i*0.8,") -- +(2,0) node[anchor=west,color=black] {"+a+"};"
    print >>outFile,"\\end{tikzpicture}"        
    
    # Print cactus plot
    print >>outFile,"\\subsection*{Cactus plot}"
    print >>outFile,"\\centering\\begin{tikzpicture}[scale=0.4]"
    # -> Boundary lines    
    print >>outFile,"\\draw[very thick,->] (0,0) -- (",WIDTH+OVERSHOOT,",0) node[anchor=west] {Time};"
    print >>outFile,"\\draw[very thick,->] (0,0) -- (0,",HEIGHT+OVERSHOOT,") node[anchor=south] {Files};"
    print >>outFile,"\\draw[dashed] (",WIDTH,",0) -- +(0,",HEIGHT,");"
    print >>outFile,"\\draw[dashed] (0,",HEIGHT,") -- +(",WIDTH,",0);"
    # -> Nof files tick
    startingTick = NOF_FILES_TICK
    while startingTick < MIN_FILES:
        startingTick += NOF_FILES_TICK
    for i in range(startingTick,totalNofFiles+1,NOF_FILES_TICK):
        pos = (HEIGHT/float(totalNofFiles-MIN_FILES))*(i-MIN_FILES)
        print >>outFile,"\\draw[semithick] (0.1,",pos,") -- +(-0.2,0) node[anchor=east] {\small "+str(i)+"};"
    # -> Time tick
    for i in TIME_AXIS_MARKS:
        pos = timeToXCoordinate(i)
        print >>outFile,"\\draw[semithick] (",pos,",0.1) -- +(0,-0.2) node[anchor=north] {\small "+str(i)+"};"
    # -> Cactus plot
    for i,filename in enumerate(performances):
        allTimes = performances[filename]
        style = PAINTSTYLES[VARIANTS.index(filename)]
        allTimes.sort()
        print >>outFile,"\\draw["+style+"] (0,0)",
        nofFilesSoFar = 0
        for t in allTimes:
            nofFilesSoFar += 1
            xPos = timeToXCoordinate(t)
            yPos = max(0.0,(HEIGHT/float(totalNofFiles-MIN_FILES))*(nofFilesSoFar-MIN_FILES))
            print >>outFile,"-| (",xPos,",",yPos,")",
        print >>outFile,";"
    print >>outFile,"\\end{tikzpicture}\n\n"        
    
    
    
    
    
    
    
    print >>outFile,"\\end{document}"
    
                
    


