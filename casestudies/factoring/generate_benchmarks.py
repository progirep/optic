#!/usr/bin/env python3
# Generate SAT instances for factoring integers
import prime_test
import random, math, sys

BIT_WIDTHS = [8,16,24]
NOF_EXAMPLES_PER_BIT_WIDTH = 2
MULT_SIZES = [(3,5),(2,4),(1,1)]
ADDER_SIZES = [(3,4),(2,3),(1,2)]

MAX_MULT_WIDTH = max([a for (a,b) in MULT_SIZES])
MAX_ADD_WIDTH = max([a for (a,b) in ADDER_SIZES])

# ===============================
# Some Global Caches
# ===============================
GlobalCNFFileCache = {}

# ===============================
# Generate some products
# ===============================
products = []
prime_test._mrpt_num_trials = 20
for j in BIT_WIDTHS:
    for i in range(0,NOF_EXAMPLES_PER_BIT_WIDTH):
        valueA = random.getrandbits(j)+3
        while not prime_test.is_probably_prime(valueA):
            valueA = random.getrandbits(j)+3
        valueB = random.getrandbits(j)+3
        while not prime_test.is_probably_prime(valueB):
            valueB = random.getrandbits(j)+3
        products.append(valueA*valueB)
        
# products = [90115705646749,87794528125921,421926227,189760523]
products.sort()
print("Random numbers:")
for a in products:
    print("- "+str(a))
    
    
