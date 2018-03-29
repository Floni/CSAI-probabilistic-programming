#!/usr/bin/python3

import sys
import argparse
import subprocess

import time

from bif_to_cnf import parse_bif #, latex_print
from srl_to_cnf import parse_srl

from sympy.logic.boolalg import Not

from pysdd.sdd import SddManager, Vtree, WmcManager

MINIC2D_PATH = "../miniC2D-1.0.0/bin/linux/miniC2D"

def cnf_to_ints(cnf, variables):
    ints = []
    clauses = cnf.args
    for clause in clauses:
        disj = []
        for lit in clause.args:
            if type(lit) is Not:
                name = lit.args[0].name
                i = variables.index(name)+1
                disj.append(-i)
            else:
                name = lit.name
                i = variables.index(name)+1
                disj.append(i)
        ints.append(disj)
    return ints

def save_cnf(fname, ints, variables, weights, c2d):
    nclauses = len(ints)
    nvars = len(variables)

    with open(fname, "w") as f:
        f.write("c {}\n".format(fname))
        f.write("c\n")
        if c2d:
            w_str = ""
            for var in variables:
                w_tuple = weights[var]
                w_str += str(w_tuple[0]) + " " + str(w_tuple[1]) + " "
            f.write("c weights {}\n".format(w_str))

        f.write("p cnf {} {}\n".format(nvars, nclauses))

        if not c2d:
            for idx, var in enumerate(variables):
                w_tuple = weights[var]
                f.write("w {} {} {}\n".format(idx+1, w_tuple[0], w_tuple[1]))

        cnf_str = ""
        i = 0
        for clause in ints:
            i += 1
            for lit in clause:
                cnf_str += str(lit) + " "
            cnf_str += "0\n"
        f.write(cnf_str)

def main():
    arg_parser = argparse.ArgumentParser(description="problog pipeline")
    arg_parser.add_argument("--bif-file", "-b", help="The input bayesian network")
    arg_parser.add_argument("--pl-file", "-p", help="The input problog file")

    arg_parser.add_argument("cnf_file", help="The output cnf file")

    arg_parser.add_argument("--enc", "-e", default=1, help="The enc type 1 or 2", type=int)
    arg_parser.add_argument("--cnf-type", "-c", default="c2d", help="The type of cnf file to output (c2d for minic2d or cachet)")

    arg_parser.add_argument("--verbose", "-v", default=False, help="Verbose output", type=bool, nargs='?', const=True)

    args = arg_parser.parse_args()

    if (args.bif_file is None and args.pl_file is None) or \
        (args.bif_file is not None and args.pl_file is not None):
        print("one input file required")
        return -1

    c2d = True
    if args.cnf_type == "c2d":
        c2d = True
    elif args.cnf_type == "cachet":
        c2d = False
    else:
        print("unknwon cnf type")
        return -1

    is_bif = args.bif_file is not None
    file_name = args.bif_file if is_bif else args.pl_file

    enc1 = args.enc == 1
    verbose = args.verbose

    contents = None
    with open(file_name, 'r') as f:
        contents = f.read()

    variables = None
    cnf = None
    weights = None
    evidence = None
    queries = None

    start_time = time.time()

    if is_bif:
        variables, cnf, weights, queries = parse_bif(contents, enc1, verbose)
    else:
        variables, cnf, weights, evidence, queries = parse_srl(contents, verbose)

    cnf_time = time.time()

#    if verbose:
#        print("cnf latex:")
#        print(len(cnf.args))
#        clauses = cnf.args
#        for clause in clauses:
#            print("$", latex_print(clause), "$")
#            print()

    ints = cnf_to_ints(cnf, variables)

    if evidence is not None:
        for ev_name, ev_val in evidence:
            idx = variables.index(ev_name)+1
            if not ev_val:
                idx = -idx
            ints.append([idx])

    save_cnf(args.cnf_file, ints, variables, weights, c2d)

    vtree_time = None

    if c2d:
        vtree_name = args.cnf_file + ".vtree"
        print("miniC2D:")
        minic2d = subprocess.run(
            [MINIC2D_PATH, '-c', args.cnf_file, '-o', vtree_name])

        if minic2d.returncode != 0:
            print("error creating vtree")
            return -1

        vtree_time = time.time()

        print("calculating sdd")
        vtree = Vtree.from_file(vtree_name.encode())
        sdd = SddManager.from_vtree(vtree)
        root = sdd.read_cnf_file(args.cnf_file.encode())

        print("sdd node count:", sdd.count())
        print("sdd size:", sdd.size())
        if verbose:
            sdd.print_stdout()

        print()

        wmc = root.wmc(log_mode=False)
        w = wmc.propagate()
        print("model count:", w)

        nlits = sdd.var_count()
        assert nlits == len(variables)

        for idx in range(nlits):
            i = idx + 1
            w_pos = weights[variables[idx]][0]
            w_neg = weights[variables[idx]][1]
            wmc.set_literal_weight(sdd.literal(i), w_pos)
            wmc.set_literal_weight(sdd.literal(-i), w_neg)
        w = wmc.propagate()
        print("weighted count:", w)
        print()
        print("queries:")
        if queries is not None:
            for query in queries:
                idx = variables.index(query)+1
                pr = wmc.literal_pr(sdd.literal(idx))
                print("P(", query, ") =\t", pr)


    end_time = time.time()

    print()
    print("cnf variables:", len(variables), "clauses: ", len(ints))
    print()
    print("total time:\t", end_time - start_time)
    print("cnf time:\t", cnf_time - start_time)
    if vtree_time is not None:
        print("vtree time:\t", vtree_time - cnf_time)
        print("count time:\t", end_time - vtree_time)

    return 0

if __name__ == '__main__':
    sys.exit(main())
