import argparse
import glob
import requests
import csv
import matplotlib
import pandas

parser = argparse.ArgumentParser(description='Input a data file and see some things.')
parser.add_argument('inFile',
                    help='Input data file URL (API)')
#parser.add_argument('outFile',
#                    help='Output file')

args = parser.parse_args()
inFile = args.inFile
#outFile = args.outFile

#testData = requests.get("https://openprescribing.net/api/1.0/org_code/?q=Beaumont&format=json")

try:
	resp = requests.get(inFile)
	#print(resp.json())
	print("Good")
except:
	print("An error occured! Fuck!")



data = pandas.read_csv("test.csv") 

data.head()

'''
with open("test.csv") as inf:
	df = csv.reader(inf, delimiter=',')
	line_count = 0
	for row in df:
		if line_count == 0:
			columnNames = row
			print(columnNames)
			#print('Column names are {", ".join(row)}')
			line_count += 1
		else:
			#print(row)
			line_count += 1
	print('Processed ' + str(line_count) + ' lines.')
'''









