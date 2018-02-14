#include <iostream>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <map>
#include "BF.h"
#include "bddDump.h"

std::string toString(int i) {
    std::ostringstream os;
    os << i;
    return os.str();
}

class TrivialVariableInfoContainer : public VariableInfoContainer {
private:
    BFManager &mgr;
    std::vector<std::string> &varNames;
    std::vector<BF> &vars;
public:
    TrivialVariableInfoContainer(BFManager &_mgr, std::vector<std::string> &_varNames, std::vector<BF> &_vars) : mgr(_mgr), varNames(_varNames), vars(_vars) {};
    void getVariableTypes(std::vector<std::string> &types) const { types.push_back("all"); }
    void getVariableNumbersOfType(std::string type, std::vector<unsigned int> &nums) const { for (unsigned int i=0;i<varNames.size();i++) nums.push_back(i); (void)type; }
    BF getVariableBF(unsigned int number) const { return vars.at(number); }
    std::string getVariableName(unsigned int number) const { return varNames.at(number); }
};

#ifdef NDEBUG
#define BF_NEWDUMPDOT(a,b,c,d) { (void)(a); (void)(b); (void)(c); (void)d; }
#else
#define BF_NEWDUMPDOT(a,b,c,d) BF_newDumpDot(a,b,c,d)
#endif


/**
 * @brief Main function. Performs all the work.
 * @param The clauses to be tested for whether they are optimally propagating or not. The trailing 0s are not contained.
 */
void testOptimalPropagation(const std::vector<std::vector<int> > &clauses) {

    BFManager mgr;
    std::vector<BF> allVars;
    std::vector<std::string> allVarNames;
    std::vector<BF> posVars;
    std::vector<BF> negVars;
    std::vector<BF> testValuationVars;

    // Allocate variables
    for (auto clause : clauses) {
        for (auto lit : clause) {
            unsigned int var = std::abs(lit);
            while (var>posVars.size()) {
                // Allocate new var
                int varNum = posVars.size()+1;
                std::ostringstream os;
                os << varNum;
                allVars.push_back(mgr.newVariable());
                posVars.push_back(allVars.back());
                allVarNames.push_back("p"+os.str());
                allVars.push_back(mgr.newVariable());
                negVars.push_back(allVars.back());
                allVarNames.push_back("n"+os.str());
                allVars.push_back(mgr.newVariable());
                testValuationVars.push_back(allVars.back());
                allVarNames.push_back("t"+os.str());
            }
        }
    }

    // Parse clauses in a BF only over the testValuationVars Variables
    BF completeInstanceOverTestVars = mgr.constantTrue();
    for (auto clause : clauses) {
        BF thisClause = mgr.constantFalse();
        for (auto lit : clause) {
            if (lit<0) {
                thisClause |= !testValuationVars[-1*lit-1];
            } else {
                thisClause |= testValuationVars[lit-1];
            }
        }
        completeInstanceOverTestVars &= thisClause;
    }
    BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),completeInstanceOverTestVars,NULL,"/tmp/completeInstanceOverTestVars.dot");


    // Compute BF that maps all partial assignments that give rise to unit propagation to TRUE
    BF partialAssignmentsThatGiveRiseToUnitPropagation = mgr.constantFalse();
    for (auto clause : clauses) {
        for (auto selectorLit : clause) {
            int selectorVar = std::abs(selectorLit);
            BF thisClause = (!posVars[selectorVar-1]) & (!negVars[selectorVar-1]);
            for (auto lit : clause) {
                if (lit!=selectorLit) {
                    if (lit<0) {
                        thisClause &= posVars[-1*lit-1];
                    } else {
                        thisClause &= negVars[lit-1];
                    }
                }
            }
            partialAssignmentsThatGiveRiseToUnitPropagation |= thisClause;
        }
    }
    BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),partialAssignmentsThatGiveRiseToUnitPropagation,NULL,"/tmp/partialAssignmentsThatGiveRiseToUnitPropagation.dot");

    // Compute BF representing which partial assignment should give rise to unit propagation.
    BF partialAssignmentsThatMapToFalse = !completeInstanceOverTestVars;
    for (unsigned int i=0;i<posVars.size();i++) {
        BF case0 = (!negVars[i]) | (partialAssignmentsThatMapToFalse & !testValuationVars[i]).ExistAbstractSingleVar(testValuationVars[i]);
        BF case1 = (!posVars[i]) | (partialAssignmentsThatMapToFalse & testValuationVars[i]).ExistAbstractSingleVar(testValuationVars[i]);
        BF caseX = negVars[i] | posVars[i] | partialAssignmentsThatMapToFalse.UnivAbstractSingleVar(testValuationVars[i]);
        partialAssignmentsThatMapToFalse = (case0 & case1 & caseX) & ((!negVars[i]) | (!posVars[i]));
    }
    BF_newDumpDot(TrivialVariableInfoContainer(mgr,allVarNames,allVars),partialAssignmentsThatMapToFalse,NULL,"/tmp/partialAssignmentsThatMapToFalse.dot");

    BF sanePartialAssignments = mgr.constantTrue();
    for (unsigned int i=0;i<posVars.size();i++) {
        sanePartialAssignments &= (!posVars[i]) | (!negVars[i]);
    }


    std::vector<BF> partialAssignmentsThatShouldGiveRiseToUnitPropagation;
    for (unsigned int i=0;i<posVars.size();i++) {
        BF oneShorter = (partialAssignmentsThatMapToFalse & (posVars[i] | negVars[i])).ExistAbstractSingleVar(posVars[i]).ExistAbstractSingleVar(negVars[i]) & !negVars[i] & !posVars[i];
        oneShorter &= !partialAssignmentsThatMapToFalse;
        oneShorter &= sanePartialAssignments;
        partialAssignmentsThatShouldGiveRiseToUnitPropagation.push_back(oneShorter);
#ifndef NDEBUG
        BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),oneShorter,NULL,"/tmp/partialAssignmentsThatShouldGiveRiseToUnitPropagation"+toString(i)+".dot");
