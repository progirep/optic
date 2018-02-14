#!/usr/bin/env python2
import os, sys

for nofBits in xrange(1,7):
    for carry in [0,1]:
        if carry==1:
            carryString = "_carry"
        else:
            carryString = ""
        with open("gen_add_"+str(nofBits)+carryString+".txt","w") as outFile:
            outFile.write("// Adder, "+str(nofBits)+" bits")
            if carry==1:
                print >>outFile,", carry output"
            else:
                print >>outFile,""
        
            # Write Bit definition A
            for i in xrange(0,nofBits):
                print >>outFile,"var a"+str(i)
            # Write Bit definition B
            for i in xrange(0,nofBits):
                print >>outFile,"var b"+str(i)            
            # Write Out definition
            for i in xrange(0,nofBits):
                print >>outFile,"var x"+str(i)
            if carry==1:
                print >>outFile,"var x"+str(nofBits)
            
                
            # Adders and carries
            print >>outFile,"ob0 = a0 ^ b0"
            print >>outFile,"cb0 = a0 & b0"
            for j in xrange(1,nofBits):
                print >>outFile,"ob"+str(j)+" = cb"+str(j-1)+" ^ a"+str(j)+" ^ b"+str(j)
                print >>outFile,"cb"+str(j)+" = cb"+str(j-1)+" & (a"+str(j)+" | b"+str(j)+") | (a"+str(j)+" & b"+str(j)+")"
                
            # Final Result
            print >>outFile,"encode = true",
            for j in xrange(0,nofBits):
                print >>outFile,"& (x"+str(j)+" <-> ob"+str(j)+")",
            if carry==1:
                print >>outFile,"& (x"+str(nofBits)+" <-> cb"+str(nofBits-1)+")"
            else:
                print >>outFile,""

