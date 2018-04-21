set -e
set -x
mkdir -p 199OPs
mkdir -p 299OPs
mkdir -p 399OPs
mkdir -p 9999OPs
mkdir -p 991OPs
mkdir -p 33OPs
mkdir -p GreedyOPs

# 1 99
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --approx 1 99 $f > 199OPs/$filename.cnf
done

# 2 99
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --approx 2 99 $f > 299OPs/$filename.cnf
done

# 3 99
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --approx 3 99 $f > 399OPs/$filename.cnf
done

# 99 99
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --approx 99 99 $f > 9999OPs/$filename.cnf
done

# 99 1
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --approx 99 1 $f > 991OPs/$filename.cnf
done

# 3 3
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --approx 3 3 $f > 33OPs/$filename.cnf
done

# Greedy
for f in operators/*.txt
do
    filename=$(basename "$f")
    extension="${filename##*.}"
    filename="${filename%.*}"
    ../../src/optic --greedy $f > GreedyOPs/$filename.cnf
done
