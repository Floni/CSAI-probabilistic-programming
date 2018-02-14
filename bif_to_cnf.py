import sys
import itertools

from deps.bif_parser import BIFParser as BIFP

def notOfAnds(ands):
    return ['-' + x for x in ands]

def convImplToCnf(left, right):
    if len(right) > 1:
        return [convImplToCnf(left, [r])[0] for r in right]
    else:
        return [notOfAnds(left) + right]

def convEqToCnf(left, right):
    impl1 = convImplToCnf(left, right)
    impl2 = convImplToCnf(right, left)
    return impl1 + impl2

def cnfToInts(cnf, vs):
    ret = ""
    for conj in cnf:
        line = ""
        for disj in conj:
            if disj[0] == '-':
                line += str(-vs[disj[1:]])
            else:
                line += str(vs[disj])
            line += " "
        line += "0\n"
        ret += line
    return ret

def enc1(nodes):
    cnf = []
    for node in nodes:
        name = node.getName()
        states = node.getStates()
        parents = node.getParents()
        svars = [name + '.v.' + s for s in states]

        cnf.append(list(svars))
        l = len(svars)
        for j in range(l):
            for i in range(j):
                cnf.append(['-' + svars[i], '-' + svars[j]])

        cond_list = [states]
        for parent in parents:
            cond_list.append(parent.getStates())
        pairs = itertools.product(*cond_list)
        
        pnames = [name] + [p.getName() for p in parents]

        for pair in pairs:
            rl = name + '.cv.' + '|'.join(pair)
            ll = [pnames[i] + '.v.' + s for i, s in enumerate(pair)]
            #print(convEqToCnf(ll, [rl]))
            cnf += convEqToCnf(ll, [rl])    
    return cnf


def enc2(nodes):
    cnf = []
    for node in nodes:
        name = node.getName()
        states = node.getStates()
        parents = node.getParents()
        svars = [name + '.v.' + s for s in states]

        cnf.append(list(svars))
        l = len(svars)
        for j in range(l):
            for i in range(j):
                cnf.append(['-' + svars[i], '-' + svars[j]])

        cond_list = [states]
        for parent in parents:
            cond_list.append(parent.getStates())
        pairs = itertools.product(*cond_list)
        
        pnames = [name] + [p.getName() for p in parents]

        for pair in pairs:
            if pair[0] == states[-1]:
            else:
                ll = [pnames[i] + '.v.' + s for i, s in enumerate(pair)]
            #rl = name + '.cv.' + '|'.join(pair)
            #ll = [pnames[i] + '.v.' + s for i, s in enumerate(pair)]
            #print(convEqToCnf(ll, [rl]))
            #cnf += convEqToCnf(ll, [rl])    
        
    return cnf

def main():
    if len(sys.argv) != 3:
        print("USAGE: ", sys.argv[0], " bif-file cnf-out-file")
        return -1

    bif_file_name = sys.argv[1]
    cnf_file_name = sys.argv[2]
    
    enc1 = False

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
    # map from name to int?
    variables = {}
    nvars = 0
    for node in nodes:
        name = node.getName()
        states = node.getStates()
        
        # each state gets one variable
        svars = [name + '.v.' + s for s in states]

        parents = node.getParents()
        # per state and state of each parent -> one variable
        if enc1:
            cond_list = [states]
        else:
            cond_list = [states[:-1]]        
        for parent in parents:
            cond_list.append(parent.getStates())

        pairs = itertools.product(*cond_list)
        pvars = [name + '.cv.' + '|'.join(p) for p in pairs]

        for v in svars + pvars:
            variables[v] = nvars + 1
            nvars += 1

    print("variables:")
    for v in variables:
        print(v, "=", variables[v])

    # create cnf
    
    cnf = enc1(nodes) if enc1 else enc2(nodes)
            
    print("cnf:")
    for c in cnf:
        print(c)

    # assign weights
    weights = {}
    for node in nodes:
        name = node.getName()
        states = node.getStates()
        parents = node.getParents()

        cond_list = [states]
        for parent in parents:
            cond_list.append(parent.getStates())
        pairs = itertools.product(*cond_list)
        
        cpd = node.getDist()

        for pair in pairs:
            var_name = name + '.cv.' + '|'.join(pair)
            prob = cpd[pair]
            weights[var_name] = prob
    print("weights:")
    print(weights)
    # save cnf
    
    with open(cnf_file_name, "w") as f:
        f.write("c " + cnf_file_name + "\n")
        f.write("c " + bif_file_name + "\n")
        f.write("c\n")
        
        f.write("p cnf " + str(nvars) + " " + str(len(cnf)) + "\n")
        

        ws = {}
        for var in variables:
            if var in weights:
                ws[variables[var]] = (weights[var], 1)
            else:
                ws[variables[var]] = (1, 1)
                #f.write("w " + str(variables[var]) + " -1\n")
        wline = "c weights"
        for i in range(nvars):
            wline += " " + str(ws[i+1][0]) + " " + str(ws[i+1][1])
        f.write(wline + "\n")
        f.write(cnfToInts(cnf, variables))
    return 0


if __name__ == '__main__':
    sys.exit(main())
