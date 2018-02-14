#!/usr/bin/env python2
import os, sys

for nofBits in xrange(1,10):
    for outBit in ["noOutputBit","outputBit"]:
        with open("gen_ult_"+str(nofBits)+"_"+outBit+".txt","w") as outFile:
        
            # Write Bit definition A
            for i in xrange(0,nofBits):
                print >>outFile,"var a"+str(i)
            # Write Bit definition B
            for i in xrange(0,nofBits):
                print >>outFile,"var b"+str(i)            
            # Write Out definition
            if outBit=="outputBit":
                print >>outFile,"var x"
            
            # Or ULT
            print >>outFile,"t0 = (!a0 & b0)"        
            for i in xrange(1,nofBits):
                print >>outFile,"t"+str(i)+" = t"+str(i-1)+" & (a"+str(i)+" <-> b"+str(i)+") | (!a"+str(i)+" & b"+str(i)+")"
                                            
            # Final Result
            if outBit=="outputBit":
                print >>outFile,"encode = (x <-> t"+str(nofBits-1)+")"
            else:
                print >>outFile,"encode = t"+str(nofBits-1)  
            

