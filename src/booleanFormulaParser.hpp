#ifndef __BOOLEAN_FORMULA_PARSER_HPP__
#define __BOOLEAN_FORMULA_PARSER_HPP__

#include "encoderContext.hpp"
#include <map>

BF parseBooleanFormula(std::string const &formula, EncoderContext const &context, const std::map<std::string,BF> &definedBFs);

#endif
