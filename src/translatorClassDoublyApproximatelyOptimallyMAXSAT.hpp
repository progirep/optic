#ifndef __TRANSLATOR_CLASS_APPROXIMATE_MAXSAT_HPP___
#define __TRANSLATOR_CLASS_APPROXIMATE_MAXSAT_HPP___

#include "encoderContext.hpp"
#include "tools.hpp"
#include <fstream>
#include <cuddInt.h>


class AntichainOptimizingClauseSet {
private:
    std::vector<std::list<std::vector<int> > > clausesByLength;

    // Old: 33,7 Mrd operations
    void addAfterItIsClearThatTheNewClauseCannotBeSubset(std::vector<int> &sortedClause, std::list<std::vector<int> > &list) {
        for (std::list<std::vector<int> >::iterator it = list.begin();it!=list.end();) {
            std::vector<int>::iterator it2 = sortedClause.begin();
            for (auto lit : *it) {
                if (it2==sortedClause.end()) goto foundMatch;
                int diff = *it2-lit;
                if (diff!=0) {
                    it++;
                    goto outerForEnd;
                }
                it2++;
            }
            foundMatch:
            //std::cerr << "Detected that the new clause";
            //for (auto j : clause) std::cerr << " " << j;
            //std::cerr << " allows us to remove clause";
            //for (auto j : *it) std::cerr << " " << j;
            //std::cerr << std::endl;
            {
                //std::cerr << "(M1)";
                auto it3 = it;
                it3++;
                list.erase(it);
                it = it3;
            }
            outerForEnd: (void)0;
        }
    }

    bool findClause(std::list<std::vector<int> > &list, std::vector<int> &clause) {
        for (std::list<std::vector<int> >::iterator it = list.begin();it!=list.end();) {
            std::vector<int>::iterator it2 = clause.begin();
            for (auto lit : *it) {
                if (lit!=*(it2++)) goto continueOrder;
            }
            //std::cerr << "(M2)";
            return true;
            continueOrder: it++;
        }
        return false;
    }

    /**
     * @brief add Adds a clause to the clause set. Warning: Clause is modified (by sorting the literals) along the way.
     * @param clause The clause to be added.
     */
    bool checkSubsumption(std::vector<int> &clause, std::list<std::vector<int> > &list) {
        const int maxINT = std::numeric_limits<int>::max();
        clause.push_back(maxINT);
        for (std::list<std::vector<int> >::iterator it = list.begin();it!=list.end();) {
            std::vector<int>::iterator it2 = clause.begin();
            for (auto lit : *it) {
                while (*it2<lit) {
                    it2++;
                }
                if (*it2==maxINT) goto continueOuter;
                if (*it2==lit) {
                    it2++;
                } else {
                    goto continueOuter;
                }
            }
            // Ok, found subsumption.
            clause.pop_back();
            //std::cerr << "(M3)";
            return true;
        continueOuter:
            it++;
        }
        clause.pop_back();
        return false;
    }


public:

    void addWhileKnowingThatTheNewClauseIsNotSubsumed(std::vector<int> &clause) {
        std::sort(clause.begin(),clause.end());
        for (unsigned int i=clause.size()+1;i<clausesByLength.size();i++) {
            //std::cerr << "(";
            addAfterItIsClearThatTheNewClauseCannotBeSubset(clause,clausesByLength[i]);
            //std::cerr << ")";
        }
        if (clausesByLength.size()<=clause.size()) clausesByLength.resize(clause.size()+1);
        clausesByLength[clause.size()].push_back(clause);

    }

    void add(std::vector<int> &clause) {
        // Returns if something has been added
        //std::cerr << ".";
        std::sort(clause.begin(),clause.end());
        for (unsigned int i=0;i<std::min(clause.size(),clausesByLength.size());i++) {
            //std::cerr << "[";
            if (checkSubsumption(clause,clausesByLength[i])) {
                //std::cerr << "CONTAINED!\n";
                return;
            }
            //std::cerr << "]";
        }
        if (clausesByLength.size()>clause.size()) {
            //if (std::find(clausesByLength[clause.size()].begin(), clausesByLength[clause.size()].end(), clause)!=clausesByLength[clause.size()].end()) return;
            if (findClause(clausesByLength[clause.size()],clause)) {
                //std::cerr << "CONTAINED!\n";
                return;
            }
        }
        for (unsigned int i=clause.size()+1;i<clausesByLength.size();i++) {
            //std::cerr << "(";
            addAfterItIsClearThatTheNewClauseCannotBeSubset(clause,clausesByLength[i]);
            //std::cerr << ")";
        }
        if (clausesByLength.size()<=clause.size()) clausesByLength.resize(clause.size()+1);
        clausesByLength[clause.size()].push_back(clause);
    }


    std::vector<std::list<std::vector<int> > > const &getClauses() const { return clausesByLength; }
};



/***
 * The version of the encoder that generated actual minimal (smallest size) sets of clauses
 */

template<class SolverType> class EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT : public EncoderContext {
private:
    unsigned int approxMaxSizeUncoveredCubes;
    unsigned int approxMaxSizeUncoveredImplicants;
    void selectAndPrintDesiredSubsetOfThePossibleClauses(std::vector<std::vector<int> > &newClauses, BF constraints);

    std::vector<BF> allLiteralsOfBaseClausesViolatedButOneOrViolated;

    // Internal functions
    void removePartialValuationsFromBFForWhichSomeClauseFires(BF &bf, const std::vector<std::pair<int,std::vector<int> > > &namedClauses, const std::vector<int> &clause);

    void recursePartialValuationCorrect(const std::vector<std::pair<int,std::vector<int> > > &remainingClauses, AntichainOptimizingClauseSet &targetClauses);
    void recursePartialValuationOptimallyConflicting(int nofVarsInSATInstanceToBeEncoded,const std::vector<std::pair<int,std::vector<int> > > &namedClauses,AntichainOptimizingClauseSet &maxsatClauses,BF remainingValuations,std::vector<int> const &currentPartialValuation,int &nextFreeVariable);
    void recursePartialValuationOptimallyPropagating(int nofVarsInSATInstanceToBeEncoded,const std::vector<std::pair<int,std::vector<int> > > &namedClauses,AntichainOptimizingClauseSet &maxsatClauses,BF remainingValuations,int &nextFreeVariable);

public:
    EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT(unsigned int _approxMaxSizeUncoveredCubes, unsigned int _approxMaxSizeUncoveredImplicants) : approxMaxSizeUncoveredCubes(_approxMaxSizeUncoveredCubes), approxMaxSizeUncoveredImplicants(_approxMaxSizeUncoveredImplicants) {}
    void encode(BF constraints, std::vector<std::vector<int> > const &prefilledClauses, unsigned int nofPropagatingVars);
};

