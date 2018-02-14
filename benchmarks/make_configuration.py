#
# Configuration for all "make..." scripts
#
# For every tool, we need the following data:
# 1. Path and parameters to solver
# 2. Name of the case in the LaTeX table
# 3. File extension in the ".res" directory

BENCHMARK_SOLVER_CONFIGURATIONS = [
    ("../build/optic --greedy",                               "Greedy",               ".simpleenumerate"),
    #("../build/optic",                                        "Optic (Optimal)",      ".optimal"),
    #("../build/optic --fast",                                 "Optic (Fast)",        ".fast"),
    #("../build/optic --aux",                                  "Optic/Optimal/Aux",   ".optimal_aux"),
    #("../build/optic --fast --aux",                           "Optic/Fast/Aux",      ".fast_aux"),
    #("../build/optic --approx 3 --lingeling",                 "Optic (Approx 3)",    ".approx3"),
    #("../build/optic --approx 4 --lingeling",                 "Optic (Approx 4)",    ".approx4"),
    #("../build/optic --approx 5 --lingeling",                 "Optic (Approx 5)",    ".approx5"),
    #("../build/optic --approx 6 --lingeling",                 "Optic (Approx 6)",     ".approx6"),
    ("../build/optic --doubleApproxMaxSAT 99 99 --lingeling", "$(\infty,\infty)$",     ".apmaxsat9999"),
    ("../build/optic --doubleApproxMaxSAT 1 99 --lingeling",  "$(1,\infty)$",      ".apmaxsat199"),
    ("../build/optic --doubleApproxMaxSAT 2 99 --lingeling",  "$(2,\infty)$",      ".apmaxsat299"),
    ("../build/optic --doubleApproxMaxSAT 3 99 --lingeling",  "$(3,\infty)$",      ".apmaxsat399"),
    ("../build/optic --doubleApproxMaxSAT 3 3 --lingeling",   "$(3,3)$",            ".apmaxsat33"),
    #("../build/optic --doubleApproxMaxSAT 3 2 --lingeling",   "$(3,2)$",          ".apmaxsat32"),
    ("../build/optic --doubleApproxMaxSAT 99 1 --lingeling",  "$(\infty,1)$",      ".apmaxsat991"),    
    #("../build/optic --minimal",                              "Optic (Minimal)",      ".minimal"),
    #("../build/genpce",                                       "GenPCE (non-opt.)",    ".genpce"),
    ("../build/genpce -minimal",                              "GenPCE",        ".genpceminimal"),
]