for blockType in ["OP","Minimal","33","9999"]:
    # ===============================
    # Define Blocks
    # ===============================
    class Block:
        def __init__(self):
            self.ports = []
            self.portsAbove = []
            self.connections = []
            self.name = "?"
            self.inputFile = None
        def encode(self,varMapping):
            clauses = []
            # Implement data file caching
            if (self.inputFile) in GlobalCNFFileCache:
                allLines = GlobalCNFFileCache[self.inputFile]
            else:
                with open(self.inputFile) as dataFile:
                    allLines = dataFile.readlines()
                    GlobalCNFFileCache[self.inputFile] = allLines
            for line in allLines:
                lineparts = [int(a) for a in line.strip().split(" ")]
                thisClause = []
                for lit in lineparts:
                    if lit<0:
                        thisClause.append(-1*varMapping[-1*lit-1])
                    elif lit==0:
                        thisClause.append(0)
                    else:
                        thisClause.append(varMapping[lit-1])
                clauses.append(thisClause)
            return clauses
            
    class SourceBlock(Block):
        def __init__(self,nofBits):
            self.ports = ["a"+str(i) for i in range(0,nofBits)]
            self.portsAbove = []
            self.name = "src"
        def encode(self,varMapping):
            return []
            

    class DestBlock(Block):
        def __init__(self,nofBits,data):
            self.ports = ["x"+str(i) for i in range(0,nofBits)]
            self.portsAbove = self.ports
            self.name = "dest"
            self.data = data
        def encode(self,varMapping):
            if (self.data >= (1 << len(self.ports))):
                raise Exception("Error: Not enough space in the destination block!")
            clauses = []
            for i in range(0,len(self.ports)):
                if (self.data & (1 << i))>0:
                    clauses.append([varMapping[i],0])
                else:
                    clauses.append([-1*varMapping[i],0])
            return clauses

    class ZeroBlock(Block):
        def __init__(self):
            self.ports = ["z"]
            self.portsAbove = []
            self.name = "zero"
            self.inputFile = "blocks"+blockType+"/zero.cnf"

    class BaseMultBlock(Block):
        def __init__(self,MULT_WIDTH,OUT_WIDTH):
            self.MULT_WIDTH = MULT_WIDTH
            self.OUT_WIDTH = OUT_WIDTH
            self.ports = ["a"+str(i) for i in range(0,MULT_WIDTH)]+["b"+str(i) for i in range(0,MULT_WIDTH)]+["x"+str(i) for i in range(0,OUT_WIDTH)]
            self.portsAbove = ["a"+str(i) for i in range(0,MULT_WIDTH)]+["b"+str(i) for i in range(0,MULT_WIDTH)]
            self.name = "mult"+str(MULT_WIDTH)
            self.inputFile = "blocks"+blockType+"/mult"+str(MULT_WIDTH)+"_"+str(OUT_WIDTH)+".cnf"
            
    class BaseAddBlock(Block):
        def __init__(self,ADD_WIDTH):
            self.ADD_WIDTH = ADD_WIDTH
            self.ports = ["a"+str(i) for i in range(0,ADD_WIDTH)]+["b"+str(i) for i in range(0,ADD_WIDTH)]+["x"+str(i) for i in range(0,ADD_WIDTH+1)]
            self.portsAbove = ["a"+str(i) for i in range(0,ADD_WIDTH)]+["b"+str(i) for i in range(0,ADD_WIDTH)]
            self.name = "add"+str(ADD_WIDTH)
            self.inputFile = "blocks"+blockType+"/adder"+str(ADD_WIDTH)+"_"+str(ADD_WIDTH+1)+".cnf"        
            
    # ===============================
    # Process all numbers
    # ===============================
    for product in products:

        # Iterate over possible factor sizes
        maxSizeSrcA = int(math.ceil(math.log(math.sqrt(product+1))/math.log(2)))

        for nofBitsSrcA in range(2,maxSizeSrcA+1): # SrcA is the lower number

            minValueA = (1 << (nofBitsSrcA-1))
            maxValueA = (1 << (nofBitsSrcA))-1
            minValueB = int(math.floor(float(product)/maxValueA))
            maxValueB = int(math.ceil(float(product)/minValueA))
            
            nofBitsSrcB = int(math.ceil(math.log(maxValueB+1)/math.log(2)))
            
            nofBitsDest = 1
            while (1 << nofBitsDest)<=product:
                nofBitsDest += 1
                
            nofMultLines = 0
            while (nofMultLines*MAX_MULT_WIDTH)<nofBitsSrcA:
                nofMultLines += 1
            nofMultColumns = 0
            while (nofMultColumns*MAX_MULT_WIDTH)<nofBitsSrcB:
                nofMultColumns += 1
            
            # ===============================
            # Define Graph
            # ===============================
            # 1. Basic Blocks
            blocks = [SourceBlock(nofBitsSrcA),SourceBlock(nofBitsSrcB),DestBlock(nofBitsDest,product)]
            connections = []

            # 2. Mult Blocks
            multBlocks = []
            bits = [[] for i in range(0,nofBitsDest*2)]
            for i in range(0,nofMultLines):
                theseBlocks = []
                for j in range(0,nofMultColumns):
                
                    # What is the blockLength that we want?
                    nofBitsLeftA = nofBitsSrcA-i*MAX_MULT_WIDTH
                    nofBitsLeftB = nofBitsSrcB-j*MAX_MULT_WIDTH
                    blockSize = min(max(nofBitsLeftA,nofBitsLeftB),MAX_MULT_WIDTH)
                    outWidth = [b for (a,b) in MULT_SIZES if a==blockSize][0]
                    
                    # Append block
                    theseBlocks.append(len(blocks))
                    blocks.append(BaseMultBlock(blockSize,outWidth))
                    thisBlock = len(blocks)-1
                    for k in range(0,blockSize):
                        if i*MAX_MULT_WIDTH+k < nofBitsSrcA:
                            connections.append(((0,i*MAX_MULT_WIDTH+k),(thisBlock,k)))
                        else:
                            blocks.append(ZeroBlock())
                            connections.append(((len(blocks)-1,0),(thisBlock,k)))
                    for k in range(0,blockSize):
                        if j*MAX_MULT_WIDTH+k < nofBitsSrcB:
                            connections.append(((1,j*MAX_MULT_WIDTH+k),(thisBlock,k+blockSize)))
                        else:
                            blocks.append(ZeroBlock())
                            connections.append(((len(blocks)-1,0),(thisBlock,k+blockSize)))
                    for k in range(0,outWidth):
                        bits[(i+j)*MAX_MULT_WIDTH+k].append((thisBlock,k+blockSize*2))
                multBlocks.append(theseBlocks)
            
            # 3. Adder Circuits
            print("Nof MultBlocks: ",len(blocks),file=sys.stderr)
            adderBlocks = []
            done = False
            while not done:
                minMultibits = -1
                for i in range(0,len(bits)):
                    if len(bits[i])>1 and (minMultibits==-1):
                        minMultibits = i
                if minMultibits == -1 or minMultibits >= nofBitsDest:
                    done = True
                else:
                    # Need to compress here
                    newBlock = len(blocks)
                    # print("Rest: ",len(bits)-minMultibits,minMultibits,len(bits[minMultibits]))
                    oldSize = len(bits[minMultibits])
                    maxBitPos = max([i for i in range(0,len(bits)) if len(bits[i])>0])
                    blockLength = max(1,min(MAX_ADD_WIDTH,maxBitPos-minMultibits))
                    while blockLength>1 and len(bits[minMultibits+blockLength-1])<=1:
                        blockLength -= 1 # No need to have overly long adder
                    blocks.append(BaseAddBlock(blockLength))
                    # Input A
                    for a in range(0,blockLength):
                        if len(bits[a+minMultibits])>0:
                            connections.append((bits[a+minMultibits][0],(newBlock,a)))
                            bits[a+minMultibits] = bits[a+minMultibits][1:]
                        else:
                            blocks.append(ZeroBlock())
                            connections.append(((len(blocks)-1,0),(newBlock,a)))
                    # Input B
                    for a in range(0,blockLength):
                        if len(bits[a+minMultibits])>0:
                            connections.append((bits[a+minMultibits][0],(newBlock,a+blockLength)))
                            bits[a+minMultibits] = bits[a+minMultibits][1:]                    
                        else:
                            blocks.append(ZeroBlock())
                            connections.append(((len(blocks)-1,0),(newBlock,a+blockLength)))
                    # Output
                    # print("RestB: ",len(bits)-minMultibits,minMultibits,len(bits[minMultibits]),blockLength,nofBitsDest,len(bits),maxBitPos)
                    for a in range(0,blockLength+1):
                        bits[a+minMultibits].append((newBlock,a+2*blockLength))
                    assert oldSize>len(bits[minMultibits])
                    
            # Connect bits to sink
            print("Nof All blocks: ",len(blocks),file=sys.stderr)
            for i in range(0,nofBitsDest):
                # print("D:"+str(i))
                connections.append((bits[i][0],(2,i)))
                
            # Connect all other bits to 0.
            for i in range(nofBitsDest,len(bits)):
                for b in bits[i]:
                    # Connect to ZERO
                    blocks.append(ZeroBlock())
                    connections.append(((len(blocks)-1,0),b))

            # ===============================================
            # Generate CNF
            # ===============================================
            with open("factor_"+str(product)+"_"+str(nofBitsSrcA)+blockType+".cnf","w") as cnfFile:
                clauses = []  
                
                # Order Connections
                orderedConnections = {}
                for (a,b) in connections:
                    if not a in orderedConnections:
                        orderedConnections[a] = [b]
                    else:
                        orderedConnections[a].append(b)
                    if not b in orderedConnections:
                        orderedConnections[b] = [a]
                    else:
                        orderedConnections[b].append(a)
                        
                # Allocate variables in a way such that connected edges all get
                # the same variable, no matter if they are forward or backward connected
                blockVarAssignments = {}
                doneVarAssignment = set([])
                nofVarsSoFar=0
                for a in orderedConnections:
                    if not a in doneVarAssignment:
                        nofVarsSoFar += 1
                        m = nofVarsSoFar        
                        todo = set([a]+orderedConnections[a])
                        while len(todo)>0:
                            thisOne = todo.pop()                
                            blockVarAssignments[thisOne] = m
                            doneVarAssignment.add(thisOne)
                            for c in orderedConnections[thisOne]:
                                if not c in doneVarAssignment:
                                    todo.add(c)
                cnfVars = {}
                for (a,b) in connections:
                    assert blockVarAssignments[a] == blockVarAssignments[b]
                    cnfVars[(a,b)] = blockVarAssignments[a]
                    
                # Encode all blocks
                for i in range(0,len(blocks)):
                    localVars = {k:v for ((u,k),v) in blockVarAssignments.items() if u==i}
                    # print("Polymer:",blocks[i])
                    # print(localVars)
                    clauses.extend(blocks[i].encode(localVars))
                    
                    
                # Encode known bits: SrcA highest bit
                clauses.append([blockVarAssignments[(0,nofBitsSrcA-1)],0])
                
                # Encode known bits: SrcB lower bound
                for i in range(0,nofBitsSrcB):
                    if ((1 << i) & minValueB) > 0:
                        clause = [blockVarAssignments[(1,i)]]
                        for j in range(i+1,nofBitsSrcB):
                            if ((1 << j) & minValueB) == 0:
                                clause.append(blockVarAssignments[(1,j)])
                        clause.append(0)
                        clauses.append(clause)
                        
                # Encode known bits: SrcB Upper bound
                for i in range(0,nofBitsSrcB):
                    if ((1 << i) & maxValueB) == 0:
                        clause = [-1*blockVarAssignments[(1,i)]]
                        for j in range(i+1,nofBitsSrcB):
                            if ((1 << j) & maxValueB) > 0:
                                clause.append(-1*blockVarAssignments[(1,j)])
                        clause.append(0)
                        clauses.append(clause)

                cnfFile.write("p cnf "+str(len(cnfVars))+" "+str(len(clauses))+"\n")
                for clause in clauses:
                    cnfFile.write(" ".join([str(a) for a in clause])+"\n")
                
                # Print VAR assignment
                cnfFile.write("c Bits (LSB first) of Factor A:")
                localVars = {k:v for ((u,k),v) in blockVarAssignments.items() if u==0}
                for i in range(0,nofBitsSrcA):
                    cnfFile.write(" "+str(localVars[i]))
                localVars = {k:v for ((u,k),v) in blockVarAssignments.items() if u==1}
                cnfFile.write("\nc Bits (LSB first) of Factor B:")
                for j in range(0,nofBitsSrcB):
                    cnfFile.write(" "+str(localVars[j]))
                cnfFile.write("\nc MinValueB: "+str(minValueB))
                cnfFile.write("\nc MaxValueB: "+str(maxValueB))            
                cnfFile.write("\n")
                
            # ===============================
            # Draw Graph
            # ===============================
            with open("factor_"+str(product)+"_"+str(nofBitsSrcA)+".dot","w") as dotFile:
                dotFile.write("digraph {\n")
                
                # Draw all blocks
                for blockNo in range(0,len(blocks)):
                    dotFile.write("struct"+str(blockNo)+" [shape=record,label=\"{{")
                    firstPort = True
                    for i,port in enumerate(blocks[blockNo].ports):
                        if port in blocks[blockNo].portsAbove:
                            if firstPort:
                                firstPort = False
                            else:
                                dotFile.write(" | ")
                            dotFile.write("<p"+str(i)+"> "+port)
                    dotFile.write("} | "+blocks[blockNo].name+":"+str(blockNo)+" | {")
                    firstPort = True
                    for i,port in enumerate(blocks[blockNo].ports):
                        if not port in blocks[blockNo].portsAbove:
                            if firstPort:
                                firstPort = False
                            else:
                                dotFile.write(" | ")
                            dotFile.write("<p"+str(i)+"> "+port)
                    dotFile.write("}}\"];\n")
                
                # Draw connections...
                for ((a,b),(c,d)) in connections:
                    dotFile.write("struct"+str(a)+":p"+str(b)+" -> struct"+str(c)+":p"+str(d)+"[label=\""+str(cnfVars[((a,b),(c,d))])+"\"];\n")
                    
                dotFile.write("}\n")
                
