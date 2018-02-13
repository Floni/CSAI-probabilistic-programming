import sys

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

    return 0


if __name__ == '__main__':
    sys.exit(main())
