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

    grounded = subprocess.Popen(['problog', 'ground', pl_file_name],stdout=subprocess.PIPE)
    grounded_str = grounded.stdout.read().decode()

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
            disjunctions.append(disj)

        elif type(clause) is problog.logic.AnnotatedDisjunction:
            # create var for each head:
            disj = []
            for head in clause.heads:
                name = term_to_var_name(head)
                sym = sympy.symbols(name)
                variables[name] = (sym, head.probability, curVarId)
                curVarId += 1
                disj.append(name)
            disjunctions.append(disj)

            print("heads: ", vars)

            bodyf = parse_formula(variables, clause.body)
            # add clause for each head:
            for name in disj:
                clauses[name] = [bodyf]

        print()

    print("varialbes: \t", variables)
    print("disjunctions: \t", disjunctions)
    print("clauses: \t", clauses)
    print()

    total = True

    # generate disjunctions:
    for disj in disjunctions:
        syms = [variables[x][0] for x in disj]
        ors = Or(*syms)

        total &= ors

        l = len(syms)

        for j in range(l):
            for i in range(j):
                total &= ~syms[i] | ~syms[j]

    # add clauses:
    for head_name in clauses:
        bodies = clauses[head_name]
        ors = Or(*bodies)
        sym = variables[head_name][0]

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

    cnf_str = 'p cnf ' + str(nvariables) + ' ' + str(nclauses) + '\n'

    for clause in cnf_clauses:
        lits = clause.args
        for lit in lits:
            name = ''
            n = False
            if type(lit) is Not:
                name = lit.args[0].name
                cnf_str += '-'
            else:
                name = lit.name
            idv = variables[name][2]
            cnf_str += str(idv) + ' '

        cnf_str += '0\n'

    with open(cnf_file_name, 'w') as f:
        f.write('c ' + str(cnf_file_name) + '\n')
        f.write('c ' + str(pl_file_name) + '\n')
        f.write('c \n')
        f.write(cnf_str)

    return 0


if __name__ == '__main__':
    sys.exit(main())
