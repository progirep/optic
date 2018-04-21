set -e
./compileOperators.sh
./compileSSA2SAT.py 199OPs < md5algo.txt
./compileSSA2SAT.py 299OPs < md5algo.txt
./compileSSA2SAT.py 399OPs < md5algo.txt
./compileSSA2SAT.py 9999OPs < md5algo.txt
./compileSSA2SAT.py 991OPs < md5algo.txt
./compileSSA2SAT.py 33OPs < md5algo.txt
./compileSSA2SAT.py GreedyOPs < md5algo.txt
./make_benchmark_makefile.py
