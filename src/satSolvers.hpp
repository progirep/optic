#ifndef __SAT_SOLVERS_HPP__
#define __SAT_SOLVERS_HPP__

extern "C" {
#include "lglib.h"
}
#include <cstdio>

/*class PicosatSolver {
private:
    PicoSAT *picosat;
public:
    inline PicosatSolver() { picosat = picosat_init(); }
    inline ~PicosatSolver() { picosat_reset(picosat); }
    PicosatSolver(const PicosatSolver&) = delete;
    inline void add(int literal) { picosat_add(picosat,literal); }
    inline bool solve() { int result = picosat_sat(picosat,-1);
                    if (result==PICOSAT_SATISFIABLE) return true;
                    if (result==PICOSAT_UNSATISFIABLE) return false;
                    throw "Error: Unknown PICOSAT result.";
    }
    inline bool getVariableValue(int variable) {
        return picosat_deref(picosat,variable)==1;
    }
    inline void assume(int literal) {
        picosat_assume(picosat,literal);
    }
    inline void markVariableAsIncremental(int variable) {
        (void)variable;
    }
};*/


class LingelingSolver {
private:
     LGL *lingeling;
#ifndef NDEBUG
     std::set<int> usedVariables;
     std::set<int> unfrozenVariables;
     std::set<int> frozenVariables;
#endif
public:
    inline LingelingSolver() {
        lingeling = lglinit();
        lglsetout(lingeling,stderr);
    }
    inline ~LingelingSolver() { lglrelease(lingeling); }
    LingelingSolver(const LingelingSolver&) = delete;
    inline void add(int literal) {
#ifndef NDEBUG
        if (literal!=0) {
            assert(lglusable(lingeling,std::abs(literal)));
            usedVariables.insert(std::abs(literal));
        }
        assert(unfrozenVariables.count(std::abs(literal))==0);
#endif
        lgladd(lingeling,literal);
    }
    inline bool solve() {
       #ifndef NDEBUG
       for (auto it : usedVariables) {
           if (frozenVariables.count(it)==0) {
               unfrozenVariables.insert(it);
           }
       }
       #endif

       /*int result1 = lglsimp(lingeling,1);
       if (result1==LGL_SATISFIABLE) return true;
       if (result1==LGL_UNSATISFIABLE) return false;*/

        int result = lglsat(lingeling);
        if (result==LGL_SATISFIABLE) return true;
        if (result==LGL_UNSATISFIABLE) return false;
        throw "Error: Unknown LINGELING result.";
    }
    inline bool getVariableValue(int variable) {
        assert(variable>0);
        return lglderef(lingeling,variable)>0;
        assert(unfrozenVariables.count(variable)==0);
    }
    inline void assume(int literal) {
        assert(frozenVariables.count(std::abs(literal))!=0);
        lglassume(lingeling,literal);
    }
    inline void markVariableAsIncremental(int variable) {
        lglfreeze(lingeling,variable);
#ifndef NDEBUG
        frozenVariables.insert(variable);
#endif
    }
};



#endif
