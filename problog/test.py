import problog
import sympy

factory = problog.program.PrologFactory()
parser = problog.parser.PrologParser(factory)

parsedFile = parser.parseFile('montyhall.pl')
ground = problog.engine.ground_default(parsedFile)

print("grounded file:")
print(ground)
print("")

formulas = []
idw = {}
idn = {}

var = 'a'

for node in ground:
    id = node[0]
    formula = node[1]

    # atom type formula
    if type(formula) == problog.formula.atom:
        prob = formula[1]
        idw[id] = 1 if (prob == True) else float(prob)
        idn[id] = var
        var = chr(ord(var)+1)

    # conjunction type formula
    elif type(formula) == problog.formula.conj:
        children = formula[0]
        transformed = []

        idn[id] = var

        for child in children:
            transformedChild = sympy.Not(sympy.symbols(idn[int(str(child)[1:])])) if (str(child)[0] == '-') else sympy.symbols(idn[child])
            transformed.append(transformedChild)

        print(transformed)
        print(idn)
        formulas.append(sympy.And(*transformed))
        formulas.append(sympy.Equivalent(sympy.symbols(var), sympy.And(*transformed)))
        var = chr(ord(var) + 1)

    # disjunction type formula
    elif type(formula) == problog.formula.disj:
        children = formula[0]
        transformed = []

        children = formula[0]
        transformed = []

        idn[id] = var

        for child in children:
            transformedChild = sympy.Not(sympy.symbols(idn[int(str(child)[1:])])) if (str(child)[0] == '-') else sympy.symbols(idn[child])
            transformed.append(transformedChild)

        print(transformed)
        print(idn)
        formulas.append(sympy.Or(*transformed))
        formulas.append(sympy.Equivalent(sympy.symbols(var), sympy.Or(*transformed)))
        var = chr(ord(var) + 1)


result = sympy.And(*formulas)
print(result)

cnf = sympy.to_cnf(result, True)
print(cnf)
