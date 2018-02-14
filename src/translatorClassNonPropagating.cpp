#include "translatorClassNonPropagating.hpp"


/**
 * @brief Generates a classical non-optimally propagating CNF encoding
 * @param constraints The constraints
 */
void EncoderContextNonPropagating::encode(BF constraints, std::vector<std::vector<int> > const & prefilledClauses, unsigned int nofPropagatingVars) {

    clauses = prefilledClauses;
    assert(nofPropagatingVars <= variables.size());

    BF careSet = constraints;

    while (!(careSet.isTrue())) {

        // Find a non-sat assignment
        BF assignment = !careSet;
        std::vector<bool> startingAssignment;
        for (unsigned int i=0;i<nofPropagatingVars;i++) {
            BF thisTry = (assignment & variables[i]);
            if (thisTry.isFalse()) {
                assignment = (assignment & !variables[i]);
                startingAssignment.push_back(false);
            } else {
                assignment = thisTry;
                startingAssignment.push_back(true);
            }
        }

        // Now take the assignment and shorten it (greedily)
        std::vector<int> thisClause;
        BF clauseSoFar = mgr.constantTrue();
        for (unsigned int i=0;i<nofPropagatingVars;i++) {
            BF newClause = clauseSoFar;
            for (unsigned int j=i+1;j<nofPropagatingVars;j++) {
                if (startingAssignment[j]) {
                    newClause &= variables[j];
                } else {
                    newClause &= !variables[j];
                }
            }
            if ((newClause & constraints).isFalse()) {
                // No Literal to be added...
            } else {
                if (startingAssignment[i]) {
                    thisClause.push_back(-1*(i+1));
                    clauseSoFar &= variables[i];
                } else {
                    thisClause.push_back(i+1);
                    clauseSoFar &= !(variables[i]);
                }
            }
        }

        careSet |= clauseSoFar;

        clauses.push_back(thisClause);

    }
}
