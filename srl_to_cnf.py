#!/usr/bin/python3

import sys
import argparse
import subprocess
import problog
import sympy

from sympy.logic.boolalg import Not, And, Or, Equivalent, to_cnf

variables = {}

def term_to_var_name(term):
    return term.functor + '_' + '_'.join(map(str, term.args))

curVarId = 1
def get_var(name, prob=None):
    global curVarId
    if name in variables:
        if prob is not None:
            variables[name] = (variables[name][0], prob)
        return variables[name]
    else:
        ret = (sympy.Symbol(name), prob)
        variables[name] = ret
        curVarId += 1
        return ret

def add_clause(clauses, name, form):
    if name in clauses:
        clauses[name].append(form)
    else:
        clauses[name] = [form]

def parse_formula(formula):
    if type(formula) is problog.logic.Term:
        name = term_to_var_name(formula)
        return get_var(name)[0]
    elif type(formula) is problog.logic.And:
        f1 = parse_formula(formula.op1)
        f2 = parse_formula(formula.op2)
        return f1 & f2
    elif type(formula) is problog.logic.Or:
        f1 = parse_formula(formula.op1)
        f2 = parse_formula(formula.op2)
        return f1 | f2
    elif type(formula) is problog.logic.Not:
        f1 = parse_formula(formula.child)
        return ~f1
    else:
        raise Exception("unknown formula: " + str(formula))

def parse_srl(contents, verbose):
    grounded = subprocess.run(['problog', 'ground', '-'],
        stdout=subprocess.PIPE, input=contents.encode())
    grounded_str = grounded.stdout.decode()
    #grounded_str = ""

    # TODO: first variable pass and then built clauses as order isn't preserved
    #with open(pl_file_name, "r") as f:
    #    grounded_str = f.read()

    factory = problog.program.PrologFactory()
    parser = problog.parser.PrologParser(factory)
    parsed = parser.parseString(grounded_str)

    clauses = {} # map of name to list of formulas, which need to be ored

    disjunctions = [] # list of disjunctions: list of list of var names that are xor [['a1', 'a2'], ['b1', 'b2', 'b3']]

    evidence = [] # list of evidence (var_name, evidence = true or false)
    queries = [] # list of variables to query

    for clause in parsed:
        if verbose:
            print(type(clause))
            print(clause)

        if type(clause) is problog.logic.Clause:
            head = clause.head
            if verbose:
                print(head)
            head_name = term_to_var_name(head)

            body = clause.body
            if verbose:
                print(body)
                print(type(body))

            bform = parse_formula(body)

            # handle probability
            if head.probability is not None:
                temp_name = head_name + "_p" + str(curVarId)
                v = get_var(temp_name, head.probability)
                bform &= v[0]

            if head_name in clauses:
                clauses[head_name].append(bform)
            else:
                if head_name not in variables:
                    get_var(head_name, None) # No probability, handled above
                clauses[head_name] = [bform]

        elif type(clause) is problog.logic.Or:
            # disjunction with probabilities
            disj = []
            ors = [clause]
            terms = []

            while len(ors) > 0:
                cur_or = ors.pop()
                e1 = cur_or.op1
                e2 = cur_or.op2

                if type(e1) is problog.logic.Or:
                    ors.append(e1)
                else:
                    terms.append(e1)

                if type(e2) is problog.logic.Or:
                    ors.append(e2)
                else:
                    terms.append(e2)

            if verbose:
                print("terms: ", terms)

            disj = []
            for term in terms:
                name = term_to_var_name(term)
                name_alter = name + "_a" + str(curVarId)
                get_var(name)
                get_var(name_alter, term.probability)
                add_clause(clauses, name, variables[name_alter][0]) # equivalance between vars
                disj.append((name, name_alter))
            disjunctions.append((disj, None))

        elif type(clause) is problog.logic.AnnotatedDisjunction:
            # create variable for clause:
            head_name = "temp_" + str(curVarId)
            get_var(head_name)

            sum_prob = 0
            # create var for each head:
            disj = []
            for head in clause.heads:
                name = term_to_var_name(head)
                name_alter = name + "_a" + str(curVarId)
                get_var(name)
                get_var(name_alter, head.probability)
                add_clause(clauses, name, variables[name_alter][0])
                disj.append((name, name_alter))
                sum_prob += float(head.probability)

            if sum_prob < 1:
                rest = 1 - sum_prob
                name = "temp_" + str(curVarId)
                get_var(name, rest)
                disj.append((None, name))

            disjunctions.append((disj, head_name))

            if verbose:
                print("heads: ", disj)

            bodyf = parse_formula(clause.body)
            clauses[head_name] = [bodyf]
        elif type(clause) is problog.logic.Term:
            if clause.functor == "query":
                queries.append(term_to_var_name(clause.args[0]))
            elif clause.functor == "evidence":
                func = clause.args[0]
                if func.functor == '\\+':
                    evidence.append((term_to_var_name(func.args[0]), False))
                else:
                    evidence.append((term_to_var_name(func), True))
            else:
                name = term_to_var_name(clause)
                prob = clause.probability
                name_alter = name + "_a" + str(curVarId)

                if verbose:
                    print(name, prob)

                if prob is None:
                    prob = 1.0

                get_var(name)
                get_var(name_alter, prob)
                add_clause(clauses, name, variables[name_alter][0])
        if verbose:
            print()

    if verbose:
        print("varialbes: \t", variables)
        print("disjunctions: \t", disjunctions)
        print("clauses: \t", clauses)
        print("evidence: \t", evidence)
        print("queries: \t", queries)
        print()

    total = True

    # generate disjunctions:
    for disj_tuple in disjunctions:
        disj = disj_tuple[0]
        head_name = disj_tuple[1]
        head_sym = variables[head_name][0] if head_name is not None else None

        syms = [variables[x[1]][0] for x in disj]
        # add head_name to a v b v c
        ors = None
        if head_name is not None:
            ors = Or(*(syms + [~head_sym]))
        else:
            ors = Or(*syms)

        total &= ors

        l = len(syms)

        # add clauses to assert that all syms are diffrent
        for j in range(l):
            for i in range(j):
                total &= ~syms[i] | ~syms[j]

        # add clauses to make all false in case of head_name == false
        if head_sym is not None:
            for sym in syms:
                total &= head_sym | ~sym

    # add clauses:
    for head_name in clauses:
        bodies = clauses[head_name]
        ors = Or(*bodies)
        sym = variables[head_name][0]
        total &= Equivalent(sym, ors)

    if verbose:
        print("total: ", total)
        print()


    cnf_total = to_cnf(total)
    if verbose:
        print("cnf: ", cnf_total)
        print()

    # weights:
    weights = {} # var name to tuple (prob true, prob false)

    for disj in disjunctions:
        for var in disj[0]:
            alter_name = var[1]
            vtuple = variables[alter_name]
            weights[alter_name] = (float(vtuple[1]), 1)

    for var_name in variables:
        vtuple = variables[var_name]
        if var_name in weights:
            continue # disjunction

        prob = vtuple[1]
        if prob is None:
            weights[var_name] = (1, 1)
        else:
            p = float(prob)
            weights[var_name] = (p, 1 - p)

    vars = list(variables.keys())
    return vars, cnf_total, weights, evidence, queries
