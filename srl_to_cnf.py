#!/usr/bin/python3

import sys
import argparse
import subprocess
import problog
import sympy

from sympy.logic.boolalg import Not, And, Or, Equivalent, to_cnf

def term_to_var_name(term):
    return term.functor + '_' + '_'.join(map(str, term.args))


def parse_formula(variables, formula):
    if type(formula) is problog.logic.Term:
        name = term_to_var_name(formula)
        if name not in variables:
            raise Exception("Unknown variable: " + name)
        return variables[name][0] # symbol of varialble
    elif type(formula) is problog.logic.And:
        f1 = parse_formula(variables, formula.op1)
        f2 = parse_formula(variables, formula.op2)
        return f1 & f2
    elif type(formula) is problog.logic.Or:
        f1 = parse_formula(variables, formula.op1)
        f2 = parse_formula(variables, formula.op2)
        return f1 | f2
    elif type(formula) is problog.logic.Not:
        f1 = parse_formula(variables, formula.child)
        return ~f1
    else:
        raise Exception("unknown formula: " + str(formula))

def main():
    parser = argparse.ArgumentParser(description="srl to CNF")
    parser.add_argument("pl_file")
    parser.add_argument("cnf_file")

    args = parser.parse_args()

    pl_file_name = args.pl_file
    cnf_file_name = args.cnf_file

    #grounded = subprocess.Popen(['problog', 'ground', pl_file_name],stdout=subprocess.PIPE)
    #grounded_str = grounded.stdout.read().decode()
    grounded_str = ""

    # TODO: first variable pass and then built clauses as order isn't preserved
    with open(pl_file_name, "r") as f:
        grounded_str = f.read()

    factory = problog.program.PrologFactory()
    parser = problog.parser.PrologParser(factory)
    parsed = parser.parseString(grounded_str)

    clauses = {} # map of name to list of formulas, which need to be ored

    disjunctions = [] # list of disjunctions: list of list of var names that are xor [['a1', 'a2'], ['b1', 'b2', 'b3']]
    variables = {} # map of var_name to (sym, prob or None, id)
    curVarId = 1

    for clause in parsed:
        print(type(clause))
        print(clause)

        if type(clause) is problog.logic.Clause:
            head = clause.head
            print(head)
            head_name = term_to_var_name(head)

            body = clause.body
            print(body)
            print(type(body))

            bform = parse_formula(variables, body)

            if head_name in clauses:
                clauses[head_name].append(bform)
            else:
                if head_name not in variables:
                    sym = sympy.symbols(head_name)
                    variables[head_name] = (sym, head.probability, curVarId)
                    curVarId += 1
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

            print("terms: ", terms)

            disj = []
            for term in terms:
                name = term_to_var_name(term)
                sym = sympy.symbols(name)
                variables[name] = (sym, term.probability, curVarId)
                curVarId += 1
                disj.append(name)
            disjunctions.append((disj, None))

        elif type(clause) is problog.logic.AnnotatedDisjunction:
            # create variable for clause:
            head_name = "temp_" + str(curVarId)
            sym = sympy.symbols(head_name)
            variables[head_name] = (sym, None, curVarId)
            curVarId += 1

            # create var for each head:
            disj = []
            for head in clause.heads:
                name = term_to_var_name(head)
                sym = sympy.symbols(name)
                variables[name] = (sym, head.probability, curVarId)
                curVarId += 1
                disj.append(name)
            disjunctions.append((disj, head_name))

            print("heads: ", disj)

            bodyf = parse_formula(variables, clause.body)
            clauses[head_name] = [bodyf]
        elif type(clause) is problog.logic.Term:
            if clause.functor == "query" or clause.functor == "evidence":
                # TODO
                pass
            else:
                name = term_to_var_name(clause)
                sym = sympy.symbols(name)
                variables[name] = (sym, clause.probability, curVarId)
                curVarId += 1
        print()

    print("varialbes: \t", variables)
    print("disjunctions: \t", disjunctions)
    print("clauses: \t", clauses)
    print()

    total = True

    disj_names = set()

    # TODO: if sum(prob) < 1 -> add variable to disjunction with remaining prob
    # generate disjunctions:
    for disj_tuple in disjunctions:
        disj = disj_tuple[0]
        head_name = disj_tuple[1]
        head_sym = variables[head_name][0] if head_name is not None else None

        for name in disj:
            disj_names.add(name)

        syms = [variables[x][0] for x in disj]
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
        if head_name in disj_names:
            total &= ors >> sym
        else:
            total &= Equivalent(sym, ors)

    print("total: ", total)
    print()


    cnf_total = to_cnf(total)
    print("cnf: ", cnf_total)
    print()

    # to string:
    cnf_clauses = list(cnf_total.args)
    nclauses = len(cnf_clauses)
    nvariables = curVarId - 1 # starts at one

    cnf_str = ''

    for clause in cnf_clauses:
        lits = clause.args
        for lit in lits:
            name = ''
            if type(lit) is Not:
                name = lit.args[0].name
                cnf_str += '-'
            else:
                name = lit.name
            idv = variables[name][2]
            cnf_str += str(idv) + ' '

        cnf_str += '0\n'

    # weights:
    weights = {} # var id to tuple (prob true, prob false)
    for disj in disjunctions:
        for var in disj[0]:
            vtuple = variables[var]
            weights[vtuple[2]] = (float(vtuple[1]), 1)

    for var_name in variables:
        vtuple = variables[var_name]
        vid = vtuple[2]
        if vid in weights:
            continue # disjunction
        prob = vtuple[1]
        if prob is None:
            weights[vid] = (1, 1)
        else:
            p = float(prob)
            weights[vid] = (p, 1 - p)

    weights_str = ''
    for vid in weights:
        weights_str += 'w ' + str(vid) + ' ' + str(weights[vid][0]) + ' ' + str(weights[vid][1]) + '\n'

    with open(cnf_file_name, 'w') as f:
        f.write('c ' + str(cnf_file_name) + '\n')
        f.write('c ' + str(pl_file_name) + '\n')
        f.write('c \n')
        f.write('p cnf ' + str(nvariables) + ' ' + str(nclauses) + '\n')
        f.write(weights_str)
        f.write(cnf_str)

    return 0


if __name__ == '__main__':
    sys.exit(main())