#include <set>
#include <map>
#include <cassert>
#include <algorithm>
#include <boost/graph/strong_components.hpp>
#include <boost/graph/adjacency_list.hpp>
#include "cuddInt.h"

//#define PICOSAT_ADD(context,literal) { picosat_add(context,literal); if (literal==0) std::cerr << "0\n"; else std::cerr << literal << " "; }
#ifdef PICOSAT_ADD
#undef PICOSAT_ADD
#endif
#define PICOSAT_ADD(context,literal) { context.add(literal); }


/**
 * @brief The
 * @param constraints what is to be encoded
 * @param prefilledClauses which clauses should be extended
 */
template<class SolverType> void EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<SolverType>::encode(BF constraints, std::vector<std::vector<int> > const &prefilledClauses, unsigned int nofPropagatingVars) {

    // Allocate PicoSAT copy
    SolverType picosat;
    int nofVarsUsedSoFar = 0;

    // Allocate variables for the literals
    int literalVars[variables.size()][2];
    //std::cerr << "c Literal Clauses\n";
    for (unsigned int i=0;i<variables.size();i++) {
        for (unsigned int j=0;j<2;j++) {
            literalVars[i][j] = ++nofVarsUsedSoFar;
            picosat.markVariableAsIncremental(literalVars[i][j]);
            PICOSAT_ADD(picosat,-1*literalVars[i][j]);
        }
        PICOSAT_ADD(picosat,0);
    }

    // Allocate variables for the ladder encoding
    // First index: Variables looked at so far
    // Second index: Variables used so far
    int ladderVars[variables.size()][variables.size()];
    for (unsigned int i=0;i<variables.size();i++) {
        for (unsigned int j=0;j<variables.size();j++) {
            ladderVars[i][j] = ++nofVarsUsedSoFar;
        }
    }
    for (unsigned int j=0;j<variables.size();j++) {
        picosat.markVariableAsIncremental(ladderVars[variables.size()-1][j]);
    }

    // Lowest line in the counting
    //std::cerr << "c Lowest counting lines\n";
    for (unsigned int i=0;i<variables.size();i++) {
        PICOSAT_ADD(picosat,ladderVars[i][0]);
        PICOSAT_ADD(picosat,-1*literalVars[i][0]);
        PICOSAT_ADD(picosat,0);
        PICOSAT_ADD(picosat,ladderVars[i][0]);
        PICOSAT_ADD(picosat,-1*literalVars[i][1]);
        PICOSAT_ADD(picosat,0);
    }

    // Forward propagation
    //std::cerr << "c Forward Propagation\n";
    for (unsigned int i=0;i<variables.size()-1;i++) {
        for (unsigned int j=0;j<variables.size();j++) {
            PICOSAT_ADD(picosat,-1*ladderVars[i][j]);
            PICOSAT_ADD(picosat,ladderVars[i+1][j]);
            PICOSAT_ADD(picosat,0);
        }
    }

    // General case
    //std::cerr << "c Ladder general case\n";
    for (unsigned int i=1;i<variables.size();i++) {
        for (unsigned int j=1;j<variables.size();j++) {
            PICOSAT_ADD(picosat,-1*ladderVars[i-1][j-1]);
            PICOSAT_ADD(picosat,-1*literalVars[i][0]);
            PICOSAT_ADD(picosat,ladderVars[i][j]);
            PICOSAT_ADD(picosat,0);
            PICOSAT_ADD(picosat,-1*ladderVars[i-1][j-1]);
            PICOSAT_ADD(picosat,-1*literalVars[i][1]);
            PICOSAT_ADD(picosat,ladderVars[i][j]);
            PICOSAT_ADD(picosat,0);
        }
    }

    // BDD encoding -- Allocate mapping
    std::set<DdNode *> todoList;
    std::map<DdNode *, int> bddNodeToSATVarMapping;
    todoList.insert(constraints.getCuddNode());
    while (todoList.size()>0) {
        DdNode *current = *(todoList.begin());
        todoList.erase(todoList.begin());
        assert(bddNodeToSATVarMapping.count(current)==0);
        bddNodeToSATVarMapping[current] = ++nofVarsUsedSoFar;
        if (!(Cudd_IsConstant(current))) {
            if (Cudd_IsComplement(current)) {
                DdNode *succ1 = Cudd_Not(cuddE(Cudd_Regular(current)));
                DdNode *succ2 = Cudd_Not(cuddT(Cudd_Regular(current)));
                if (bddNodeToSATVarMapping.count(succ1)==0) todoList.insert(succ1);
                if (bddNodeToSATVarMapping.count(succ2)==0) todoList.insert(succ2);
            } else {
                DdNode *succ1 = cuddE(current);
                DdNode *succ2 = cuddT(current);
                if (bddNodeToSATVarMapping.count(succ1)==0) todoList.insert(succ1);
                if (bddNodeToSATVarMapping.count(succ2)==0) todoList.insert(succ2);
            }
        }
    }

    // BDD encoding -- encode the stuff
    //std::cerr << "c BDD encoding\n";
    PICOSAT_ADD(picosat,bddNodeToSATVarMapping[constraints.getCuddNode()]);
    PICOSAT_ADD(picosat,0);

    for (auto it = bddNodeToSATVarMapping.begin();it!=bddNodeToSATVarMapping.end();it++) {
        DdNode *current = it->first;

        if (!(Cudd_IsConstant(current))) {
            if (Cudd_IsComplement(current)) {
                DdNode *succ1 = Cudd_Not(cuddE(Cudd_Regular(current)));
                DdNode *succ2 = Cudd_Not(cuddT(Cudd_Regular(current)));
                unsigned int thisLevel = Cudd_NodeReadIndex(Cudd_Regular(current));
                assert(variables[Cudd_NodeReadIndex(Cudd_Regular(current))].readNodeIndex()==Cudd_NodeReadIndex(Cudd_Regular(current)));

                PICOSAT_ADD(picosat,-1*bddNodeToSATVarMapping[current]);
                PICOSAT_ADD(picosat,literalVars[thisLevel][0]);
                PICOSAT_ADD(picosat,bddNodeToSATVarMapping[succ1]);
                PICOSAT_ADD(picosat,0);

                PICOSAT_ADD(picosat,-1*bddNodeToSATVarMapping[current]);
                PICOSAT_ADD(picosat,literalVars[thisLevel][1]);
                PICOSAT_ADD(picosat,bddNodeToSATVarMapping[succ2]);
                PICOSAT_ADD(picosat,0);

            } else {
                DdNode *succ1 = cuddE(current);
                DdNode *succ2 = cuddT(current);
                unsigned int thisLevel = Cudd_NodeReadIndex(Cudd_Regular(current));
                assert(variables[Cudd_NodeReadIndex(Cudd_Regular(current))].readNodeIndex()==Cudd_NodeReadIndex(Cudd_Regular(current)));

                PICOSAT_ADD(picosat,-1*bddNodeToSATVarMapping[current]);
                PICOSAT_ADD(picosat,literalVars[thisLevel][0]);
                PICOSAT_ADD(picosat,bddNodeToSATVarMapping[succ1]);
                PICOSAT_ADD(picosat,0);

                PICOSAT_ADD(picosat,-1*bddNodeToSATVarMapping[current]);
                PICOSAT_ADD(picosat,literalVars[thisLevel][1]);
                PICOSAT_ADD(picosat,bddNodeToSATVarMapping[succ2]);
                PICOSAT_ADD(picosat,0);
            }
        } else {
            if (current==Cudd_ReadOne(mgr.getMgr())) {
                // True. Must not be reached!
                PICOSAT_ADD(picosat,-1*bddNodeToSATVarMapping[current]);
                PICOSAT_ADD(picosat,0);
            } else {
                PICOSAT_ADD(picosat,bddNodeToSATVarMapping[current]);
                PICOSAT_ADD(picosat,0);
            }
        }
    }

    // Finally, we need to guess a partial assignment
    // that does not violate any of the old rules, or gives rise to unit propagation to any of them.
    int exampleAssignmentWithoutAnyUnitPropagation[variables.size()][2];
    for (unsigned int i=0;i<variables.size();i++) {
        exampleAssignmentWithoutAnyUnitPropagation[i][0] = ++nofVarsUsedSoFar;
        exampleAssignmentWithoutAnyUnitPropagation[i][1] = ++nofVarsUsedSoFar;
        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,0);
        picosat.markVariableAsIncremental(exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        picosat.markVariableAsIncremental(exampleAssignmentWithoutAnyUnitPropagation[i][1]);
    }

    //std::cerr << "c The first example assignment variable is " << exampleAssignmentWithoutAnyUnitPropagation[0][0] << "\n";
    for (unsigned int i=0;i<variables.size();i++) {
        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,-1*literalVars[i][0]);
        PICOSAT_ADD(picosat,0);
        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,-1*literalVars[i][1]);
        PICOSAT_ADD(picosat,0);
    }
    //std::cerr.flush();


    // std::cerr << "c The new clause must give rise to unit propagation to the example assignment \n";
    // The variables encode whether the not-yet-satisfied literal in the clause has
    // already been seen.
    int checkUnitPropagationOnNewClauseLadderVariables[nofPropagatingVars+1];
    for (unsigned int i=0;i<=nofPropagatingVars;i++) {
        checkUnitPropagationOnNewClauseLadderVariables[i] = ++nofVarsUsedSoFar;
    }

    // Initially, the value of the variables is 0
    PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[0]);
    PICOSAT_ADD(picosat,0);
    for (unsigned int i=0;i<nofPropagatingVars;i++) {

        // Zero needs to be propagated: Match 0
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,-1*literalVars[i][0]);
        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[i+1]);
        PICOSAT_ADD(picosat,0);

        // Zero needs to be propagateed: Match 1
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,-1*literalVars[i][1]);
        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[i+1]);
        PICOSAT_ADD(picosat,0);

        // Zero needs to be propagateed: No match at all
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,literalVars[i][0]);
        PICOSAT_ADD(picosat,literalVars[i][1]);
        PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[i+1]);
        PICOSAT_ADD(picosat,0);

        // Switch zero to one: Case 1
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,-1*literalVars[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i+1]);
        PICOSAT_ADD(picosat,0);

        // Switch zero to one: Case 2
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,-1*literalVars[i][1]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i+1]);
        PICOSAT_ADD(picosat,0);

        // No missing value if we already found one: case 1
        PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,-1*literalVars[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,0);

        // No missing value if we already found one: case 2
        PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,-1*literalVars[i][1]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,0);

        // Push right
        PICOSAT_ADD(picosat,-1*checkUnitPropagationOnNewClauseLadderVariables[i]);
        PICOSAT_ADD(picosat,checkUnitPropagationOnNewClauseLadderVariables[i+1]);
        PICOSAT_ADD(picosat,0);
    }

    // At the end, there must be one literal not yet satisfied
    PICOSAT_ADD(picosat,1*checkUnitPropagationOnNewClauseLadderVariables[nofPropagatingVars]);
    PICOSAT_ADD(picosat,0);

    // Finally, the valuation for the non-propagating variables must already be set in the example
    // assignment *or* they do not occur in the new clause.
    for (unsigned int i=nofPropagatingVars;i<variables.size();i++) {
        PICOSAT_ADD(picosat,-1*literalVars[i][0]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][1]);
        PICOSAT_ADD(picosat,0);
        PICOSAT_ADD(picosat,-1*literalVars[i][1]);
        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[i][0]);
        PICOSAT_ADD(picosat,0);
    }

    // Pre-initialize clauses
    clauses = prefilledClauses;

    // The found assignment should be covered by unit propagation
    // Add new clauses to the SAT instance to rule out finding new example partial assignments
    // that lead to unit propagation with this newly found clause
    for (auto newClause : prefilledClauses) {
        for (unsigned int i=0;i<newClause.size();i++) {

            // Either the clause is already satisfied...
            for (auto it : newClause) {
                if (it<0) {
                    PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[-1*it-1][0]);
                } else {
                    PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[it-1][1]);
                }
            }

            // ...or every literal except for the ith one is not already falsified
            for (unsigned int j=0;j<newClause.size();j++) {
                if (i!=j) {
                    if (newClause[j]<0) {
                        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[-1*newClause[j]-1][1]);
                    } else {
                        PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[newClause[j]-1][0]);
                    }
                }
            }

            // ...or unit propagation has already been performed!
            if (newClause[i]<0) {
                PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[-1*newClause[i]-1][0]);
            } else {
                PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[newClause[i]-1][1]);
            }

            PICOSAT_ADD(picosat,0);
        }
    }

    // std::cerr << "Done with the search instance.\n";


    // Iterate over the possible clause lengths
    std::vector<std::vector<int> > clausesThisLevel;
    for (unsigned int maxLenClauses=0;maxLenClauses<=variables.size();maxLenClauses++) {

        // Repeatedly class PICOSAT to find all clauses
        bool noMoreClauses = false;

        while (!noMoreClauses) {

            // Limit the size - since assumed literals become invalid after
            // every unsatisfiability result *and* after adding a new clause,
            // we need to assume the number-limit literal every time we
            // call picosat
            if (maxLenClauses<variables.size()) {
                //std::cerr << "Assuming For Clause Generation: " << -1*ladderVars[variables.size()-1][maxLenClauses] << std::endl;
                picosat.assume(-1*ladderVars[variables.size()-1][maxLenClauses]);
            }

            bool picosat_result = picosat.solve();
            if (picosat_result) {

                // Get the new clause
                std::vector<int> newClause;
                for (unsigned int i=0;i<variables.size();i++) {
                    if (picosat.getVariableValue(literalVars[i][0])) {
                        newClause.push_back(-1*(i+1));
                    } else if (picosat.getVariableValue(literalVars[i][1])) {
                        newClause.push_back(i+1);
                    }
                }
                clausesThisLevel.push_back(newClause);

                // The new clause should not already be satisfied
                for (auto it : newClause) {
                    if (it<0) {
                        PICOSAT_ADD(picosat,-1*literalVars[-1*it-1][0]);
                    } else {
                        PICOSAT_ADD(picosat,-1*literalVars[it-1][1]);
                    }
                }

                PICOSAT_ADD(picosat,0);

            } else {
                // Ok, we are done here.
                noMoreClauses = true;
            }
        }

        // Move the new clauses to the standard clauses folder and filter out the unneeded clauses
        //std::cerr << "Start Subset Comp\n";
        /*for (auto it : clausesThisLevel) {
            clauses.push_back(it);
        }*/
        //std::cerr << "End Subset Comp\n";

        // The example assignment does not give rise to unit propagation to any of the old clauses
        //for (auto newClause : clausesThisLevel) {

            /*// Add new clauses to the SAT instance to rule out finding new example partial assignments
            // that lead to unit propagation with this newly found clause
            for (unsigned int i=0;i<newClause.size();i++) {

                // Either the clause is already satisfied...
                for (auto it : newClause) {
                    if (it<0) {
                        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[-1*it-1][0]);
                    } else {
                        PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[it-1][1]);
                    }
                }

                // ...or every literal except for the ith one is not already falsified
                for (unsigned int j=0;j<newClause.size();j++) {
                    if (i!=j) {
                        if (newClause[j]<0) {
                            PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[-1*newClause[j]-1][1]);
                        } else {
                            PICOSAT_ADD(picosat,-1*exampleAssignmentWithoutAnyUnitPropagation[newClause[j]-1][0]);
                        }
                    }
                }

                // ...or unit propagation has already been performed!
                if (newClause[i]<0) {
                    PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[-1*newClause[i]-1][0]);
                } else {
                    PICOSAT_ADD(picosat,exampleAssignmentWithoutAnyUnitPropagation[newClause[i]-1][1]);
                }

                PICOSAT_ADD(picosat,0);
            }*/

        //}

    }

    std::cerr << "c Number of clauses to select a good subset from: " << clausesThisLevel.size() << std::endl;
    selectAndPrintDesiredSubsetOfThePossibleClauses(clausesThisLevel,constraints);
}



