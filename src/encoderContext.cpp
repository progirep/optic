#include "encoderContext.hpp"
#include <map>
#include <algorithm>
#include <fstream>

/**
 * @brief Prints the SAT encoding. Orders the literals to allow better comparisons
 */
void EncoderContext::printEncoding() {
    std::cout << "Encoding start\n";
    for (auto it : clauses) {
        // std::sort(it.begin(),it.end());
        for (auto it2 : it) {
            std::cout << it2 << " ";
        }
        std::cout << "0\n";
    }
    std::cout << "Encoding end\n";
    std::cout.flush();
}


/**
 * @brief This function tests if the clauses stored in the "clauses" field of this program are togeter
 *        equivalent to the original Boolean function representing the constraints.
 *        The function does not check if the generated clauses are propagation-complete.
 * @param constraints
 */
void EncoderContext::testGeneratedClauses(BF constraints,unsigned int nofPropagatingVars) {
    BF allClauses = mgr.constantTrue();
    //std::cerr << "Final final set of clauses:\n";
    for (auto it : clauses) {
        BF thisClause = mgr.constantFalse();
        for (auto it2 : it) {
            //std::cerr << it2 << " ";
            if (it2<0) {
                thisClause |= !variables[-it2-1];
            } else {
                thisClause |= variables[it2-1];
            }
        }
        //std::cerr << "\n";
        allClauses &= thisClause;
    }
    //std::cerr << "end of list.\n";

    // Take care of auxiliary vars
    std::vector<BF> auxVars;
    for (unsigned int i=nofPropagatingVars;i<variables.size();i++) {
        auxVars.push_back(variables[i]);
    }
    allClauses = allClauses.ExistAbstract(mgr.computeCube(auxVars));
    constraints = constraints.ExistAbstract(mgr.computeCube(auxVars));

    if (allClauses != constraints) {
        BF_newDumpDot(*this,allClauses & !constraints,NULL,"/tmp/diffA.dot");
        BF_newDumpDot(*this,(!allClauses) & constraints,NULL,"/tmp/diffB.dot");
        std::ofstream clauseFile("/tmp/wrongClauses.txt");
        for (auto it : clauses) {
            for (auto it2 : it) {
                clauseFile << it2 << " ";
            }
            clauseFile << "0\n";
        }
        throw "Error: The generated clauses could not be successfully tested!";
    }
}


/**
 * @brief This function encodes the "constraint" BF with additional auxiliary variables over which the
 * generated clause set is not optimally propagating
 * @param constraints the constraints to be encoded
 */
