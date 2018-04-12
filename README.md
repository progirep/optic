Optic: The Propagation-Optimal CNF Encoder
===========================================================================
(C) by Ruediger Ehlers

Optic is a tool to compute confunctive normal form (CNF) encodings of Boolean constraints. If you have questions, please leave a note under https://github.com/progirep/optic/issues.

License
-------

Optic is available under GPLv3 license.

Preparation:
------------

The optic tool is written in C++. Before the tool can be used, some tools/libraries need to be downloaded:

- The CUDD decision diagram library by [Fabio Somenzi](http://vlsi.colorado.edu/~fabio/), version 3.0
- The SAT solver [lingeling](http://fmv.jku.at/lingeling/) by Armin Biere

For rerunning the experiments, the [GenPCE](https://github.com/sat-group/genpce) tool also needs to be downloaded. An additional timeout script is also needed for running the experiments.

All of them can be obtained using the following command sequence (tested on Ubuntu Linux v.17.10)

    cd lib; wget ftp://vlsi.colorado.edu/pub/cudd-3.0.0.tar.gz; tar -xvzf cudd-3.0.0.tar.gz; cd ..
    cd lib; wget http://fmv.jku.at/lingeling/lingeling-bbc-9230380-160707.tar.gz; tar -xvzf lingeling-bbc-9230380-160707.tar.gz; cd ..
    cd lib; git clone https://github.com/sat-group/genpce; cd genpce; git checkout 87cf2949ff360af1431d8b4ae09ad4018a8abe80; cd ../..
    cd tools; wget https://raw.githubusercontent.com/pshved/timeout/edb59c93c167c15ede5ccc2795e1abee25ebf9b4/timeout; chmod +x timeout; cd ..

Please also visit the home pages of these tools.

The following commands build the main tool and some auxiliary tools:
    
    cd src; make -f DirectMakefile; cd ..
    cd tools/conflictingTester; make -f DirectMakefile; cd ../..
    cd tools/propagationTester; make -f DirectMakefile; cd ../..


Using Optic
--------------------------

The Optic tool takes constraint specifications in the form of Boolean formulas. The following is an example constraint file for a two-bit adder with carry output:

    // Full adder, 2 bits, carry output
    var a0
    var a1
    var b0
    var b1
    var x0
    var x1
    var x2
    ob0 = a0 ^ b0
    cb0 = a0 & b0
    ob1 = cb0 ^ a1 ^ b1
    cb1 = cb0 & (a1 | b1) | (a1 & b1)
    encode = true & (x0 <-> ob0) & (x1 <-> ob1) & (x2 <-> cb1)

Variable declarations and comments are always on separate lines. The other lines assign Boolean formula to new identifiers using the usual Boolean operators. The encoded constraint must be stored in the _encode_ variable at the end of the constraint description. Variable numbers in the CNF encoding are assigned in the order in which the variables are declared in the constraint files.

To compute a greedy CNF encoding, optic takes two parameters: `--greedy` and the constraint file name. The generated CNF encoding is printed on the standard output.

To compute an approximately propagation complete and approximately conflict propagating CNF encoding, optic takes four parameters: `--approx`, the propagation completeness quality level, the constraint propagation quality level, and the constraint file name. The generated CNF encoding is then printed on the standard output. For this mode of operation, the environment variable MAXSATSOLVERPATH needs to point to a MaxSAT solver executable, such as LMHS.


Running the benchmarks from the paper
-------------------------------------

Step 1 is to compile GenPCE:

    cd lib/genpce; make; cd ../..
    
Then, we need to call all the benchmark generator scripts in the "benchmarks" directory:

    cd benchmarks; ./generator_adder.py; cd ..
    cd benchmarks; ./generator_from_genpce.py; cd ..
    cd benchmarks; ./generator_alldiff_cook.py; cd ..
    cd benchmarks; ./generator_mult.py; cd ..
    cd benchmarks; ./generator_alldiff_ladder.py; cd ..
    cd benchmarks; ./generator_sqrt.py; cd ..
    cd benchmarks; ./generator_alldiff.py; cd ..
    cd benchmarks; ./generator_square.py; cd ..
    cd benchmarks; ./generator_bipatite_matching.py; cd ..
    cd benchmarks; ./generator_ult.py; cd ..

All of these steps generate files with the names `gen_`...`.txt` in the benchmarks folder. These are constraint specification files in the format described above. Now we can make the Makefile for running the experiments:

    cd benchmarks; ./make_benchmark_makefile.py; cd ..
    
The experiments can now be run with:
    
    cd benchmarks; make; cd ..
    
If multiple processor cores and more than 8 GB of RAM per core is available, the computation time can be decreased by running `make -j<number of processor cores>` in the benchmarks folder instead. 

At the end of the computation, the file "benchmarks/table.pdf" contains the overall result table, and "benchmarks/tableshort.pdf" the short result table.


Running the integer factoring case study
----------------------------------------

As preparation, we need a python library for prime number testing.

    cd casestudies/factoring; wget https://raw.githubusercontent.com/CamDavidsonPilon/projecteuler-utils/70491a136f033051b61c4f4cc21c639cd35abf69/primality_tests.py -O prime_test.py; cd ../..

The addition and multiplication CNF encodings are already in the folders `casestudies/factoring/blocks<something>`, where the 4-bit full adder in the (3,3) case may not have a minimal number of clauses.
    
The following command then generates some benchmarks:

    cd casestudies/factoring; ./generate_benchmarks.py; cd ../..
    cd casestudies/factoring; ./make_benchmark_makefile.py; cd ../..
    
If exactly the composite numbers from the paper are to be used, the first character of the line

    # products = [90115705646749,87794528125921,421926227,189760523]

in the file `casestudies/factoring/generate_benchmarks.py` needs to be removed (so that no new products of random primes numbers are used).

Before running the benchmarks, we need to compile lingeling and download and compile MapleSAT as solvers:

    cd lib/lingeling-bbc-9230380-160707; ./configure.sh; make; cd ../..
    cd lib; wget https://sites.google.com/a/gsd.uwaterloo.ca/maplesat/MapleCOMSPS_LRB.zip; unzip MapleCOMSPS_LRB.zip; cd MapleCOMSPS_LRB/core; export MROOT=$PWD/..; make; cd ../../..
    
Now be benchmark can be obtained with:
    
    cd casestudies/factoring; make -j<number of processor cores>; cd ../..

This will generate the plot file `casestudies/factoring/summary.pdf` with the cactus plot.


Running the stair-shaped Sudoku case study
------------------------------------------
As preparation, the SAT solver `picosat` should be in the path. In Ubuntu Linux, this can be made sure with `sudo apt-get install picosat`.

The first step is the generation of some stair-shaped sudokus. This can be done with the following command:

    cd casestudies/sudoku/sudokuBuilder/; ./stairSudokuBuilder.py; cd ../../..
    
Afterwards, the CNF problems can be generated (from the Sudokus) as follows:

    cd casestudies/sudoku/satInstanceBuilder; ./builderStair.py ; cd ../../..
    
The benchmark Makefile can then be generated with the following command:

    cd casestudies/sudoku/satEncodings; ./make_benchmark.py; cd ../../..

The benchmark results can then be computed as follows:

    cd casestudies/sudoku/satEncodings; make -j<number of processor cores>; cd ../..