/**
 * Recursive worker function for ensuring that complete assignments that are not allowed by the encoding have some clause in the encoded SAT instance
 * that rule them out.
 */
template<class SolverType> void EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<SolverType>::recursePartialValuationCorrect(const std::vector<std::pair<int,std::vector<int> > > &remainingClauses, AntichainOptimizingClauseSet &targetClauses) {

    // Satisfying assingment..
    if (remainingClauses.size()==0) return;

    int chosenVariable = 0;

    auto it = remainingClauses.begin();
    while (it!=remainingClauses.end()) {
        for (auto it2 : it->second) {
            chosenVariable = std::abs(it2);
        }
        it++;
    }
    //std::cerr << "Chosen var: " << chosenVariable << std::endl;

    // Induction base case
    if (chosenVariable==0) {
        // Done!
        std::vector<int> clause;
        for (const std::pair<int,std::vector<int> > &it : remainingClauses) {
            int tmp = it.first + 1;
            clause.push_back(tmp);
        }
        targetClauses.add(clause);
        return;
    }

    // The two inductive cases
    for (int value : {-1,1}) {
        std::vector<std::pair<int,std::vector<int> > > newRemainingClauses;
        newRemainingClauses.reserve(remainingClauses.size());
        for (const std::pair<int,std::vector<int> > &originalClause : remainingClauses) {
            bool satisfied = false;
            std::vector<int> remainingLits;
            remainingLits.reserve(originalClause.second.size());
            for (int lit : originalClause.second) {
                satisfied |= (lit==value*chosenVariable);
                int lit2 = lit;
                if (lit!=-1*value*chosenVariable) remainingLits.push_back(lit2);
            }
            if (!satisfied) newRemainingClauses.push_back(std::pair<int,std::vector<int> >(originalClause.first,remainingLits));
        }
        recursePartialValuationCorrect(newRemainingClauses, targetClauses);
    }
}


