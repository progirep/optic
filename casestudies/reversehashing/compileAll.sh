set -e
./compileOperators.sh
./compileSSA2SAT.py 199OPs $1 < md5algo.txt
./compileSSA2SAT.py 299OPs $1 < md5algo.txt
./compileSSA2SAT.py 399OPs $1 < md5algo.txt
./compileSSA2SAT.py 9999OPs $1 < md5algo.txt
./compileSSA2SAT.py 991OPs $1 < md5algo.txt
./compileSSA2SAT.py GreedyOPs $1 < md5algo.txt
./make_benchmark_makefile.py
