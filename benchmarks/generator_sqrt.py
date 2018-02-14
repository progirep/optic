#!/usr/bin/env python2
import os, sys, math

for nofBits in xrange(2,9):
    with open("gen_sqrt_"+str(nofBits)+".txt","w") as outFile:
        outFile.write("// Square root, "+str(nofBits)+" bits\n")
    
        # Write Bit definition A
        for i in xrange(0,nofBits):
            print >>outFile,"var a"+str(i)
        nofOutputBits = nofBits/2 + (nofBits % 2)
        for i in xrange(0,nofOutputBits):
            print >>outFile,"var x"+str(i)
        
        print >>outFile,"encode = false"
        for i in xrange(0,1 << nofBits):
            print >>outFile,"encode = encode | (true",
            for j in xrange(0,nofBits):
                if (i & (1 << j))>0:
                    print >>outFile,"& a"+str(j),
                else:
                    print >>outFile,"& !a"+str(j), 
            data = int(math.sqrt(i))
            for j in xrange(0,nofOutputBits):
                if (data & (1 << j))>0:
                    print >>outFile,"& x"+str(j),
                else:
                    print >>outFile,"& !x"+str(j), 
            print >>outFile,")"
            
                    