template<class SolverType> void EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<SolverType>::removePartialValuationsFromBFForWhichSomeClauseFires(BF &bf, const std::vector<std::pair<int,std::vector<int> > > &namedClauses, const std::vector<int> &existingClause) {

    //std::vector<BF> variablesSecondCopy = getOnlyTheSecondCopyVariables();
    BF valuationsTriggeringAllSATClauses = mgr.constantTrue();

    for (auto lit : existingClause) {
        //std::cerr << " " << lit;
        // So far, we assume that all maxsat clauses only have positive polarity because a higher number of
        // SAT clauses should always lead to easier satisfiability
        assert(lit>0);
        assert(namedClauses[lit-1].first == lit-1); // Order must still be ok

        valuationsTriggeringAllSATClauses &= allLiteralsOfBaseClausesViolatedButOneOrViolated[lit-1];

        //valuationsTriggeringAllSATClauses &= (allViolated | allViolatedButOne);
    }
    bf &= !valuationsTriggeringAllSATClauses;
}


/**
 * @brief Recursive worker function for ensuring that the final result is approximately optimally conflicting. We use the definition here that
 *        if <= than approxMaxSizeUncoveredImplicants many variables do not have values and the partial valuation is already in violation of the
 *        constraint, then some clause needs to "fire".
 * @param namedClauses The clauses to select from for the SAT encoding that we search for
 * @param maxsatClauses The clauses already in the MAXSAT instance
 * @param remainingValuations The Boolean formula to be encoded restricted to the current partial valuation
 * @param currentPartialValuation The current partial valuation using -1 and 1 for selection and
 * @param nextFreeVariable The next free variable in the MAXSAT instance
 */