void EncoderContext::encodeWithAuxVars(BF constraints, unsigned int auxThreshold) {

    unsigned int nofCoreVariables = variables.size();
    std::vector<std::vector<int> > addedClauses;
    BF addedClausesBF = mgr.constantTrue();

    // Reduce until threshold has been reahed
    while (true) {

        // Build new encoding
        encode(constraints & addedClausesBF,addedClauses,nofCoreVariables);

        // Debugging abort..
        if (addedClauses.size()>8) {
            return;
        }

        // Iterate over the clauses and check for each clause if there is also the same clause with one literal different

        // Copy clauses so that they are in set form
        std::vector<std::set<int> > clausesCopy;
        for (auto it: clauses) {
            clausesCopy.push_back(std::set<int>(it.begin(),it.end()));
        }

        std::map<std::tuple<int,int>,unsigned int> nofOccurrencesNonXOR;
        std::map<std::tuple<int,int>,unsigned int> nofOccurrencesXOR;
        std::map<std::tuple<int,int>,std::vector<std::tuple<int,int> > > clausePairsNonXOR;
        std::map<std::tuple<int,int>,std::vector<std::tuple<int,int> > > clausePairsXOR;

        for (unsigned int i=0;i<clausesCopy.size();i++) {
            for (auto it : clausesCopy[i]) {
                std::set<int> copy1 = clausesCopy[i];
                copy1.erase(it);
                for (unsigned int j=i+1;j<clausesCopy.size();j++) {
                    if (copy1.size()==clausesCopy[j].size()-1) {
                        std::set<int> copy2;
                        std::set_difference(clausesCopy[j].begin(), clausesCopy[j].end(), copy1.begin(), copy1.end(),
                            std::inserter(copy2, copy2.end()));

                        // Check if it makes sense to build an AND/OR/NAND-like function
                        if (copy2.size()==1) {
                            int mini = std::min(it,*(copy2.begin()));
                            int maxi = std::max(it,*(copy2.begin()));
                            auto thisTuple = std::make_tuple(mini,maxi);
                            if (nofOccurrencesNonXOR.find(thisTuple)==nofOccurrencesNonXOR.end()) {
                                nofOccurrencesNonXOR[thisTuple] = 1;
                            } else {
                                nofOccurrencesNonXOR[thisTuple]++;
                            }
                            clausePairsNonXOR[thisTuple].push_back(std::make_tuple(it==mini?i:j,it==mini?j:i));
                        }
                    }
                }
            }
        }

        for (unsigned int i=0;i<clausesCopy.size();i++) {
            std::set<int> copy1 = clausesCopy[i];
            for (unsigned int j=i+1;j<clausesCopy.size();j++) {
                if (copy1.size()==clausesCopy[j].size()) {
                    std::set<int> copy2;
                    std::set_difference(clausesCopy[j].begin(), clausesCopy[j].end(), copy1.begin(), copy1.end(),
                        std::inserter(copy2, copy2.end()));

                    // Check if it is a XOR-like function.
                    if (copy2.size()==2) {

                        // XOR - Normalize the literal pair
                        int literalA = *(copy2.begin());
                        int literalB = *(++(copy2.begin()));
                        if ((copy1.count(-1*literalA)>0) && (copy1.count(-1*literalB)>0)) {
                            if (std::abs(literalA)<std::abs(literalB)) std::swap(literalA,literalB);
                            if (literalA>0) {
                                literalA *= -1;
                                literalB *= -1;
                            }
                            auto thisTuple = std::make_tuple(literalA,literalB);
                            if (nofOccurrencesXOR.find(thisTuple)==nofOccurrencesXOR.end()) {
                                nofOccurrencesXOR[thisTuple] = 1;
                            } else {
                                nofOccurrencesXOR[thisTuple]++;
                            }
                            if (copy1.count(literalA)>0) {
                                clausePairsXOR[thisTuple].push_back(std::make_tuple(i,j));
                            } else {
                                clausePairsXOR[thisTuple].push_back(std::make_tuple(j,i));
                            }
                        }
                    }
                }
            }
        }

        // Find the best tuple
        unsigned int bestValue = 0;
        bool bestValueXOR = false;
        std::tuple<int,int> bestPair;

        // Non-XOR...
        for (auto it : nofOccurrencesNonXOR) {
            // std::cerr << "n NofOccNonXOR: " << it.first.first << "," << it.first.second << "," << it.second << std::endl;
            if (it.second>bestValue) {
                bestValue = it.second;
                bestPair = it.first;
            }
        }

        // XOR...
        for (auto it : nofOccurrencesXOR) {
            if (it.second>bestValue) {
                bestValue = it.second;
                bestPair = it.first;
                bestValueXOR = true;
            }
        }

        // Ok, if the best correlation does not lead to enough simplication, just stop at this point.
        std::cerr << "c BestValue: " << bestValue << " for " << std::get<0>(bestPair) << "," << std::get<1>(bestPair) << " with type " << bestValueXOR << std::endl;
        if (auxThreshold<2) {
            throw "Error: 'auxThreshold' must be at least 2 as otherwise aux. variables that represent TRUE or FALSE could be introduced, which breaks the minimization procedure.";
        }
        if (bestValue<auxThreshold) {
            return;
        }

        if (bestValueXOR) {

            // Merge! XOR Version!
            clauses.clear();
            newVariable("addedAuxVarXor");
            int newVar = variables.size();
            std::cerr << "c NEWVAR: " << newVar << std::endl;

            // Add defining clauses for the new variable
            addedClauses.push_back(std::vector<int>{-1*newVar,-1*std::get<0>(bestPair),-1*std::get<1>(bestPair)});
            addedClauses.push_back(std::vector<int>{-1*newVar,std::get<0>(bestPair),std::get<1>(bestPair)});
            addedClauses.push_back(std::vector<int>{newVar,std::get<0>(bestPair),-1*std::get<1>(bestPair)});
            addedClauses.push_back(std::vector<int>{newVar,-1*std::get<0>(bestPair),std::get<1>(bestPair)});

            BF a = std::get<0>(bestPair)<0?!variables[-1*std::get<0>(bestPair)-1]:variables[std::get<0>(bestPair)-1];
            BF b = std::get<1>(bestPair)<0?!variables[-1*std::get<1>(bestPair)-1]:variables[std::get<1>(bestPair)-1];
            addedClausesBF &= (!variables[newVar-1]) ^ a ^ b;

        } else {

            // Merge! NON-XOR Version!
            clauses.clear();
            newVariable("addedAuxVarNonXor");
            int newVar = variables.size();


            // Add defining clauses for the new variable
            addedClauses.push_back(std::vector<int>{-1*newVar,std::get<0>(bestPair)});
            addedClauses.push_back(std::vector<int>{-1*newVar,std::get<1>(bestPair)});
            addedClauses.push_back(std::vector<int>{newVar,-1*std::get<0>(bestPair),-1*std::get<1>(bestPair)});
            BF a = std::get<0>(bestPair)<0?!variables[-1*std::get<0>(bestPair)-1]:variables[std::get<0>(bestPair)-1];
            BF b = std::get<1>(bestPair)<0?!variables[-1*std::get<1>(bestPair)-1]:variables[std::get<1>(bestPair)-1];
            BF andIng = a & b;
            addedClausesBF &= (!variables[newVar-1]) ^ andIng;
        }
    }



}
