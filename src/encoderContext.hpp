#ifndef __ENCODER_CONTEXT_HPP
#define __ENCODER_CONTEXT_HPP

#include "BF.h"
#include "bddDump.h"
#include <vector>
#include <set>

class EncoderContext : public VariableInfoContainer {
protected:
    BFManager mgr;
    std::vector<std::string> variableNames;
    std::vector<BF> variables;
    std::vector<BF> onlyTheSecondCopyVariables; // Used in some plugins for encoding don't care values

    // The result
    std::vector<std::vector<int> > clauses;

public:

    // Building a problem
    BF newVariable(std::string newName) {
        variableNames.push_back(newName);
        BF newVar = mgr.newVariable();
        variables.push_back(newVar);
        return newVar;
    }
    const BF &getVariable(unsigned int nr) const {
        return variables.at(nr);
    }
    const std::vector<std::vector<int> > &getClauses() const {
        return clauses;
    }
    const BFManager &getBFMgr() const { return mgr; }
    unsigned int getNofVariables() const { return variables.size(); }

    /**
     * @brief Some plugins need a second copy of the BDD variables in order to encode "Don't care value".
     * This function allocates them automatically and then returns them.
     * @return
     */
    std::vector<BF> getOnlyTheSecondCopyVariables() {
        // Allocate the second copy of the variables whenever needed
        while (onlyTheSecondCopyVariables.size()<(variables.size()+1)/2) {
            onlyTheSecondCopyVariables.push_back(newVariable(variableNames[onlyTheSecondCopyVariables.size()]+"-dontcare"));
        }
        return onlyTheSecondCopyVariables;
    }


    // The actual encoding part is basec on inheritance
    virtual void encode(BF constraints, std::vector<std::vector<int> > const &prefilledClauses, unsigned int nofPropagatingVars) = 0;

    // Encoding function that introduces additional variables to reduce the encoding size
    virtual void encodeWithAuxVars(BF constraints, unsigned int auxThreshold);


    // Other functionality that is common for all contexts
    void printEncoding();
    void testGeneratedClauses(BF constraints,unsigned int nofPropagatingVars);


    const BF &getVariableBF(std::string name) const {
        for (unsigned int i=0;i<variables.size();i++) {
            if (variableNames[i]==name) return variables[i];
        }
        throw "Error: Variable '"+name+"' was not declared.";
    }

    bool hasVariable(std::string name) {
        for (unsigned int i=0;i<variables.size();i++) {
            if (variableNames[i]==name) return true;
        }
        return false;
    }

    // Implementations for the VariableInfoContainer
    void getVariableTypes(std::vector<std::string> &types) const {
        types.push_back("all");
    }

    virtual void getVariableNumbersOfType(std::string type, std::vector<unsigned int> &nums) const {
        if (type!="all") throw "Illegal variable type";
        for (unsigned int i=0;i<variables.size();i++) nums.push_back(i);
    }

    BF getVariableBF(unsigned int number) const {
        return variables.at(number);
    }

    std::string getVariableName(unsigned int number) const {
        return variableNames.at(number);
    }

};



#endif