template<class SolverType> void EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<SolverType>::recursePartialValuationOptimallyConflicting(int nofVarsInSATInstanceToBeEncoded, const std::vector<std::pair<int,std::vector<int> > > &namedClauses,AntichainOptimizingClauseSet &maxsatClauses, BF remainingValuations, std::vector<int> const &currentPartialValuation,int &nextFreeVariable) {

    // Build BDD representing the partial valuations that need to trigger unit propagation (or conflicts)
    std::vector<BF> variablesSecondCopy = getOnlyTheSecondCopyVariables();
    BFBddVarCube allVarCube = mgr.computeCube(variables);

    std::vector<std::vector<BF> > definedValuesSoFar;
    definedValuesSoFar.push_back({!remainingValuations});
    for (unsigned int varsSoFar = 0;varsSoFar < variablesSecondCopy.size();varsSoFar++) {
        std::vector<BF> nextLevel;
        for (unsigned int i=0;i<definedValuesSoFar.back().size();i++) {
            BF these = definedValuesSoFar.back()[i].UnivAbstractSingleVar(getVariableBF(varsSoFar)) & !(variablesSecondCopy[varsSoFar]);
            if (i>0) these |= definedValuesSoFar.back()[i-1] & (variablesSecondCopy[varsSoFar]);
            nextLevel.push_back(these);
        }
        nextLevel.push_back(definedValuesSoFar.back().back() & (variablesSecondCopy[varsSoFar]));
        definedValuesSoFar.push_back(nextLevel);
    }
    BF cases = mgr.constantFalse();
    for (int i=std::max(2,static_cast<int>(variablesSecondCopy.size()-approxMaxSizeUncoveredImplicants));i<=static_cast<int>(variablesSecondCopy.size());i++) {
        cases |= definedValuesSoFar.back()[i];
    }
    remainingValuations = cases;
    std::cerr << "RemainingCases found!\n";

    // BF_newDumpDot(*this,cases ,NULL,"/tmp/cases.dot");

    // Remove the valuations that are definitely covered by the clauses that we already have in the MAXSAT instance
    for (auto &existingClauseSet : maxsatClauses.getClauses()) {
        for (auto &existingClause : existingClauseSet) {
            removePartialValuationsFromBFForWhichSomeClauseFires(remainingValuations,namedClauses,existingClause);
        }
    }

    std::cerr << "Cover remaining valuations:" << remainingValuations.isFalse() << "\n";

    DdNode *oneDdNode = DD_ONE(mgr.getMgr());

    // Now go through "remainingValuations" and find new valuations to be taken care of
    while (!(remainingValuations.isFalse())) {

        // Determinize
        /*BF thisCase = remainingValuations;
        bool careVars[variablesSecondCopy.size()];
        for (unsigned int i=0;i<variablesSecondCopy.size();i++) {
            BF test = thisCase & variablesSecondCopy[i];
            if (test.isFalse()) {
                careVars[i] = false;
                thisCase = thisCase & !(variablesSecondCopy[i]);
            } else {
                careVars[i] = true;
                thisCase = test;
            }
        }

        //std::cerr << "{case}";

        bool assignmentVars[variablesSecondCopy.size()];
        for (unsigned int i=0;i<variablesSecondCopy.size();i++) {
            if (careVars[i]) {
                BF test = thisCase & getVariableBF(i);
                if (test.isFalse()) {
                    assignmentVars[i] = false;
                    thisCase = thisCase & !getVariableBF(i);
                } else {
                    assignmentVars[i] = true;
                    thisCase = test;
                }
            }
        }*/

        // Moving to a BFless analysis approach
        // Assumes that the variables are allocated in "normal copy first, then second copy" order.
        bool allVars[variablesSecondCopy.size()*2];
        memset(allVars,0,sizeof(bool)*variablesSecondCopy.size()*2);
        DdNode *currentNode = remainingValuations.getCuddNode();
        while (Cudd_Regular(currentNode)->index != CUDD_CONST_INDEX) {
            if ((size_t)currentNode & 1) {
                // Negated node
                currentNode = Cudd_Regular(currentNode);
                DdNode *e = cuddE(currentNode);
                if ((size_t)e & 1) {
                    // Doubly-Negated
                    e = Cudd_Regular(e);
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e==oneDdNode) {
                            // Can stay false
                            currentNode = e;
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = Cudd_Not(cuddT(currentNode));
                        }
                    } else {
                        currentNode = e;
                    }
                } else {
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e!=oneDdNode) {
                            // Can stay false
                            currentNode = Cudd_Not(e);
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = Cudd_Not(cuddT(currentNode));
                        }
                    } else {
                        currentNode = Cudd_Not(e);
                    }
                }
            } else {
                // Non-Negated node
                DdNode *e = cuddE(currentNode);
                if ((size_t)e & 1) {
                    // Doubly-Negated
                    e = Cudd_Regular(e);
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e!=oneDdNode) {
                            // Can stay false
                            currentNode = e;
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = cuddT(currentNode);
                        }
                    } else {
                        currentNode = Cudd_Not(e);
                    }
                } else {
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e==oneDdNode) {
                            // Can stay false
                            currentNode = e;
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = cuddT(currentNode);
                        }
                    } else {
                        currentNode = e;
                    }
                }
            }
        }
        //std::cerr << ".";

        bool *assignmentVars = allVars;
        bool *careVars= &(allVars[variablesSecondCopy.size()]);

        //remainingValuations &= !thisCase;

        // Find which clauses do the trick for this assignment
        std::vector<int> newMAXSATClause;
        //std::cerr << "Processing case";
        //for (int i=0;i<static_cast<int>(variablesSecondCopy.size());i++) {
        //    if (careVars[i]) std::cerr << " " << (assignmentVars[i]?(i+1):(-1*(i+1)));
        //}
        //std::cerr << std::endl;

        //BF_newDumpDot(*this,thisCase,NULL,"/tmp/thisCase.dot");
        //throw 3;
        for (const std::pair<int,std::vector<int> > &satClause : namedClauses) {
            //std::cerr << ".";
            bool isSAT = false;
            bool doesNotFire = false;
            int remainingLit = 0;
            for (auto lit : satClause.second) {
                if (careVars[std::abs(lit)-1]) {
                    if (assignmentVars[std::abs(lit)-1]==(lit>0)) isSAT = true;
                    else {
                        // Literal does not hold on the partial valuation
                    }
                } else {
                    if (remainingLit==0) {
                        remainingLit = lit;
                    } else {
                        doesNotFire = true;
                    }
                }
            }
            if ( (!isSAT) && (!doesNotFire)) {
                // We have a winner!
                newMAXSATClause.push_back(satClause.first+1);
                //std::cerr << "(" << satClause.first << ")";
            }
        }
        //std::cerr << std::endl;
        //std::cerr << "/clause ";
        //for (auto it : newMAXSATClause) std::cerr << " " << it;
        maxsatClauses.addWhileKnowingThatTheNewClauseIsNotSubsumed(newMAXSATClause);
        removePartialValuationsFromBFForWhichSomeClauseFires(remainingValuations,namedClauses,newMAXSATClause);
        //if (!((thisCase & remainingValuations).isFalse())) throw 13;
        //std::cerr << " --> " << remainingValuations.getNofSatisfyingAssignments(allVarCube) << "\n";
        //std::cerr << std::endl;
    }
}

