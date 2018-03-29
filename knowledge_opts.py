#!/usr/bin/python3

import sys
import subprocess

MINIC2D_PATH = "../miniC2D-1.0.0/bin/linux/miniC2D"

cnf_paths = [
    'enc1_c2d_cancer',
    'enc2_c2d_cancer',
    'c2d_montyhall'
]

opts_1 = ['p', 'i']

for cnf_path in cnf_paths:
    min_nodes = 100000
    min_edges = 100000
    min_nodes_opts = None
    min_edges_opts = None
    for opt in opts_1:
        for m in range(5):
            cnf_tot_path = 'cnf/' + cnf_path + '.cnf'
            vtree_path = 'vtree/' + cnf_path + '_' + opt + '_' + str(m) + '.vtree'

            mc2d = subprocess.run([MINIC2D_PATH,
                '-t', opt,
                '-m', str(m),
                '-c', cnf_tot_path,
                '-o', vtree_path],
                stdout=subprocess.PIPE)

            if mc2d.returncode != 0:
                print("error running miniC2D")
                sys.exit(-1)

            output = mc2d.stdout.decode().splitlines()

            for line in output:
                spl = line.split()
                if len(spl) != 2:
                    continue
                if spl[0] == 'Nodes':
                    nodes = int(spl[1])
                    if nodes < min_nodes:
                        min_nodes = nodes
                        min_nodes_opts = (opt, m)
                elif spl[0] == 'Edges':
                    edges = int(spl[1])
                    if edges < min_edges:
                        min_edges = edges
                        min_edges_opts = (opt, m)
                    break
    print(cnf_path)
    print("min nodes:", min_nodes, "opts:", min_nodes_opts)
    print("min edges:", min_edges, "opts:", min_edges_opts)
    print("----")