#endif
    }
    //

    // Not compute the culprints - must be a correct parial assignment, though.
    std::vector<std::vector<BF> > soFar({{!partialAssignmentsThatGiveRiseToUnitPropagation}});
    for (unsigned int i=0;i<posVars.size();i++) {
        std::vector<BF> nextLevel;
        nextLevel.push_back(soFar.back()[0] & !partialAssignmentsThatShouldGiveRiseToUnitPropagation[i]);
        for (unsigned int j=1;j<soFar.back().size();j++) {
            nextLevel.push_back((soFar.back()[j] & !partialAssignmentsThatShouldGiveRiseToUnitPropagation[i]) | (soFar.back()[j-1] & partialAssignmentsThatShouldGiveRiseToUnitPropagation[i]));
        }
        nextLevel.push_back(soFar.back().back() & partialAssignmentsThatShouldGiveRiseToUnitPropagation[i]);
        soFar.push_back(nextLevel);
    }

    for (int nuv=soFar.back().size()-1;nuv>=0;nuv--) {
        BF culprits = soFar.back()[nuv];

        // We found a problem? Hmm, ok, print it to the user.
        if (!(culprits.isFalse())) {
            // Print a culprit
            BF_newDumpDot(TrivialVariableInfoContainer(mgr,allVarNames,allVars),culprits,NULL,"/tmp/culprits.dot");
            std::cout << nuv;
            std::cerr << "Partial assignment that should give rise to unit propagation: ";
            for (unsigned int i=0;i<posVars.size();i++) {
                if (!((culprits & posVars[i]).isFalse())) {
                    culprits &= posVars[i];
                    std::cerr << i+1 << " ";
                } else if (!((culprits & negVars[i]).isFalse())) {
                    culprits &= negVars[i];
                    std::cerr << -(int)i-1 << " ";
                } else {
                    culprits &= !negVars[i];
                    culprits &= !posVars[i];
                    assert(!culprits.isFalse());
                }
            }
            std::cerr << "\n";
            return;
        }
    }
    std::cout << "0";
}



int main(int argc, const char **args) {
    try {

        // Parse command line parameters
        std::string filename = "";
        for (int i=1;i<argc;i++) {
            std::string thisOne = args[i];
            if (thisOne.substr(0,1)=="-") {
                {
                    std::cerr << "Error: Did not understand the parameter '" << thisOne << std::endl;
                    return 1;
                }
            } else {
                if (filename!="") {
                    std::cerr << "Error: More than one input file name given.\n";
                    return 1;
                } else {
                    filename = thisOne;
                }
            }
        }

        if (filename=="") {
            std::cerr << "Error: Input file name missing!\n";
            return 1;
        }

        // Read input file
        std::ifstream inFile(filename);
        std::vector<std::vector<int> > clauses;
        if (inFile.fail()) throw "Error: Cannot open input file";
        std::string currentLine;
        while (std::getline(inFile,currentLine)) {
            if ((currentLine.substr(0,1)=="p") || (currentLine.substr(0,1)=="c") || (currentLine.size()==0)) {
                // Ignore comments
            } else {
                std::istringstream is(currentLine);
                std::vector<int> clause;
                int literal = -1;
                do {
                    is >> literal;
                    if (is.fail()) {
                        std::cerr << "In line: " << currentLine << std::endl;
                        throw "Error: Failed to read literal from file.";
                    }
                    if (literal!=0) clause.push_back(literal);
                } while ((literal!=0) && !(is.eof()));
                if (literal!=0) throw "Error: Non-terminated clause found";
                clauses.push_back(clause);
            }
        }

        testOptimalPropagation(clauses);
        return 0;
    } catch (const char *error) {
        std::cerr << error << std::endl;
        return 1;
    } catch (const std::string error) {
        std::cerr << error << std::endl;
        return 1;
    }
}
