#!/usr/bin/env python2
import os, sys, glob, subprocess, make_configuration

# Extensions
extensionsBenchmarkResults = [c for (a,b,c) in make_configuration.BENCHMARK_SOLVER_CONFIGURATIONS]
tableHeaders = [b for (a,b,c) in make_configuration.BENCHMARK_SOLVER_CONFIGURATIONS]

# List of Benchmarks
benchmarkGroups = ["gen_fulladd*.txt","gen_mult_*.txt","gen_square*.txt","gen_sqrt*.txt","gen_ult_*.txt","gen_bipatite_*.txt","gen_cvc-*.txt"]
badFiles = ["gen_cvc-ult_6.txt","gen_cvc-ult-gadget.txt","gen_cvc-mult2-2n2n_2.txt","gen_cvc-mult4_4.txt"]
allBenchmarkFiles = []
for a in benchmarkGroups:
    b = glob.glob(a)
    b.sort()
    b = [u for u in b if not u in badFiles]
    allBenchmarkFiles.extend(b)

# Special functions
def texEscape(data):
    return data.replace("_","-")

# Print Header
print "\\documentclass[9pt]{scrartcl}"
print "\\usepackage[paperwidth=797mm,paperheight=210mm,left=0.5cm,right=0.5cm,top=0.5cm,bottom=0.5cm]{geometry}"
print "\\usepackage{pxfonts}"
print "\\usepackage{longtable}"
print "\\begin{document}"
sys.stdout.write("\\begin{longtable}{l")
for i in xrange(0,len(tableHeaders)):
    sys.stdout.write("||r|r|r")
sys.stdout.write("}\n")
sys.stdout.write("\\textbf{Benchmark}")
for i in xrange(0,len(tableHeaders)):
    sys.stdout.write(" & ")
    if i==len(tableHeaders)-1:
        sys.stdout.write("\\multicolumn{3}{c}{\\textbf{"+tableHeaders[i]+"}}\n")
    else:
        sys.stdout.write("\\multicolumn{3}{c||}{\\textbf{"+tableHeaders[i]+"}}\n")
print "\\\\ \\hline \\hline \\endhead"

# Print Data
for benchFile in allBenchmarkFiles:

    # Find name of benchmark file
    benchName = benchFile
    with open(benchName,"r") as benchFileRead:
        a = benchFileRead.readline()
        if a[0:2]=="//":
            benchName = a[2:].strip()

    # Write line
    sys.stdout.write(texEscape(benchName))
    for i,e in enumerate(extensionsBenchmarkResults):
        inputFileOut = ".res/"+benchFile+e
        inputFileErr = ".res/"+benchFile+e+".stderr"
        sys.stdout.write("&")
        
        time = ""
        mode = ""
        try:
            with open(inputFileErr,"r") as dataFile:
                for line in dataFile.readlines():
                    line = line.strip()
                    if line.startswith("TIMEOUT"):
                        mode = "timeout"        
                    elif line.startswith("terminate called after throwing an instance of 'std::bad_alloc'"):
                        mode = "memout"
                    elif line.startswith("MEM"):
                        mode = "memout"
                    elif line.startswith("*** picosat: out of memory in 'resize'"):
                        mode = "memout"
                    elif line.startswith("Killed") or line.startswith("killed"):
                        print >>sys.stderr, "Error: Process did not have enough memory in "+inputFileErr
                        sys.exit(1)
                    elif line.startswith("FINISHED"):
                        if mode!="memout": # Memouts occur earlier
                            mode = "finished"
                            lineParts = line.split(" ")
                            time = lineParts[2]
                            while len(time)>4 and "." in time:
                                time = time[0:len(time)-1]
                                if time[-1]==".":
                                    time = time[0:len(time)-1]
                            assert lineParts[1]=="CPU"
            if mode=="finished":
                nofClauseLines = 0
                with open(inputFileOut,"r") as dataFile:
                    for line in dataFile.readlines():
                        line = line.strip()
                        if len(line)>0:
                            if line[0] in ['0','1','2','3','4','5','6','7','8','9','-']:
                                nofClauseLines += 1
                sys.stdout.write(str(nofClauseLines)+"&"+time)
                
                # Now find out how well-propagating and how well-conflicting the resulting encoding is
                sys.stdout.write(" & $(")
                for extension in [".howwellpropagating",".howwellconflicting"]:
                    try:
                        howWellProp = open(inputFileOut+extension,"r")
                        result = None
                        for line in howWellProp.readlines():
                            assert result==None
                            result = line.strip()
                        howWellProp.close()
                        if result==None:
                            sys.stdout.write("\\times")
                        else:
                            if extension==".howwellpropagating":
                                sys.stdout.write(str(int(result)+1))
                            else:
                                if result=="$\\infty$":
                                    if extension==".howwellconflicting":
                                        result = "\!\\infty\!"
                                    else:
                                        result = "\\infty"
                                sys.stdout.write(result)
                    except OSError:
                        sys.stdout.write("??")
                    except IOError:
                        sys.stdout.write("?")
                    if extension==".howwellpropagating":
                        sys.stdout.write(",")
                sys.stdout.write(")$")
                    
                    
            else:
                if mode=="":
                    mode = "unknown"
                if i==len(tableHeaders)-1:
                    sys.stdout.write("\\multicolumn{3}{|c}{"+mode+"}")
                else:
                    sys.stdout.write("\\multicolumn{3}{|c||}{"+mode+"}")                    
        except IOError:
            if i==len(tableHeaders)-1:
                sys.stdout.write("\\multicolumn{3}{|c}{$\emptyset$}")
            else:
                sys.stdout.write("\\multicolumn{3}{|c||}{$\emptyset$}")                    
    sys.stdout.write("\\\\ \hline\n")            
        

print "\\end{longtable}"
print "\\end{document}"

