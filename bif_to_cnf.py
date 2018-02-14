#!/usr/bin/python3

import sys
import argparse
import itertools

from deps.bif_parser import BIFParser as BIFP


# variables are tuple: (node name, var state name)
# conditional variables have an extra tuple: (node name, var state name, (conditional var 1, ...))
# for cnf: clauses are tuples (Boolean, variable)
# with boolean == False <=> not(var)
# and variable as defined above

def get_combinations(list_of_lists):
    return itertools.product(*list_of_lists)

def create_var(node, state):
    return (node.getName(), state)

def create_conditional_var(node, state, conds):
    return (node.getName(), state, tuple(conds))

def var_cnf(var, true=True):
    return (true, var)

def get_state_vars(node):
    return [create_var(node, s) for s in node.getStates()]

def get_all_cond_vars(node):
    cond_list = [node.getStates()]
    for parent in node.getParents():
        cond_list.append(parent.getStates())
    pairs = get_combinations(cond_list)
    return [create_conditional_var(node, p[0], p[1:]) for p in pairs]

def create_variables(nodes, enc1):
    variables = {}
    nvars = 0
    for node in nodes:
        name = node.getName()
        states = node.getStates()

        # each state gets one variable
        svars = get_state_vars(node)

        parents = node.getParents()
        # per state and state of each parent -> one variable
        if enc1:
            cond_list = [states]
        else:
            cond_list = [states[:-1]]

        for parent in parents:
            cond_list.append(parent.getStates())

        pairs = get_combinations(cond_list)
        pvars = [create_conditional_var(node, p[0], p[1:]) for p in pairs]

        for v in svars + pvars:
            variables[v] = nvars + 1
            nvars += 1

    return variables, nvars

def not_cnf(x):
    """ Negates the given cnf variable """
    return (not x[0], x[1])

def notOfAnds(ands):
    """ maps not_cnf to the given list of ands turning it into an or """
    return [not_cnf(x) for x in ands]

def convImplToCnf(left, right):
    if len(right) > 1:
        return [convImplToCnf(left, [r])[0] for r in right]
    else:
        return [notOfAnds(left) + right]

def convEqToCnf(left, right):
    impl1 = convImplToCnf(left, right)
    impl2 = convImplToCnf(right, left)
    return impl1 + impl2


def create_indicator_cnf(node):
    cnf = []
    svars = get_state_vars(node)
    # the disjunction of all states:
    cnf.append([var_cnf(v) for v in svars])

    # negation:
    l = len(svars)
    for j in range(l):
        for i in range(j):
            cnf.append([var_cnf(svars[i], False), var_cnf(svars[j], False)])
    return cnf


def toEnc1(nodes):
    cnf = []
    for node in nodes:
        cnf += create_indicator_cnf(node)

        parents = node.getParents()

        cond_list = [node.getStates()]
        for parent in parents:
            cond_list.append(parent.getStates())
        pairs = get_combinations(cond_list)

        nodes = [node] + parents

        for pair in pairs:
            rl = var_cnf(create_conditional_var(node, pair[0], pair[1:])) #name + '.cv.' + '|'.join(pair)
            ll = [var_cnf(create_var(nodes[i], s)) for i, s in enumerate(pair)] # [pnames[i] + '.v.' + s for i, s in enumerate(pair)]
            #print(convEqToCnf(ll, [rl]))
            cnf += convEqToCnf(ll, [rl])
    return cnf


def toEnc2(nodes):
    cnf = []
    for node in nodes:
        states = node.getStates()

        cnf += create_indicator_cnf(node)

        cond_list = [states]
        for parent in node.getParents():
            cond_list.append(parent.getStates())
        pairs = itertools.product(*cond_list)

        nodes = [node] + node.getParents()

        for pair in pairs:
            ll = [var_cnf(create_var(nodes[i+1], s)) for i, s in enumerate(pair[1:])]
            ll += [var_cnf(create_conditional_var(node, s, pair[1:]), False) for s in states[:states.index(pair[0])]]
            if pair[0] != states[-1]:
                ll += [var_cnf(create_conditional_var(node, pair[0], pair[1:]))]

            rl = var_cnf(create_var(node, pair[0]))
            #print(ll, '=>', rl)
            cnf += convImplToCnf(ll, [rl])

    return cnf


