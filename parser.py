import argparse
import requests
import csv
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
from dateutil.parser import parse
from pandas.io.json import json_normalize

# Specify command line arguments (including defaults for optional args)
parser = argparse.ArgumentParser(description='Input a data file and see some things. Either specify the API and columns for analysis here (see options below) or run parser with no options and input when asked.')
parser.add_argument('--inFile', dest='inFile', default="",
                    help='Input data file URL (API)')
parser.add_argument('--x_axis', dest='x_axis', default="",
                    help='What column would you like to use (from your API data) as the x-axis?')
parser.add_argument('--y_axis', dest='y_axis', default="",
                    help='What column would you like to use (from your API data) as the y-axis?')
parser.add_argument('--groupby', dest='groupby', default="",
                    help='What column would you like to use (from your API data) to group the data (e.g. by practice)?')
parser.add_argument('--dateRange', dest='dateRange', default="all",
                    help='The range of dates (if x axis is time) for which to plot. Format as [date1|date2].')
parser.add_argument('--groupSubset', dest='groupSubset', default="all",
                    help='The subset of values (from the groupby) to actually plot. Format as [value1|value2|value3] etc.')
parser.add_argument('--test', dest='test', default='False',
                    help='Run the test dataset to make sure things are working.')

# Set given arguments to variables to be used later.
args = parser.parse_args()
inFile = args.inFile
xarg = args.x_axis
yarg = args.y_axis
group = args.groupby
dateRange = args.dateRange
groupSubset = args.groupSubset
test = args.test


# If the test option is set to True, this will run a test analysis.
if test == 'True':
	inFile = 'https://openprescribing.net/api/1.0/spending_by_practice/?code=5.1&org=14L&format=json'
	xarg = 'date'
	yarg = 'quantity'
	group = 'row_name'
	dateRange = '2017-04-01|2018-04-01'
	groupSubset = 'all'

def getAPIresponse(search):
	'''
	Get data from API (& check for error codes).
	'''
	try:
		resp = requests.get(inFile)
		#print(resp.json())
		print(resp.status_code)
		if str(resp.status_code) != "200":
			print('An error occured. Please check the API')
			exit(1)
		else: return resp
	except:
		print("An error occured! Fuck!")
		exit(1)

# If no arguments given at the command line, ask for user input. Start with API interrogation.
if inFile == "":
	searchTerms = ""
	inp = input("What CCG would you like to look at?: ")
	print(getAPIresponse('/api/1.0/org_code/?q=' + inp))


	inFile = 'https://openprescribing.net/api/1.0/spending_by_practice/?' + searchTerms	
	resp = getAPIresponse(inFile)	

# Continue getting user input.
if xarg == "":
	xarg = input("Please enter the column to plot on the x-axis: ")
if yarg == "":
	yarg = input("Please enter the column to plot on the y-axis: ")
if group == "":
	group = input("Please enter the column by which you'd like to group the plot data (e.g. practice): ")
if dateRange == "":
	dateRange = input("Please enter a date range in the format [date1|date2], or type [all] for all dates: ")
if groupSubset == "":
	groupSubset = input("Please enter a subset (list of values in format [one|two|three]) or type [all] for all values: ")


resp = getAPIresponse(inFile)


# Get nested json into flat dataframe.
df = pd.io.json.json_normalize(resp.json())


def plotGraph(dataF):
	'''
	This function plots a line graph based on whatever dataframe it is given. The variables plotted are the same as for the rest of the script, but possibly a subset.
	'''
	dataF.set_index(xarg, inplace=True)
	dataF.groupby(group)[yarg].plot(legend=True)
	plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))

# If both the below options are used, this will subset the dataframe by both.
if groupSubset != "all" and dateRange != "all":
	dr = dateRange.split('|')
	start = datetime.strptime(dr[0], '%Y-%m-%d')
	end = datetime.strptime(dr[1], '%Y-%m-%d')
	gS = groupSubset.split('|')
	df_both = df.loc[(pd.to_datetime(df['date']) >= start) & (pd.to_datetime(df['date']) <= end) & df[group].isin(gS)]
	plotGraph(df_both)

# If a date range is specified, this will create a subset of the main dataframe, within the date range.
elif dateRange != "all":
	dr = dateRange.split('|')
	start = datetime.strptime(dr[0], '%Y-%m-%d')
	end = datetime.strptime(dr[1], '%Y-%m-%d')
	df_dateRange = df.loc[(pd.to_datetime(df['date']) >= start) & (pd.to_datetime(df['date']) <= end)]
	plotGraph(df_dateRange)
	
# If a subset of the grouping option is specified, this will create a subset of the dataframe, constrained to that subset.
elif groupSubset != "all":
	gS = groupSubset.split('|')
	df_groupSubset = df.loc[df[group].isin(gS)]
	plotGraph(df_groupSubset)
	
# Plot xarg against yarg, grouped by group (no subset).
else:
	plotGraph(df)

#Display the graph.
plt.show()











