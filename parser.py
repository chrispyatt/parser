from sys import argv
import argparse
import glob
import re
import itertools
from collections import defaultdict


parser = argparse.ArgumentParser(description='Input a directory containing (in subdirectories for each strain) sequence files for cluster genes.')
parser.add_argument('inputDir',
                    help='Directory containing ONLY MapCoordinates.py output files (FASTA files of gene sequences). These can be in subdirectories if multiple strains.')
parser.add_argument('outputFile',
                    help='Desired name of output .txt file (saves to current working directory unless full path specified).')
parser.add_argument('clusterLength',
                    help='The number of genes in the complete cluster.')

args = parser.parse_args()
inputDir = args.inputDir
outputFile = args.outputFile
clusterLength = int(args.clusterLength)
