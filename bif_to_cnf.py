#!/usr/bin/python3

import sys
import argparse
import itertools

import sympy

from deps.bif_parser import BIFParser as BIFP

from sympy.logic.boolalg import Not, And, Or, Equivalent, Implies, to_cnf

# variables are tuple: (sympy var, node name, var state name)
# conditional variables have an extra element:
#   (sympy var, node name, var state name, (conditional var 1, ...))
# for cnf: clauses are tuples (Boolean, variable)
# with boolean == False <=> not(var)
# and variable as defined above

LATEX_NAMES = False

def get_combinations(list_of_lists):
    """
        Returns all posible combinations of the given lists
        used to create all conditional variables
    """
    return itertools.product(*list_of_lists)

def create_var(node, state):
    """
        Creates a variable representing that the given node is in the given state
    """
    if LATEX_NAMES:
        var_name = "\\lambda_{" + node.getName() + "\\_" + state  + "}"
    else:
        var_name = node.getName() + '_' + state
    return (sympy.Symbol(var_name), node.getName(), state)

def create_conditional_var(node, state, conds, parents):
    """
        Creates a conditional probability variable of the node in the given state
        assumings all conds states of parents
    """
    if LATEX_NAMES:
        cond_names = ",".join([b.getName() + "\\_" + a for a, b in zip(conds, parents)])
        var_name = "\\theta_{" + node.getName() + "\\_" + state + "|" + cond_names+ "}"
    else:
        var_name = node.getName() + "_" + state + "|" + "_".join(conds)
    return (sympy.Symbol(var_name), node.getName(), state, tuple(conds))

def get_state_vars(node):
    """ Creates all state variables of the given node """
    return [create_var(node, s) for s in node.getStates()]

def get_all_cond_vars(node):
    """ Creates all conditional state variables """
    cond_list = [node.getStates()]
    parents = node.getParents()
    for parent in parents:
        cond_list.append(parent.getStates())
    pairs = get_combinations(cond_list)
    return [create_conditional_var(node, p[0], p[1:], parents) for p in pairs]

def create_variables(nodes, enc1):
    """ creates required all variables """
    variables = []
    queries = []
    for node in nodes:
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
        pvars = [create_conditional_var(node, p[0], p[1:], parents) for p in pairs]

        for v in svars:
            queries.append(v[0].name)

        # add all variables
        for v in svars + pvars:
            variables.append(v[0].name)

    return variables, queries

def create_indicator_cnf(node):
    """ Creates the indicator clauses """
    cnf = []
    svars = get_state_vars(node)
    # the disjunction of all states:
    cnf.append(Or(*[s[0] for s in svars]))

    # negation:
    l = len(svars)
    for j in range(l):
        for i in range(j):
            sa = svars[j][0]
            sb = svars[i][0]
            cnf.append(~sa | ~sb)
    return cnf


def toEnc1(nodes):
    """ Creates the ENC 1 encoding of the given nodes """
    cnf = []

    for node in nodes:
        cnf += create_indicator_cnf(node)

        parents = node.getParents()

        cond_list = [node.getStates()]
        for parent in parents:
            cond_list.append(parent.getStates())
        pairs = get_combinations(cond_list)

        nodes = [node] + parents

        # create parameter clauses
        for pair in pairs:
            par_var = create_conditional_var(node, pair[0], pair[1:], parents)

            rl = par_var[0]
            ll = And(*[create_var(nodes[i], s)[0] for i, s in enumerate(pair)])

            cnf.append(Equivalent(ll, rl))
    return And(*cnf)


def toEnc2(nodes):
    """ Creates the ENC 2 encoding of the given nodes """
    cnf = []
    for node in nodes:
        states = node.getStates()

        cnf += create_indicator_cnf(node)

        cond_list = [states]
        parents = node.getParents()
        for parent in parents:
            cond_list.append(parent.getStates())
        pairs = itertools.product(*cond_list)

        nodes = [node] + parents

        for pair in pairs:
            # pair[0] is the state of the node
            # pair[1:] are the state of all conditionals
            ll = [create_var(nodes[i+1], s)[0] for i, s in enumerate(pair[1:])]
            ll += [~(create_conditional_var(node, s, pair[1:], parents)[0]) for s in states[:states.index(pair[0])]]
            if pair[0] != states[-1]:
                ll += [create_conditional_var(node, pair[0], pair[1:], parents)[0]]

            ll = And(*ll)

            rl = create_var(node, pair[0])[0]
            #print(ll, '=>', rl)
            cnf.append(Implies(ll, rl))

    return And(*cnf)

def assign_weights_enc1(nodes):
    weights = {}
    for node in nodes:
        cpd = node.getDist()
        cvars = get_all_cond_vars(node)

        for cvar in cvars:
            # cpd[state_of_node + state_of_conditionals]
            prob = cpd[(cvar[2],) + cvar[3]]
            weights[cvar[0].name] = prob
    return weights

def assign_weights_enc2(nodes):
    weights = {}
    for node in nodes:
        states = node.getStates()
        cpd = node.getDist()
        cvars = get_all_cond_vars(node)

        for cvar in cvars:
            prob = cpd[(cvar[2],) + cvar[3]]
            # index of state
            idx = states.index(cvar[2])
            divisor = 1
            for i in range(idx):
                divisor -= cpd[(states[i],) + cvar[3]]
            # TODO: 0 or 1 if divisor == 0
            weights[cvar[0].name] = prob / divisor if divisor > 0 else 0
    return weights

def weights_to_dict(weights, variables, enc1):
    ws = {}
    for var in variables:
        if var in weights:
            weight = weights[var]
            ws[var] = (weight, 1 if enc1 else (1 - weight))
        else:
            ws[var] = (1, 1)
    return ws


def latex_print(s):
    if type(s) is And:
        return " \\wedge ".join([latex_print(a) for a in s.args])
    elif type(s) is Or:
        return " \\vee ".join([latex_print(a) for a in s.args])
    elif type(s) is Equivalent:
        return latex_print(s.args[0]) + " \\Leftrightarrow " + latex_print(s.args[1])
    elif type(s) is Implies:
        return latex_print(s.args[0]) + " \\Rightarrow " + latex_print(s.args[1])
    elif type(s) is Not:
        return " \\neg " + latex_print(s.args[0])
    else:
        return s.name

def parse_bif(contents, enc1, verbose):
    nodes = None

    bif_w = contents.splitlines()
    bif = BIFP.fixWhiteSpace(bif_w)
    nodes = BIFP.parseBIF(bif)

    if nodes is None:
        print("error parsing bif")
        return -1

    if verbose:
        print(">bif info:")
        for n in nodes:
            n.printNode()

    # create variables
    # map from name to int
    variables, queries = create_variables(nodes, enc1)

    if verbose:
        print("variables:")
        for v in variables:
            print(v)

    # create cnf
    cnf = toEnc1(nodes) if enc1 else toEnc2(nodes)

    if verbose:
        print("enc:")
        clauses = cnf.args
        for clause in clauses:
            p = "$ "

            p += latex_print(clause)

            p += " $"
            print(p)
            print()

    cnf = to_cnf(cnf)

    if verbose:
        print("cnf:")
        print(cnf)

    # assign weights
    weights = assign_weights_enc1(nodes) if enc1 else assign_weights_enc2(nodes)
    weights = weights_to_dict(weights, variables, enc1)

#    if verbose:
#        print("weights:")
#        keys = weights.keys()
#        for key in keys:
#            print("$ " + key + " $ & " + str(weights[key][0])  + "&" + str(weights[key][1]) + " \\\\")

    return variables, cnf, weights, queries