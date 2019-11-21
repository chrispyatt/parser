import argparse
import glob
import requests
import csv
import matplotlib.pyplot as plt
import pandas as pd
import json
from pandas.io.json import json_normalize


parser = argparse.ArgumentParser(description='Input a data file and see some things.')
parser.add_argument('inFile',
                    help='Input data file URL (API)')
#parser.add_argument('outFile',
#                    help='Output file')

args = parser.parse_args()
inFile = args.inFile
#outFile = args.outFile

#testData = requests.get("https://openprescribing.net/api/1.0/org_code/?q=Beaumont&format=json")
#https://openprescribing.net/api/1.0/org_details/?org_type=practice&org=14L

try:
	resp = requests.get(inFile)
	
	#print(resp.json())
	print("Good")
except:
	print("An error occured! Fuck!")


#df = pd.DataFrame(resp.json())

df = pd.io.json.json_normalize(resp.json())

#print(list(df.columns.values))

#df2 = df['star_pu'].apply(pd.Series)
#df3 = pd.concat([df, df2], sort=False, join='inner')

#print(df3)
#print(list(df3.columns.values))
#print(df3['date'])

#df.plot(x='date', y='female_0_4')

df.set_index('date', inplace=True)
df.groupby('row_name')['star_pu.oral_antibacterials_item'].plot(legend=True)

plt.show()








