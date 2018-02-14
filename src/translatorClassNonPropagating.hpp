#ifndef __TRANSLATOR_CLASS_NONPRPAGATING__HPP___
#define __TRANSLATOR_CLASS_NONPRPAGATING__HPP___

#include "encoderContext.hpp"

class EncoderContextNonPropagating : public EncoderContext {
public:

    // Main functionality
    void encode(BF constraints, std::vector<std::vector<int> > const &prefilledClauses, unsigned int nofPropagatingVars);

};
















#endif
