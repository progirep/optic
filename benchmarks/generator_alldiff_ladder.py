#!/usr/bin/env python2
import os, sys

for nofElements in xrange(3,6): # nofElements must be <10 to permit simple variable naming below
    with open("gen_alldiff_ladder_"+str(nofElements)+".txt","w") as outFile:
        outFile.write("// All-Difference Ladder "+str(nofElements)+" obj.\n")
        
        # Write Bit definition A
        for i in xrange(0,nofElements):
            for j in xrange(0,nofElements-1):
                print >>outFile,"var v"+str(i)+str(j)
            for j in xrange(0,nofElements):
                if j==0:
                    print >>outFile,"s"+str(i)+str(j)+" = v"+str(i)+str(j)
                elif j<nofElements-1:
                    print >>outFile, "s"+str(i)+str(j)+" = v"+str(i)+str(j)+" & ! v"+str(i)+str(j-1)
                else:
                    print >>outFile, "s"+str(i)+str(j)+" = !v"+str(i)+str(j-1)
                
        # Constraints
        print >>outFile,"encode = true"
        for i in xrange(0,nofElements):
            print >>outFile,"encode = encode & (false",        
            for j in xrange(0,nofElements):
                print >>outFile," | s"+str(i)+str(j),
            print >>outFile,")"
            
        for i in xrange(0,nofElements):
            for j in xrange(0,nofElements-2):
                print >>outFile,"encode = encode & (!v"+str(i)+str(j)+" | v"+str(i)+str(j+1)+")"
            for j in xrange(0,nofElements):
                for k in xrange(j+1,nofElements):
                    print >>outFile,"encode = encode & (!s"+str(i)+str(j)+" | !s"+str(i)+str(k)+")"
                    print >>outFile,"encode = encode & (!s"+str(j)+str(i)+" | !s"+str(k)+str(i)+")"

