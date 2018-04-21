#!/usr/bin/env python2
import sys, os, glob, random

# Solver selection
SOLVERS = [("lingeling","../../lib/lingeling-bbc-9230380-160707/lingeling"),("mapleSat","../../lib/MapleCOMSPS_LRB/core/minisat")]


# Find all benchmarks
allBenchmarkFiles = glob.glob("*.cnf")
print allBenchmarkFiles

with open("Makefile","w") as makefile:
    print >>makefile,"default :",
    dependencies = []
    for a in allBenchmarkFiles:
        for (solvername,solverpath) in SOLVERS:    
            dependencies.append(".res/"+a+solvername+".txt")        
    random.shuffle(dependencies)
    for dependency in dependencies:
        print >>makefile,dependency,
    print >>makefile,"\n\t./make_results_summary.py > table.tex\n\tpdflatex table.tex\n\tpdflatex table.tex\n\tpdflatex table.tex"
    print >>makefile,"\n\techo \"Done!\"\n"
    
    for (solvername,solverpath) in SOLVERS:
        for a in allBenchmarkFiles:
            print >>makefile,".res/"+a+solvername+".txt : "+a
            print >>makefile,"\t@mkdir -p .res\n"                
            print >>makefile,"\t(../../tools/timeout -m 8192000 -t 1800 "+solverpath+" "+a+" > .res/"+a+solvername+".txt; test $$? -eq 10 -o $$? -eq 20 -o $$? -eq 0) 2> .res/"+a+solvername+".stderr"
            print >>makefile,""
    
    print >>makefile,"clean :"
    for a in allBenchmarkFiles:
        print >>makefile,"\trm -f .res/"+a+".txt"
        print >>makefile,"\trm -f .res/"+a+".stderr"
    print >>makefile,""            