/**
 * Add the clauses that enforce approximate optimal propagation
 */
template<class SolverType> void EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<SolverType>::recursePartialValuationOptimallyPropagating(int nofVarsInSATInstanceToBeEncoded, const std::vector<std::pair<int,std::vector<int> > > &namedClauses,AntichainOptimizingClauseSet &maxsatClauses, BF remainingValuations, int &nextFreeVariable) {

    std::vector<BF> variablesSecondCopy = getOnlyTheSecondCopyVariables();

    // Find the partial valuations that give rise to unit propagation (and count how many variables were implied
    // by them)
    std::vector<std::vector<BF> > propagatedValuesSoFar;
    propagatedValuesSoFar.push_back({mgr.constantTrue()});
    for (unsigned int varsSoFar = 0;varsSoFar < variablesSecondCopy.size();varsSoFar++) {

        BF allAssignmentsThatImplyAnyLit = mgr.constantFalse();

        for (unsigned int sign = 0;sign<2;sign++) {
            BF allAssignmentsThatImplyThisLit =
                    sign?((remainingValuations & getVariableBF(varsSoFar)).ExistAbstractSingleVar(getVariableBF(varsSoFar)) & !((remainingValuations & !getVariableBF(varsSoFar)).ExistAbstractSingleVar(getVariableBF(varsSoFar))))
                                          :((remainingValuations & !getVariableBF(varsSoFar)).ExistAbstractSingleVar(getVariableBF(varsSoFar)) & !((remainingValuations & getVariableBF(varsSoFar)).ExistAbstractSingleVar(getVariableBF(varsSoFar))));

            allAssignmentsThatImplyThisLit |= !(remainingValuations.ExistAbstractSingleVar(getVariableBF(varsSoFar)));

            /*if (sign==0) {
                std::ostringstream filename; filename << "/tmp/allAssignmentsThatImplyThisLit" << varsSoFar << ".dot";
                BF_newDumpDot(*this,allAssignmentsThatImplyThisLit,NULL,filename.str().c_str());
            }*/

            // extend "allAssignmentsThatImplyLit" to partial valuations
            for (unsigned int i=0;i<variablesSecondCopy.size();i++) {
                if (i!=varsSoFar) {
                    allAssignmentsThatImplyThisLit = allAssignmentsThatImplyThisLit & variablesSecondCopy[i] | allAssignmentsThatImplyThisLit.UnivAbstractSingleVar(getVariableBF(i)) & !variablesSecondCopy[i];
                }
            }

            allAssignmentsThatImplyAnyLit |= allAssignmentsThatImplyThisLit;
        }

        std::ostringstream filename; filename << "/tmp/allAssignmentsThatImplyLit" << varsSoFar << ".dot";
        // BF_newDumpDot(*this,allAssignmentsThatImplyAnyLit,NULL,filename.str().c_str());

        std::vector<BF> nextLevel;
        for (unsigned int i=0;i<propagatedValuesSoFar.back().size();i++) {
            BF these = propagatedValuesSoFar.back()[i];
            if (i>0) these |= propagatedValuesSoFar.back()[i-1] & allAssignmentsThatImplyAnyLit & !variablesSecondCopy[varsSoFar];
            nextLevel.push_back(these);
        }
        nextLevel.push_back(propagatedValuesSoFar.back().back() & allAssignmentsThatImplyAnyLit & !variablesSecondCopy[varsSoFar]);
        propagatedValuesSoFar.push_back(nextLevel);
    }

    BF cases = mgr.constantFalse();
    for (unsigned int i=approxMaxSizeUncoveredCubes;i<propagatedValuesSoFar.back().size();i++) {
        cases |= propagatedValuesSoFar.back()[i];
    }
    cases &= remainingValuations;
    //BF_newDumpDot(*this,cases,NULL,"/tmp/allCases.dot");

    if (approxMaxSizeUncoveredCubes<1) throw "Error: The cube size must be at least 1 for it to make sense.";

    // TODO: Refactor so that there is no code duplication below with the optimally conflicting case.

    // Remove the valuations that are definitely covered by the clauses that we already have in the MAXSAT instance
    for (auto &existingClauseSet : maxsatClauses.getClauses()) {
        for (auto &existingClause : existingClauseSet) {
            removePartialValuationsFromBFForWhichSomeClauseFires(cases,namedClauses,existingClause);
        }
    }

    DdNode *oneDdNode = DD_ONE(mgr.getMgr());



    // Now go through cases and find new valuations to be taken care of
    while (!(cases.isFalse())) {

        // Determinize
        /*BF thisCase = cases;
        bool careVars[variablesSecondCopy.size()];
        for (unsigned int i=0;i<variablesSecondCopy.size();i++) {
            BF test = thisCase & variablesSecondCopy[i];
            if (test.isFalse()) {
                careVars[i] = false;
                thisCase = thisCase & !(variablesSecondCopy[i]);
            } else {
                careVars[i] = true;
                thisCase = test;
            }
        }

        bool assignmentVars[variablesSecondCopy.size()];
        for (unsigned int i=0;i<variablesSecondCopy.size();i++) {
            if (careVars[i]) {
                BF test = thisCase & getVariableBF(i);
                if (test.isFalse()) {
                    assignmentVars[i] = false;
                    thisCase = thisCase & !getVariableBF(i);
                } else {
                    assignmentVars[i] = true;
                    thisCase = test;
                }
            }
        }

        cases &= !thisCase;*/

        // Moving to a BFless analysis approach
        // Assumes that the variables are allocated in "normal copy first, then second copy" order.
        bool allVars[variablesSecondCopy.size()*2];
        memset(allVars,0,sizeof(bool)*variablesSecondCopy.size()*2);
        DdNode *currentNode = cases.getCuddNode();
        while (Cudd_Regular(currentNode)->index != CUDD_CONST_INDEX) {
            if ((size_t)currentNode & 1) {
                // Negated node
                currentNode = Cudd_Regular(currentNode);
                DdNode *e = cuddE(currentNode);
                if ((size_t)e & 1) {
                    // Doubly-Negated
                    e = Cudd_Regular(e);
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e==oneDdNode) {
                            // Can stay false
                            currentNode = e;
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = Cudd_Not(cuddT(currentNode));
                        }
                    } else {
                        currentNode = e;
                    }
                } else {
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e!=oneDdNode) {
                            // Can stay false
                            currentNode = Cudd_Not(e);
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = Cudd_Not(cuddT(currentNode));
                        }
                    } else {
                        currentNode = Cudd_Not(e);
                    }
                }
            } else {
                // Non-Negated node
                DdNode *e = cuddE(currentNode);
                if ((size_t)e & 1) {
                    // Doubly-Negated
                    e = Cudd_Regular(e);
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e!=oneDdNode) {
                            // Can stay false
                            currentNode = e;
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = cuddT(currentNode);
                        }
                    } else {
                        currentNode = Cudd_Not(e);
                    }
                } else {
                    if (e->index == CUDD_CONST_INDEX) {
                        if (e==oneDdNode) {
                            // Can stay false
                            currentNode = e;
                        } else {
                            // We need a "TRUE" here
                            allVars[currentNode->index] = true;
                            currentNode = cuddT(currentNode);
                        }
                    } else {
                        currentNode = e;
                    }
                }
            }
        }
        //std::cerr << ".";

        bool *assignmentVars = allVars;
        bool *careVars= &(allVars[variablesSecondCopy.size()]);

        // Find which clauses do the trick for this assignment
        std::vector<int> newMAXSATClause;
        //std::cerr << "Processing case";
        //for (int i=0;i<variablesSecondCopy.size();i++) {
        //    if (careVars[i]) std::cerr << " " << (assignmentVars[i]?(i+1):(-1*(i+1)));
        //}

        //BF_newDumpDot(*this,thisCase,NULL,"/tmp/thisCase.dot");
        //throw 3;
        for (const std::pair<int,std::vector<int> > &satClause : namedClauses) {
            //std::cerr << ".";
            bool isSAT = false;
            bool doesNotFire = false;
            int remainingLit = 0;
            for (auto lit : satClause.second) {
                if (careVars[std::abs(lit)-1]) {
                    if (assignmentVars[std::abs(lit)-1]==(lit>0)) isSAT = true;
                    else {
                        // Literal does not hold on the partial valuation
                    }
                } else {
                    if (remainingLit==0) {
                        remainingLit = lit;
                    } else {
                        doesNotFire = true;
                    }
                }
            }
            if ( (!isSAT) && (!doesNotFire)) {
                // We have a winner!
                newMAXSATClause.push_back(satClause.first+1);
                //std::cerr << "(" << satClause.first << ")";
            }
        }
        //std::cerr << std::endl;
        maxsatClauses.addWhileKnowingThatTheNewClauseIsNotSubsumed(newMAXSATClause);
        removePartialValuationsFromBFForWhichSomeClauseFires(cases,namedClauses,newMAXSATClause);
    }


}

