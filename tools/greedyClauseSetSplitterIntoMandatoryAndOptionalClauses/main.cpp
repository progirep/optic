#include <iostream>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <map>
#include "BF.h"
#include "bddDump.h"


/**
 * @brief Main function. Performs all the work.
 * @param The clauses to be tested for whether they are optimally propagating or not. The trailing 0s are not contained.
 */
void splitter(const std::vector<std::vector<int> > &clauses, std::ofstream &outMandatory, std::ofstream &outOptional) {

    BFManager mgr;
    std::vector<BF> allVars;
    std::vector<std::string> allVarNames;

    for (auto clause : clauses) {
        for (auto lit : clause) {
            unsigned int var = std::abs(lit);
            while (var>allVars.size()) {
                // Allocate new var
                int varNum = allVars.size()+1;
                std::ostringstream os;
                os << varNum;
                allVars.push_back(mgr.newVariable());
                allVarNames.push_back("p"+os.str());
            }
        }
    }
    
    BF completeInstance = mgr.constantTrue();
    for (auto clause : clauses) {
        BF thisClause = mgr.constantFalse();
        for (auto lit : clause) {
            if (lit<0) {
                thisClause |= !allVars[-1*lit-1];
            } else {
                thisClause |= allVars[lit-1];
            }
        }
        completeInstance &= thisClause;
    }
    
    // Initialize list of mandatory clauses
    std::vector<bool> mandatoryClauses;
    for (unsigned int i=0;i<clauses.size();i++) {
        mandatoryClauses.push_back(true);
    }
    
    // Check which ones can be removed
    for (unsigned int i=0;i<clauses.size();i++) {
        BF test = mgr.constantTrue();
        for (unsigned int j=0;j<clauses.size();j++) {
            if ((j!=i) && mandatoryClauses[j]) {
                BF thisClause = mgr.constantFalse();
                for (auto lit : clauses[j]) {
                    if (lit<0) {
                        thisClause |= !allVars[-1*lit-1];
                    } else {
                        thisClause |= allVars[lit-1];
                    }
                }
                test &= thisClause;
            }
        }
        if (test==completeInstance) mandatoryClauses[i] = false;
    }   
    
    // Output clauses
    for (unsigned int i=0;i<clauses.size();i++) {
        std::ofstream &out = mandatoryClauses[i]?outMandatory:outOptional;
        for (auto lit : clauses[i]) {
            out << lit << " ";
        }
        out << "0\n";
    }
}



int main(int argc, const char **args) {
    try {

        // Parse command line parameters
        std::vector<std::string> filenames;
        for (int i=1;i<argc;i++) {
            std::string thisOne = args[i];
            if (thisOne.substr(0,1)=="-") {
                {
                    std::cerr << "Error: Did not understand the parameter '" << thisOne << std::endl;
                    return 1;
                }
            } else {
                filenames.push_back(thisOne);
            }
        }

        if (filenames.size()!=3) {
            std::cerr << "Error: Expected exactly three file names: The input file, the output file for the mandatory clauses, and the output file for the optional clauses!\n";
            return 1;
        }

        // Read input file
        std::ifstream inFile(filenames[0]);
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
        
        std::ofstream outFileMandatory(filenames[1]);
        std::ofstream outFileOptional(filenames[2]);

        splitter(clauses,outFileMandatory,outFileOptional);
        return 0;
    } catch (const char *error) {
        std::cerr << error << std::endl;
        return 1;
    } catch (const std::string error) {
        std::cerr << error << std::endl;
        return 1;
    }
}
