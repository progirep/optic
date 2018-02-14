#!/usr/bin/env python3
import os, sys, random, math

random.seed(42,version=2)

for nofElements in range(3,5):
    for thisOne in range(0,100):
        with open("gen_bipatite_matching_"+str(nofElements)+"_"+str(thisOne)+".txt","w") as outFile:
            outFile.write("// Bipatite matching, "+str(nofElements)+" obj's, ex. "+str(thisOne)+"\n")

            # Generate random graphs until one has a good number of matchings
            done = False
            maxNofMatchings = math.ceil(math.sqrt(math.factorial(nofElements)))
            minNofMatchings = math.floor(math.sqrt(math.factorial(nofElements)))            
            
            while not done:

                graph = set([])
                for i in range(0,nofElements):
                    for j in range(0,nofElements):
                        if random.random()<0.5:
                            graph.add((i,j))
            
                # Check how many bitatite matchings
                def countMatchings(prefix,usedTargets):
                    if len(prefix)==nofElements:
                        return 1
                    thisSum = 0
                    for i in range(0,nofElements):
                        if not i in usedTargets:
                            if (len(prefix),i) in graph:
                                thisSum += countMatchings(prefix+[(len(prefix),i)],usedTargets+[i])
                    return thisSum
                    
                thisNof = countMatchings([],[])
                # print (nofElements,thisNof,minNofMatchings,maxNofMatchings)
                done = (minNofMatchings<=thisNof) and (maxNofMatchings>=thisNof) 
            
        
            # Write Bit definition
            nofBitsPerElement = 1
            while (1 << nofBitsPerElement)<nofElements:
                nofBitsPerElement += 1
            
            for j in range(0,nofElements):
                for i in range(0,nofBitsPerElement):
                    outFile.write("var a"+str(j)+"b"+str(i)+"\n")
                            

            # Write assignment definitions
            for i in range(0,nofElements):
                for j in range(0,nofElements):
                    outFile.write("match"+str(i)+"to"+str(j)+" = (true")
                    for k in range(0,nofBitsPerElement):
                        if (j & (1 << k))>0:
                            outFile.write(" & a"+str(i)+"b"+str(k))
                        else:
                            outFile.write(" & ! a"+str(i)+"b"+str(k))
                    outFile.write(")\n")    
            
            # Encode that we have to have a matching
            outFile.write("encode = true\n")
            for i in range(0,nofElements):
                outFile.write("encode = encode & (false")
                for j in range(0,nofElements):
                    if (i,j) in graph:
                        outFile.write(" | match"+str(i)+"to"+str(j))
                outFile.write(")\n")
                
            # Encode that no collisions are possible
            for iA in range(0,nofElements):
                for iB in range(iA+1,nofElements):      
                    for j in range(0,nofElements):
                      outFile.write("encode = encode & (!match"+str(iA)+"to"+str(j)+" | !match"+str(iB)+"to"+str(j)+")\n")
                
