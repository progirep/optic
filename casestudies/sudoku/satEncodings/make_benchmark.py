#!/usr/bin/env python2
import os, glob, sys

SOLVERS = [("lingeling","../../../lib/lingeling-bbc-9230380-160707/lingeling"),("mapleSat","../../../lib/MapleCOMSPS_LRB/core/minisat"),("minisat","../../../lib/minisat/simp/minisat"),("picosat","../../../lib/picosat-965/picosat")]

allCNFFiles = glob.glob("*.cnf")
allOutputFiles = []
for (a,b) in SOLVERS:
    allOutputFiles.extend([".res/"+c+"."+a for c in allCNFFiles])

with open("Makefile","w") as outFile:
    print >>outFile,"default: "+" ".join(allOutputFiles)
    print >>outFile,"\t./cactus_plot.py"
    print >>outFile,"\tpdflatex summary.tex"
    print >>outFile,"\tpdflatex summary.tex"
    print >>outFile,"\techo \"Done!\""
    print >>outFile,"\t\n"
    
    for (a,b) in SOLVERS:
        for c in allCNFFiles:
            print >>outFile,".res/"+c+"."+a+":"
            print >>outFile,"\tmkdir -p .res"
            print >>outFile,"\t../../../tools/timeout -t 1200 -m 3192000 \"("+b+" "+c+";test $$? -eq 10 -o $$? -eq 0)\" > .res/"+c+"."+a+" 2>&1;"
            print >>outFile,"\t\n"
