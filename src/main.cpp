#include <iostream>
#include <algorithm>
#include "encoderContext.hpp"
#include "translatorClassNonPropagating.hpp"
#include "translatorClassDoublyApproximatelyOptimallyMAXSAT.hpp"
#include "satSolvers.hpp"
#include <fstream>
#include <map>
#include <boost/algorithm/string/trim.hpp>
#include "booleanFormulaParser.hpp"

int main(int argc, const char **args) {
    try {

        // Parse command line parameters
        std::string filename = "";
        int mode = -1; // 0=doubleApprox, 1=NonPropagating
        unsigned int approxMaxSizeUncoveredCubes;
        unsigned int approxMaxSizeUncoveredImplicants;

        for (int i=1;i<argc;i++) {
            std::string thisOne = args[i];
            if (thisOne.substr(0,1)=="-") {
                // Parse parameters
                if (thisOne=="--greedy") {
                    mode = 1;
                } else if (thisOne=="--approx") {
                    mode = 0;
                    if (i>=argc-2) {
                        std::cerr << "Error: Expected two numbers after '--approx'.\n";
                        return 1;
                    }
                    std::istringstream is(args[++i]);
                    is >> approxMaxSizeUncoveredCubes;
                    if (is.fail()) throw "Error: Number of '--approx' is invalid.";
                    std::istringstream is2(args[++i]);
                    is2 >> approxMaxSizeUncoveredImplicants;
                    if (is2.fail()) throw "Error: Number of '--approx' is invalid.";
                } else {
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
        
        if (mode==-1) {
            std::cerr << "Error: No operation mode given: supply '--approx' or '--greedy'\n";
            return 1;
        }

        if (filename=="") {
            std::cerr << "Error: Input file name missing!\n";
            return 1;
        }

        EncoderContext *context;
        if (mode==0) {
            context = new EncoderContextDoublyApproximatelyOptimallyPropagatingMaxSAT<LingelingSolver>(approxMaxSizeUncoveredCubes,approxMaxSizeUncoveredImplicants);
        } else if (mode==1) {
            context = new EncoderContextNonPropagating();
        } else {
            throw "Internal error.";
        }

        // Everything starting here is deleted after the context.
        {
            // Parse input file
            std::ifstream inputFile(filename);
            if (inputFile.fail()) throw "Error: Could not read input file.";
            std::string currentLine;
            unsigned int lineNumber = 0;
            std::map<std::string,BF> definedBFs;
            while (std::getline(inputFile,currentLine)) {
                lineNumber++;
                boost::trim(currentLine);

                if (currentLine.substr(0,2)=="//") {
                    // Comment, ignore
                } else if (currentLine.substr(0,4)=="var ") {

                    // Define variable
                    std::string varDef = currentLine.substr(4,std::string::npos);
                    boost::trim(varDef);

                    // Variable name illegal?
                    if ((varDef=="1") || (varDef=="0") || (varDef=="f") || (varDef=="t") || (varDef=="true") || (varDef=="false") || (varDef=="True") || (varDef=="False") || (varDef=="TRUE") || (varDef=="FALSE")) {
                        std::cerr << "Error: Illegal variable name in line " << lineNumber << std::endl;
                        return 1;
                    }

                    // See if variable already existing
                    if (context->hasVariable(varDef)) {
                        std::cerr << "Error: The variable in line " << lineNumber << " has been defined multiple times.";
                    }
                    context->newVariable(varDef);
                } else if (currentLine.length()>0) {
                    // Ok, a new command
                    // Search for equality sign
                    size_t posEqual = currentLine.find("=");
                    if (posEqual==std::string::npos) {
                        std::cerr << "Error: Line " << lineNumber << " does not represent a valid assignment.";
                    }
                    std::string assignTo = currentLine.substr(0,posEqual);
                    boost::trim(assignTo);
                    std::string formula = currentLine.substr(posEqual+1,std::string::npos);
                    boost::trim(formula);

                    BF thisData;
                    try {
                         thisData = parseBooleanFormula(formula,*context,definedBFs);
                    } catch (std::string error) {
                        std::cerr << "Error in line " << lineNumber << ": " << error << std::endl;
                        return 1;
                    }

                    definedBFs[assignTo] = thisData;
                }
            }

            if (inputFile.bad()) {
                std::cerr << "Error reading input file to the end.\n";
                return 1;
            }

            if (definedBFs.count("encode")==0) {
                std::cerr << "Error: The input file must define a Boolean function called 'encode' to determine what is to be encoded.\n";
                return 1;
            }

            BF encode = definedBFs.at("encode");
            unsigned int nofCoreVariables = context->getNofVariables();
            context->encode(encode,{},nofCoreVariables);            
            context->printEncoding();
            context->testGeneratedClauses(encode,nofCoreVariables);
        }

        delete context;
        return 0;
    } catch (const char *error) {
        std::cerr << error << std::endl;
        return 1;
    } catch (const std::string error) {
        std::cerr << error << std::endl;
        return 1;
    }
}
