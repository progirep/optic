#!/usr/bin/env python2
import sys, os, glob, random, itertools, make_configuration

# Find all benchmarks
allBenchmarkFiles = glob.glob("*.txt")
print allBenchmarkFiles

# Extensions
extensionsBenchmarkResults = [c for (a,b,c) in make_configuration.BENCHMARK_SOLVER_CONFIGURATIONS] 
commands = [a for (a,b,c) in make_configuration.BENCHMARK_SOLVER_CONFIGURATIONS] 

with open("Makefile","w") as makefile:
    print >>makefile,"default :",
    dependencies = []
    for a in allBenchmarkFiles:
        for e in extensionsBenchmarkResults:
            dependencies.append(".res/"+a+e)
            
    # Randomly shuffle in chunks
    def splitter(l):
        for i in range(0, len(l), len(extensionsBenchmarkResults)):
            yield l[i:i + len(extensionsBenchmarkResults)]
    dependencies = list(splitter(dependencies))
    random.shuffle(dependencies)
    dependencies = list(itertools.chain.from_iterable(dependencies))
    dependencies = list(a.next() for a in itertools.cycle([iter(dependencies),iter([a+".howwellpropagating" for a in dependencies]),iter([a+".howwellconflicting" for a in dependencies])]))
    
    for dependency in dependencies:
        print >>makefile,dependency,
    print >>makefile,"\n\t./make_results_table.py > table.tex\n\tpdflatex table.tex\n\tpdflatex table.tex\n\tpdflatex table.tex"
    print >>makefile,"\n\techo \"Done!\"\n"
    
    for a in allBenchmarkFiles:
        for i,e in enumerate(extensionsBenchmarkResults):
            if e.startswith(".gen"):
                print >>makefile,".res/"+a+e+" : .res/"+a+".simpleenumerate"
                print >>makefile,"\t@mkdir -p .res"
                print >>makefile,"\t../tools/timeout -m 8192000 -t 1800 \"("+commands[i]+" .res/"+a+".simpleenumerate > .res/"+a+e+"; test $$? -eq 10 -o $$? -eq 0)\" 2> .res/"+a+e+".stderr"
            else:
                print >>makefile,".res/"+a+e+" : "+a
                print >>makefile,"\t@mkdir -p .res"                
                print >>makefile,"\t../tools/timeout -m 8192000 -t 1800 "+commands[i]+" "+a+" > .res/"+a+e+" 2> .res/"+a+e+".stderr"
            print >>makefile,""
            
            print >>makefile,".res/"+a+e+".howwellpropagating : .res/"+a+e
            print >>makefile,"\t../tools/timeout -m 3192000 -t 60 ../tools/propagationTester/propagationtester .res/"+a+e+" > .res/"+a+e+".howwellpropagating 2> .res/"+a+e+".howwellpropagating.stderr"
            print >>makefile,""
            
            print >>makefile,".res/"+a+e+".howwellconflicting : .res/"+a+e
            print >>makefile,"\t../tools/timeout -m 3192000 -t 60 ../tools/conflictingTester/conflictingtester .res/"+a+e+" > .res/"+a+e+".howwellconflicting 2> .res/"+a+e+".howwellconflicting.stderr"
            print >>makefile,""
            
    
    print >>makefile,"clean :"
    for a in allBenchmarkFiles:
        for i,e in enumerate(extensionsBenchmarkResults):
            print >>makefile,"\trm -f .res/"+a+e
            print >>makefile,"\trm -f .res/"+a+e+".stderr"
            print >>makefile,"\trm -f .res/"+a+e+".howwellpropagating"
            print >>makefile,"\trm -f .res/"+a+e+".howwellconflicting"
    print >>makefile,""            
