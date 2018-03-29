# CSAI-probabilistic-programming Assignment

## Installing

The requirements are listed in requirements.txt and can be installed using pip:

`pip install -r requirements.txt`

pySdd may need to be compiled seperatly,
the source can be found at: https://github.com/wannesm/PySDD

For creating the vtree MiniC2D is used.
It can be found at: http://reasoning.cs.ucla.edu/minic2d/
After compiling the path to the miniC2D executable must be specified
in the MINIC2D_PATH variable in pipeline.py

For model counting using cachet a custom version must be used
that supports both negative and positive weights.
It can be found at: https://github.com/timower/cachet-fix

## Usage

```
usage: pipeline.py [-h] [--bif-file BIF_FILE] [--pl-file PL_FILE] [--enc ENC]
                   [--cnf-type CNF_TYPE] [--verbose]
                   cnf_file

problog pipeline

positional arguments:
  cnf_file              The output cnf file

optional arguments:
  -h, --help            show this help message and exit
  --bif-file BIF_FILE, -b BIF_FILE
                        The input bayesian network
  --pl-file PL_FILE, -p PL_FILE
                        The input problog file
  --enc ENC, -e ENC     The enc type 1 or 2
  --cnf-type CNF_TYPE, -c CNF_TYPE
                        The type of cnf file to output (c2d for minic2d or
                        cachet)
  --verbose, -v         Verbose output
```

The pipeline needs either a bif Bayesian network or a problog file as input using
the -b or -p parameters. For Bayesian networks the encoding can be specified using the
-e parameter.

The output cnf file needs to be specified as the last parameter.
The format of the weights encoded in cnf can be specified using the -c paramter.
This is either c2d for miniC2D and SDD or cachet.

If MiniC2D is used as output format (the default),
MiniC2D is executed automaticly to generate a vtree saved as (`cnf_file_name.vtree`).
Weighted model counting using pySDD is also performed.

The verbose option can be used to get more information about parsing
and weight generation.

## Examples

Compute the enc1 encoding of the cancer Bayesian network:

`./pipeline.py -e 1 -c c2d -b ./bif/cancer.bif output.cnf`

Compute the enc2 encoding of the cancer network for cachet:

`./pipeline.py -e 2 -c cachet -b ./bif/cancer.bif output.cnf`

Compute the cnf encoding and queries of the monyhall problog file:

`./pipeline.py -p ./problog/montyhall.pl output.cnf`
