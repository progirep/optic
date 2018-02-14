#!/usr/bin/env python2
# Generates all-difference constraints.
# Uses additional variables as introduced by Cook in 
# "A SHORT PROOF OF THE PIGEON HOLE PRINCIPLE USING EXTENDED RESOLUTION"
#
# Note that the paper talks about the pidgeon hole principle, while this here
# talks about all-diff constraints.
import os, sys

for nofElements in xrange(3,5): # nofElements must be <10 to permit simple variable naming below
    with open("gen_alldiff_"+str(nofElements)+"_cook.txt","w") as outFile:
        outFile.write("// All-Difference Cook "+str(nofElements)+" obj.\n")
        
        # Write Bit definition A
        for i in xrange(0,nofElements):
            for j in xrange(0,nofElements):
                print >>outFile,"var s"+str(i)+str(j)

        for i in xrange(0,nofElements-1):
            for j in xrange(0,nofElements-1):
                print >>outFile,"var q"+str(i)+str(j)
                
        # Constraints
        print >>outFile,"encode = true"
        for i in xrange(0,nofElements):
            print >>outFile,"encode = encode & (false",        
            for j in xrange(0,nofElements):
                print >>outFile,"| s"+str(i)+str(j),
            print >>outFile,")"
            
        for i in xrange(0,nofElements):
            for j in xrange(0,nofElements):
                for k in xrange(j+1,nofElements):
                    print >>outFile,"encode = encode & (!s"+str(i)+str(j)+" | !s"+str(i)+str(k)+")"
                    print >>outFile,"encode = encode & (!s"+str(j)+str(i)+" | !s"+str(k)+str(i)+")"

        # Added "Q" constraints from the paper
        for i in xrange(0,nofElements-1):
            for j in xrange(0,nofElements-1):
                print >>outFile,"encode = encode & (q"+str(i)+str(j)+" <-> (s"+str(i)+str(j)+" | (s"+str(i)+str(nofElements-1)+" & s"+str(nofElements-1)+str(j)+")))"
        
