#
# Configuration for all "make..." scripts
#
# For every tool, we need the following data:
# 1. Path and parameters to solver
# 2. Name of the case in the LaTeX table
# 3. File extension in the ".res" directory

BENCHMARK_SOLVER_CONFIGURATIONS = [
    ("../src/optic --greedy",                               "Greedy",               ".simpleenumerate"),
    ("../src/optic --approx 99 99 ",                        "$(\infty,\infty)$",    ".apmaxsat9999"),
    ("../src/optic --approx 1 99",                          "$(1,\infty)$",         ".apmaxsat199"),
    ("../src/optic --approx 2 99",                          "$(2,\infty)$",         ".apmaxsat299"),
    ("../src/optic --approx 3 99",                          "$(3,\infty)$",         ".apmaxsat399"),
    ("../src/optic --approx 3 3",                           "$(3,3)$",              ".apmaxsat33"),
    ("../src/optic --approx 99 1",                          "$(\infty,1)$",         ".apmaxsat991"),    
    ("../lib/genpce/GenPCE -minimal",                              "GenPCE",               ".genpceminimal"),
]