def cnfToInts(cnf, variables):
    ret = ""
    for conj in cnf:
        line = ""
        for disj in conj:
            i = variables[disj[1]]
            if not disj[0]:
                i = -i
            line += str(i) + " "
        line += "0\n"
        ret += line
    return ret

def assign_weights_enc1(nodes):
    weights = {}
    for node in nodes:
        cpd = node.getDist()
        cvars = get_all_cond_vars(node)

        for cvar in cvars:
            prob = cpd[(cvar[1],) + cvar[2]]
            weights[cvar] = prob
    return weights

def assign_weights_enc2(nodes):
    weights = {}
    for node in nodes:
        states = node.getStates()
        cpd = node.getDist()
        cvars = get_all_cond_vars(node)

        for cvar in cvars:
            prob = cpd[(cvar[1],) + cvar[2]]
            # index of state
            idx = states.index(cvar[1])
            divisor = 1
            for i in range(idx):
                divisor -= cpd[(states[i],) + cvar[2]]

            weights[cvar] = prob / divisor
    return weights

def weights_to_str(weights, variables, enc1, c2d):
    ws = {}
    for var in variables:
        if var in weights:
            weight = weights[var]
            ws[variables[var]] = (weight, 1 if enc1 else (1 - weight))
        else:
            ws[variables[var]] = (1 if c2d else -1, 1)

    wline = ""
    if c2d:
        wline += "c weights"
        for i in range(len(variables)):
            wline += " " + str(ws[i+1][0]) + " " + str(ws[i+1][1])
        wline += '\n'
    else:
        for i in range(len(variables)):
            wline += "w " + str(i+1) + " " + str(ws[i+1][0]) + "\n"
    return wline

def main():
    parser = argparse.ArgumentParser(description="Convert a baysean network to CNF")
    parser.add_argument("--enc", "-e", default=1, type=int)
    parser.add_argument("--cnf-type", default="c2d", type=str)
    parser.add_argument("bif_file")
    parser.add_argument("cnf_file")

    args = parser.parse_args()

    bif_file_name = args.bif_file
    cnf_file_name = args.cnf_file

    enc1 = args.enc == 1
    cnf_type = args.cnf_type

    nodes = None
    with open(bif_file_name, "r") as f:
        bif_w = f.readlines()
        bif = BIFP.fixWhiteSpace(bif_w)
        nodes = BIFP.parseBIF(bif)

    if nodes is None:
        print("error parsing bif")
        return -1

    print(">bif info:")
    for n in nodes:
        n.printNode()

    # create variables
    # map from name to int
    variables, nvars = create_variables(nodes, enc1)

    print("variables:")
    for v in variables:
        print(v, "=", variables[v])

    # create cnf
    cnf = toEnc1(nodes) if enc1 else toEnc2(nodes)

    print("cnf:")
    for c in cnf:
        print(c)

    # assign weights
    weights = assign_weights_enc1(nodes) if enc1 else assign_weights_enc2(nodes)

    print("weights:")
    print(weights)
    # save cnf

    with open(cnf_file_name, "w") as f:
        f.write("c " + cnf_file_name + "\n")
        f.write("c " + bif_file_name + "\n")
        f.write("c\n")

        f.write("p cnf " + str(nvars) + " " + str(len(cnf)) + "\n")

        wline = weights_to_str(weights, variables, enc1, cnf_type == "c2d")
        f.write(wline)
        f.write(cnfToInts(cnf, variables))
    return 0


if __name__ == '__main__':
    sys.exit(main())
