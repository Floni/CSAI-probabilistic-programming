import sys
import itertools

from deps.bif_parser import BIFParser as BIFP

def main():
    if len(sys.argv) != 3:
        print("USAGE: ", sys.argv[0], " bif-file cnf-out-file")
        return -1

    bif_file_name = sys.argv[1]
    cnf_file_name = sys.argv[2]
    
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
        cond_list = [states]
        for parent in parents:
            cond_list.append(parent.getStates())

        pairs = itertools.product(*cond_list)
        pvars = [name + '.cv.' + '|'.join(p) for p in pairs]

        for v in svars + pvars:
            variables[v] = nvars
            nvars += 1
    
    print("variables:")
    for v in variables:
        print(v, "=", variables[v])

    # create cnf
    # assign weights
    # save cnf

    return 0


if __name__ == '__main__':
    sys.exit(main())
