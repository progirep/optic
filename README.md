Optic: The Propagation-Optimal CNF Encoder
===========================================================================

Optic is a tool to compute confunctive normal form (CNF) encodings of Boolean constraints. If you have questions, please leave a note under https://github.com/progirep/optic/issues.

License
-------

Optic is available under GPLv3 license.

Preparation:
------------

The optic tool is written in C++. Before the tool can be used, some libraries need to be downloaded:

- The CUDD decision diagram library by [http://vlsi.colorado.edu/~fabio/ Fabio Somenzi], version 3.0
- The SAT solver [http://fmv.jku.at/lingeling/ lingeling] by Armin Biere

For rerunning the experiments, the [https://github.com/sat-group/genpce GenPCE] tool also needs to be downloaded.

All of them can be obtained using the following command sequence (tested on Ubuntu Linux v.17.10)

    cd lib; wget ftp://vlsi.colorado.edu/pub/cudd-3.0.0.tar.gz; tar -xvzf cudd-3.0.0.tar.gz; cd ..
    cd lib; wget http://fmv.jku.at/lingeling/lingeling-bbc-9230380-160707.tar.gz; tar -xvzf lingeling-bbc-9230380-160707.tar.gz; cd ..
    cd lib; git clone https://github.com/sat-group/genpce; cd genpce; git checkout 87cf2949ff360af1431d8b4ae09ad4018a8abe80; cd ../..

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

Variable declarations and comments are always on separate lines. The other lines assign Boolean formula to new identifiers using the usual Boolean operators. The encoded constraint must be stored in the /encode/ variable at the end of the constraint description. Variable numbers in the CNF encoding are assigned in the order in which the variables are declared in the constraint files.

To compute a greedy CNF encoding, optic takes two parameters: +--greedy+ and the constraint file name. The generated CNF encoding is printed on the standard output.

To compute an approximately propagation complete and approximately conflict propagating CNF encoding, optic takes four parameters: +--approx+, the propagation completeness quality level, the constraint propagation quality level, and the constraint file name. The generated CNF encoding is then printed on the standard output. For this mode of operation, the environment variable MAXSATSOLVERPATH needs to point to a MaxSAT solver executable, such as LMHS.


