#!/usr/bin/python3

import sys
import argparse
import subprocess
import problog
import sympy


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

    var = 'a'
    formulas = []
    idw = {}
    nid = {}

    for clause in parsed:
        print(type(clause))
        print(clause)

        if type(clause) is problog.logic.Clause:
            head = clause.head
            print(head)
            cvar = ""
            key = str(head.functor) + str(head.args)
            if nid.__contains__(key):
                cvar = nid.get(key)
            else:
                cvar = var
                nid[key] = var
                var = chr(ord(var) + 1)

            body = clause.body
            print(body)
            print(type(body))

            bparts = [body]
            conj = []

            if type(body) is problog.logic.Term:
                #TODO: Add head body relationship
                #TODO: handle not's
                print("body is single term")
            else:
                #conjunction
                while len(bparts) > 0:
                    cur_par = bparts.pop()
                    e1 = cur_par.op1
                    e2 = cur_par.op2

                    if type(e1) is problog.logic.And:
                        bparts.append(e1)
                    else:
                        # type must be term -> add to conjunction
                        key = str(e1.functor) + str(e1.args)
                        cvar = ""
                        if nid.__contains__(key):
                            cvar = nid[key]
                        else:
                            nid[key] = var
                            cvar = var
                            var = chr(ord(var) + 1)
                        conj.append(sympy.symbols(cvar))

                    if type(e2) is problog.logic.And:
                        bparts.append(e2)
                    else:
                        # type must be term -> add to conjunction
                        key = str(e2.functor) + str(e2.args)
                        cvar = ""
                        if nid.__contains__(key):
                            cvar = nid[key]
                        else:
                            nid[key] = var
                            cvar = var
                            var = chr(ord(var) + 1)
                        conj.append(sympy.symbols(cvar))

                print(conj)

            #Add head body relationship


        elif type(clause) is problog.logic.Or:
            # disjunction with probabilities
            disj = []
            ors = [clause]
            while len(ors) > 0:
                cur_or = ors.pop()
                e1 = cur_or.op1
                e2 = cur_or.op2

                if type(e1) is problog.logic.Or:
                    ors.append(e1)
                else:
                    # type must be term -> add to disjunction
                    disj.append(sympy.symbols(var))
                    idw[var] = e1.probability
                    nid[str(e1.functor) + str(e1.args)] = var
                    var = chr(ord(var) + 1)

                if type(e2) is problog.logic.Or:
                    ors.append(e2)
                else:
                    # type must be term -> add to disjunction
                    disj.append(sympy.symbols(var))
                    idw[var] = e2.probability
                    nid[str(e2.functor) + str(e2.args)] = var
                    var = chr(ord(var) + 1)

            #TODO: exclusive OR of all values of the variable in the disjunction (like enc1)
            formula = sympy.Or(*disj)
            formulas.append(formula)

        elif type(clause) is problog.logic.AnnotatedDisjunction:
            a = 1

        print()

    print(nid)
    print(idw)
    print(formulas)
    return 0


if __name__ == '__main__':
    sys.exit(main())
