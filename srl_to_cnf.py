#!/usr/bin/python3

import sys
import argparse
import subprocess

def main():
    print("test")
    parser = argparse.ArgumentParser(description="srl to CNF")
    parser.add_argument("pl_file")
    parser.add_argument("cnf_file")

    args = parser.parse_args()

    pl_file_name = args.pl_file
    cnf_file_name = args.cnf_file

    grounded = subprocess.Popen(['problog', 'ground', pl_file_name])

    print(grounded)

    return 0


if __name__ == '__main__':
    sys.exit(main())