/**
 * Filter out clauses that are not stricly needed.
 */
template<class SolverType> void EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<SolverType>::selectAndPrintDesiredSubsetOfThePossibleClauses(std::vector<std::vector<int> > &originalClauses, BF constraints) {

    AntichainOptimizingClauseSet maxsatClauses;

    // Compute list of free variables in the original clause set
    int maxVarNum = 0;
    for (auto const &clause : originalClauses) {
        for (auto it : clause) {
            maxVarNum = std::max(it,maxVarNum);
        }
    }

    std::vector<std::vector<int> > sortedClauses;
    for (auto it : originalClauses) {
        sortedClauses.push_back(it);
        std::sort(sortedClauses.back().begin(),sortedClauses.back().end(), [](const int& a, const int &b) -> bool {
            assert(std::abs(a)!=std::abs(b));
            return std::abs(a) > std::abs(b);
        });
    }

    std::cerr << "Original clauses:\n";
    for (auto it : sortedClauses) {
        std::cerr << "-";
        for (auto it2 : it) {
            std::cerr << " " << it2;
        }
        std::cerr << std::endl;
    }

    // Check that free variable set is continuous
    /*for (unsigned int i=0;i<freeVariableSet.size();i++) {
        if (freeVariableSet.count(i+1)==0) throw "Error: Free variable set is not continuous";
    }*/

    std::vector<std::pair<int,std::vector<int> > > namedClauses;
    for (unsigned int i=0;i<sortedClauses.size();i++) namedClauses.push_back(std::pair<int,std::vector<int> >(i,sortedClauses[i]));


    // Fill "allLiteralsOfBaseClausesViolatedButOneOrViolated"
    std::vector<BF> variablesSecondCopy = getOnlyTheSecondCopyVariables();
    for (unsigned int i=0;i<namedClauses.size();i++) {
        BF allViolated = mgr.constantTrue();
        BF allViolatedButOne = mgr.constantFalse();
        for (auto satLit : namedClauses[i].second) {
            if (satLit<0) {
                allViolatedButOne = allViolatedButOne & getVariableBF(-1*satLit-1) & variablesSecondCopy[-1*satLit-1] | allViolated & !variablesSecondCopy[-1*satLit-1];
                allViolated &= variablesSecondCopy[-1*satLit-1] & getVariableBF(-1*satLit-1);
            } else {
                allViolatedButOne = allViolatedButOne & !getVariableBF(satLit-1) & variablesSecondCopy[satLit-1] | allViolated & !variablesSecondCopy[satLit-1];
                allViolated &= variablesSecondCopy[satLit-1] & !getVariableBF(satLit-1);
            }
        }
        allLiteralsOfBaseClausesViolatedButOneOrViolated.push_back(allViolated | allViolatedButOne);
    }


    // The encoding must be *correct*
    recursePartialValuationCorrect(namedClauses,maxsatClauses);
    std::cerr << "Correctness done!\n";

    // The encoding must be approximately optimally conflicting
    int nextFreeVariable = namedClauses.size()+1;
    recursePartialValuationOptimallyConflicting(maxVarNum,namedClauses,maxsatClauses,constraints,std::vector<int>(),nextFreeVariable);

    recursePartialValuationOptimallyPropagating(maxVarNum,namedClauses,maxsatClauses,constraints,nextFreeVariable);

    std::vector<std::list<std::vector<int> > > const &maxSATClauseList = maxsatClauses.getClauses();
    unsigned int allMaxSatClausesNumber = 0;
    for (auto &it : maxSATClauseList) allMaxSatClausesNumber += it.size();

    std::cerr << "RECURSE DONE!\n";

    // Ok, now generate a MAXSAT output file
    std::ostringstream outFilename;
    outFilename << std::string(std::tmpnam(nullptr)) << "-optic-" << getpid() << ".maxsat";
    std::ofstream maxSATFile(outFilename.str(),std::ofstream::out);
    maxSATFile << "p wcnf " << originalClauses.size() << " " << originalClauses.size()+allMaxSatClausesNumber << " 15\n";
    for (int i=0;i<static_cast<int>(originalClauses.size());i++) {
        maxSATFile << "1 " << -1*(i+1) << " 0\n";
    }
    for (auto &clausesBylength : maxSATClauseList) {
        for (auto &clause : clausesBylength) {
            maxSATFile << "15";
            for (auto lit : clause) maxSATFile << " " << lit;
            maxSATFile << " 0\n";
        }
    }
    maxSATFile.close();


    // Now generate a file name for the result
    std::ostringstream solverResultFilename;
    solverResultFilename << std::string(std::tmpnam(nullptr));

    // Run the solver
    const char *solverPathEnvironmentVar = std::getenv("MAXSATSOLVERPATH");
    if (solverPathEnvironmentVar==0) throw "Error: The environment variable 'MAXSATSOLVERPATH' is not set.";

    std::ostringstream commandToBeExecuted;
    commandToBeExecuted << solverPathEnvironmentVar << " " << outFilename.str() << " > " << solverResultFilename.str();

    int returnCode = std::system(commandToBeExecuted.str().c_str());
    if ((returnCode & 255) != 0) {
        std::cerr << "Warning: Execution of '" << commandToBeExecuted.str() << "' failed with return code " << returnCode << ".\n";
        //throw "Computation aborted";
    }

    /*if ((returnCode != 2560) && (returnCode != 0)) {
        throw "Optimum not found by the solver.";
    }*/

    // Read selected clauses
    std::ifstream inFile(solverResultFilename.str(),std::ifstream::in);
    std::string currentLineString;
    std::set<int> clauseSelection;
    while (std::getline(inFile,currentLineString)) {
        std::istringstream thisLine(currentLineString);
        std::string lineStart;
        thisLine >> lineStart;
        std::cerr << "O: " << lineStart << "-" << currentLineString << std::endl;
        if (lineStart=="v") {
            int lit;
            while (thisLine >> lit) {
                clauseSelection.insert(lit);
                std::cerr << "Clause push: " << lit << "out of" << originalClauses.size() << std::endl;
            }
        }
    }

    // Copy the selected clauses over
    for (unsigned int i=0;i<originalClauses.size();i++) {
        if (clauseSelection.count(i+1)>0) {
            std::cerr << "Pushing Ice: " << i << std::endl;
            clauses.push_back(originalClauses[i]);
        } else if (clauseSelection.count(-1-i)>0) {
            // Not selected
        } else {
            throw "Error: Did not fully understand the result of the MAXSAT solver.";
        }

    }
}






#endif
