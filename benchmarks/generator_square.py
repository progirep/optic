#!/usr/bin/env python2
import os, sys

for nofBits in xrange(1,8):
    for nofOutputBits in [nofBits*2]:
        with open("gen_square_"+str(nofBits)+".txt","w") as outFile:
            print >>outFile,"// Square function, "+str(nofBits)+" bits"
        
            # Write Bit definition A
            for i in xrange(0,nofBits):
                print >>outFile,"var a"+str(i)
            # Write Out definition
            for i in xrange(0,nofOutputBits):
                print >>outFile,"var x"+str(i)
                
            # AND matrix for multiplication
            for i in xrange(0,nofBits):
                for j in xrange(0,nofBits*2):
                    print >>outFile,"p"+str(i)+"_"+str(j)+" = a"+str(i)+" &",
                    if j>=i and j-i<nofBits:
                        print >>outFile,"a"+str(j-i)
                    else:
                        print >>outFile,"false"
            for i in xrange(nofBits,nofBits*2):
                for j in xrange(0,nofBits*2):
                    print >>outFile,"p"+str(i)+"_"+str(j)+" = false"
            
            # Adders level 1
            for j in xrange(0,nofBits*2):
                print >>outFile,"ob0_"+str(j)+" = p0_"+str(j)
                
            # Adders first levels
            for k in xrange(1,nofBits):
                for j in xrange(0,k):
                    print >>outFile,"ob"+str(k)+"_"+str(j)+" = ob"+str(k-1)+"_"+str(j)
                    print >>outFile,"cb"+str(k)+"_"+str(j)+" = false"
                for j in xrange(k,nofBits*2):
                    print >>outFile,"ob"+str(k)+"_"+str(j)+" = ob"+str(k-1)+"_"+str(j)+" ^ cb"+str(k)+"_"+str(j-1)+" ^ p"+str(k)+"_"+str(j)
                    print >>outFile,"cb"+str(k)+"_"+str(j)+" = ob"+str(k-1)+"_"+str(j)+" & (cb"+str(k)+"_"+str(j-1)+" | p"+str(k)+"_"+str(j)+") | (cb"+str(k)+"_"+str(j-1)+" & p"+str(k)+"_"+str(j)+")"
                                
            # Final Result
            print >>outFile,"encode = true",
            for j in xrange(0,nofOutputBits):
                print >>outFile,"& (x"+str(j)+" <-> ob"+str(nofBits-1)+"_"+str(j)+")",
            print >>outFile,""
                

