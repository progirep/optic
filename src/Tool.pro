# QMake Build file
# QMAKE_CC = gcc
# QMAKE_LINK_C = gcc
# QMAKE_CXX = g++
# QMAKE_LINK = g++

BDDFLAGS = $$system(gcc BFAbstractionLibrary/compilerOptionGenerator.c -o /tmp/BFAbstractionCompilerOptionsProducer-$$(USER);/tmp/BFAbstractionCompilerOptionsProducer-$$(USER))
DEFINES += USE_CUDD NDEBUG
CFLAGS += -g -fpermissive
LINGELINGFLAGS = -DNLGLOG -DNCHKSOL -DNLGLDRUPLIG -DNLGLYALSAT -DNLGLFILES -DNLGLDEMA

QMAKE_LFLAGS = # -static # -fsanitize=address

QMAKE_CFLAGS_X86_64 = -arch x86_64
QMAKE_CXXFLAGS_X86_64 = -arch x86_64

QMAKE_CFLAGS_RELEASE += -g \
    $$BDDFLAGS $$LINGELINGFLAGS # -fsanitize=address
QMAKE_CXXFLAGS_RELEASE += -g -std=c++14  \
    $$BDDFLAGS $$LINGELINGFLAGS # -fsanitize=address
QMAKE_CFLAGS_DEBUG += -g -Wall -Wextra \
    $$BDDFLAGS $$LINGELINGFLAGS  # -fsanitize=address
QMAKE_CXXFLAGS_DEBUG += -g -std=c++14 -Wall -Wextra \
    $$BDDFLAGS $$LINGELINGFLAGS  # -fsanitize=address

TEMPLATE = app \
    console
CONFIG += release
CONFIG -= app_bundle
CONFIG -= qt
HEADERS += BFAbstractionLibrary/BF.h BFAbstractionLibrary/BFCudd.h translatorClassFast.hpp translatorClassPrecise.hpp \
           encoderContext.hpp booleanFormulaParser.hpp translatorClassNonPropagating.hpp satSolvers.hpp translatorClassApproximatelyOptimallyPropagating.hpp \
           translatorClassMinimalNonPropagatingEncoding.hpp \
           ../lib/lingeling-bal-2293bef-151109/lglib.h \
           translatorClassDoublyApproximatelyOptimallyMAXSAT.hpp

SOURCES += BFAbstractionLibrary/bddDump.cpp BFAbstractionLibrary/BFCuddVarVector.cpp BFAbstractionLibrary/BFCudd.cpp BFAbstractionLibrary/BFCuddManager.cpp \
    BFAbstractionLibrary/BFCuddVarCube.cpp main.cpp \
    encoderContext.cpp booleanFormulaParser.cpp translatorClassNonPropagating.cpp \
    ../lib/lingeling-bal-2293bef-151109/lglib.c ../lib/lingeling-bal-2293bef-151109/lglopts.c

TARGET = optic
INCLUDEPATH = ../lib/cudd-3.0.0/cudd ../lib/cudd-3.0.0/ ../lib/cudd-3.0.0/st ../lib/cudd-3.0.0/mtr ../lib/cudd-3.0.0/epd BFAbstractionLibrary ../lib/lingeling-bal-2293bef-151109

LIBS += -L../lib/cudd-3.0.0/lib -L../lib/cudd-3.0.0/cudd -L../lib/cudd-3.0.0/util -L../lib/cudd-3.0.0/mtr -L../lib/cudd-3.0.0/st -L../lib/cudd-3.0.0/dddmp -L../lib/cudd-3.0.0/epd -static -lcudd # -ldddmp -lmtr -lepd -lst -lutil # -fsanitize=address

PKGCONFIG += 
QT -= gui \
    core
