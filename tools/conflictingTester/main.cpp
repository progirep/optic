#include <iostream>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <map>
#include "BF.h"
#include "bddDump.h"


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
#define BF_NEWDUMPDOT(a,b,c,d) { (void)a; (void)b; (void)c; (void)d; }
#else
#define BF_NEWDUMPDOT(a,b,c,d) BF_newDumpDot(a,b,c,d)
#endif


/**
 * @brief Main function. Performs all the work.
 * @param The clauses to be tested for whether they are optimally conflicting or not. The trailing 0s are not contained.
 */
void testOptimalConfliction(const std::vector<std::vector<int> > &clauses) {

    BFManager mgr;
    std::vector<BF> allVars;
    std::vector<std::string> allVarNames;
    std::vector<BF> mainVars;
    std::vector<BF> careVars;

    // Allocate variables
    for (auto clause : clauses) {
        for (auto lit : clause) {
            unsigned int var = std::abs(lit);
            while (var>mainVars.size()) {
                // Allocate new var
                int varNum = mainVars.size()+1;
                std::ostringstream os;
                os << varNum;
                allVars.push_back(mgr.newVariable());
                mainVars.push_back(allVars.back());
                allVarNames.push_back("m"+os.str());
                allVars.push_back(mgr.newVariable());
                careVars.push_back(allVars.back());
                allVarNames.push_back("c"+os.str());
            }
        }
    }

    // Parse clauses in a BF only over the testValuationVars Variables
    BF completeInstanceOverMainVars = mgr.constantTrue();
    for (auto clause : clauses) {
        BF thisClause = mgr.constantFalse();
        for (auto lit : clause) {
            if (lit<0) {
                thisClause |= !mainVars[-1*lit-1];
            } else {
                thisClause |= mainVars[lit-1];
            }
        }
        completeInstanceOverMainVars &= thisClause;
    }
    BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),completeInstanceOverMainVars,NULL,"/tmp/completeInstanceOverMainVars.dot");


    // Compute BF that maps all partial assignments that give rise to unit propagation to TRUE
    BF partialAssignmentsThatGiveRiseToUnitPropagationOrConflicts = mgr.constantFalse();
    for (auto clause : clauses) {
        BF allLitsViolated = mgr.constantTrue();
        BF allLitsButOneViolated = mgr.constantFalse();
        for (auto lit : clause) {
            BF thisLit;
            BF thisCare;
            if (lit<0) {
                thisLit = mainVars[-1*lit-1];
                thisCare = careVars[-1*lit-1];
            } else {
                thisLit = !mainVars[lit-1];
                thisCare = careVars[lit-1];
            }
            allLitsButOneViolated = (allLitsButOneViolated & thisLit & thisCare) | (allLitsViolated & !thisCare);
            allLitsViolated &= thisLit & thisCare;
        }
        partialAssignmentsThatGiveRiseToUnitPropagationOrConflicts |= allLitsViolated | allLitsButOneViolated;
    }
    BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),partialAssignmentsThatGiveRiseToUnitPropagationOrConflicts,NULL,"/tmp/partialAssignmentsThatGiveRiseToUnitPropagationOrConflicts.dot");

    // Compute the partial assignments that are actually conflicting -- whenever a variable is don't care, the partial assignment can only
    // be conflicting if for both polarities, we get a conflict.
    BF conflictingPartialAssignments = !completeInstanceOverMainVars;
    for (unsigned int i=0;i<mainVars.size();i++) {
        conflictingPartialAssignments = (conflictingPartialAssignments & careVars[i]) | (conflictingPartialAssignments & !careVars[i]).UnivAbstractSingleVar(mainVars[i]);
    }

    // Compute the "problematic cases", i.e., the partial assignments that are conflicting but for which the encoded
    // CNF does not detect this by conflict or unit propagation.
    BF problematicCases = conflictingPartialAssignments & !partialAssignmentsThatGiveRiseToUnitPropagationOrConflicts;

    BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),problematicCases,NULL,"/tmp/problematicCases.dot");

    // Now measure how many don't care's we can have in the problematic cases
    std::vector<std::vector<BF> > nofDontCares;
    nofDontCares.push_back({problematicCases});
    for (unsigned int currentVar = 0;currentVar<mainVars.size();currentVar++) {
        std::vector<BF> thisLevel;
        for (unsigned int i=0;i<nofDontCares.back().size();i++) {
            BF cases = mgr.constantFalse();
            if (i>0) cases |= nofDontCares.back()[i-1] & careVars[currentVar];
            cases |= nofDontCares.back()[i] & !careVars[currentVar];
            thisLevel.push_back(cases);
        }
        thisLevel.push_back(nofDontCares.back().back() & careVars[currentVar]);
        nofDontCares.push_back(thisLevel);
    }

    /*for (int i=nofDontCares.back().size()-1;i>=0;i--) */
    for (int i=0;i<nofDontCares.back().size();i++) {
        if (!(nofDontCares.back()[i].isFalse())) {
            std::cout << nofDontCares.back().size()-i-1;
            BF_NEWDUMPDOT(TrivialVariableInfoContainer(mgr,allVarNames,allVars),nofDontCares.back()[i],NULL,"/tmp/worstCases.dot");
            return;
        }
    }

    std::cout << "$\\infty$";
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

        testOptimalConfliction(clauses);
        return 0;
    } catch (const char *error) {
        std::cerr << error << std::endl;
        return 1;
    } catch (const std::string error) {
        std::cerr << error << std::endl;
        return 1;
    }
}
