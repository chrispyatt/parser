# Import libraries
import argparse
import requests
import csv
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
from dateutil.parser import parse
from pandas.io.json import json_normalize
from matplotlib.cbook import boxplot_stats
import scipy
from scipy import stats
import datetime
import numpy as np
import seaborn as sns

# Specify command line arguments (including defaults for optional args)
parser = argparse.ArgumentParser(description='Input a data file (in the form of an API link) and see some summary statistics for a time period of your choice. Use the -h option for info.')
group = parser.add_mutually_exclusive_group()
parser.add_argument('-i', '--inFile', dest='inFile',
                    help='Input data file URL (API), as a list, e.g. [1] or [1, 2]')
parser.add_argument('-x', '--x_axis', dest='x_axis',
                    help='What column would you like to use (from your API data) as the x-axis?')
parser.add_argument('-y', '--y_axis', dest='y_axis',
                    help='What column would you like to use (from your API data) as the y-axis?')
parser.add_argument('-g', '--groupby', dest='groupby',
                    help='What column would you like to use (from your API data) to group the data (e.g. by practice)?')
parser.add_argument('--dateRange', dest='dateRange', default="all",
                    help='The range of dates (if x axis is time) for which to plot. Format as [date1|date2].')
parser.add_argument('--groupSubset', dest='groupSubset', default="all",
                    help='The subset of values (from the groupby) to actually plot. Format as [value1|value2|value3] etc.')
group.add_argument('--test', dest='test', action="store_true",
                    help='Run the test dataset to make sure things are working. Requires internet connection for test API. If no internet access use --testOffline instead)')
group.add_argument('--testOffline', dest='testOffline', action="store_true",
                    help='Run the offline test dataset to make sure things are working (if you have no internet access and therefore no access to the test API).')


# Set given arguments to variables to be used later.
args = parser.parse_args()
inFile = args.inFile
xarg = args.x_axis
yarg = args.y_axis
group = args.groupby
dateRange = args.dateRange
groupSubset = args.groupSubset
test = args.test
testOffline = args.testOffline


# If the test option is set to True, this will run a test analysis.
if test:
    inFile = ['https://openprescribing.net/api/1.0/spending_by_practice/?code=5.1&org=14L&format=json', 'https://openprescribing.net/api/1.0/org_details/?org_type=practice&org=14L&keys=total_list_size&format=json']
    xarg = 'date'
    yarg = 'quantity'
    group = 'row_name'
    dateRange = '2017-04-01|2018-04-01'
    groupSubset = 'all'

# If the testOffline option is set to True, this will run a test analysis without reliance on an internet connection.
if testOffline:
    inFile = ['spending-by-practice-0501.csv', 'list_size.csv']
    xarg = 'date'
    yarg = 'quantity'
    group = 'row_name'
    dateRange = '2017-04-01|2018-04-01'
    groupSubset = 'all'
    df_list = []
    for inp in inFile:
        df_list.append(pd.read_csv(inp))
    #print(df_list)
    #print(len(df_list))
    if len(df_list) > 1:
        df = df_list[0]
        del df_list[0]
        for dframe in df_list:
            df = pd.concat([df, dframe], axis=1, join='inner')
            df = df.loc[:,~df.columns.duplicated()]

else:
    # Get data from each API (& check for error codes), then merge into single dataframe.
    print('\nRetrieving data...')
    df_list = []
    for inp in inFile:
        try:
            resp = requests.get(inp)
            #print(resp.json())
            print(resp.status_code)
        except:
            print("An error occured! Please check the input API.")

        # Get nested json into flat dataframe.
        df_list.append(pd.io.json.json_normalize(resp.json()))
    
    # If df_list is longer than one, merge the dataframes one by one.
    if len(df_list) > 1:
        df = df_list[0]
        del df_list[0]
        for dframe in df_list:
            df = df.merge(dframe, how='inner')

#print(df.head)
#print(df.tail)
# Normalising yarg per 1000 patients.
print('\nNormalising ' + yarg + '...')
yarg_n = pd.Series(df[yarg]/(0.001*df['total_list_size']))
# Merging normalised yarg into whole dataframe.
df = df.merge(yarg_n.rename('yarg_n'), how='inner', left_index=True, right_index=True)


# Shows datatypes of variables.
print("\nDataframe information:")
print(df.info())
# Shows if there are any null values in the dataframe.
print("\nNumber of NULL values:")
print(df.isna().sum())

#print(df.head)
#print(df.tail)
# Subsetting the data by timepoints or by practises using dictionaries.
print('\nCreating timepoint dictionaries...')
date={}
for i in df['date']:
    date[i] = df[df['date'] == i]
prac={}
for i in df['row_name']:
    prac[i] = df['row_name'][df['row_name'] ==i]
    
    
# Extracting outliers for each time point using matplotlib.cbook's boxplot_stats, and putting it into a list.
print('\nExtracting outliers...')
outliers = []
for i in date:
    outliers.append([y for stat in boxplot_stats(date[i]['yarg_n']) for y in stat['fliers']])
# Flatten to 2D list (non nested).
flat = []
for sublist in outliers:
    for item in sublist:
        flat.append(item)
        


# Makes new column which determines if the yarg_n value is an outlier.
print('\nAssessing outliers...')
df['outlier'] = df['yarg_n'].isin(flat)

    
def plotGraphs(dataF):
    '''
    This function plots a line graph based on whatever dataframe it is given. 
    The variables plotted are the same as for the rest of the script, but possibly a subset.
    
    It will also plot boxplots of the specified Y variable over time, with and without outliers.
    '''
    # Set figure size for later plots.
    plt.figure(figsize=(24,16))
    
    # Line graph of specified columns.
    dataF.set_index(xarg, inplace=True)
    lineplot = dataF.groupby(group)[yarg].plot(legend=True)
    plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
       
    # Boxplots of normalised yarg at each timepoint showing outliers.
    boxplt = sns.catplot(x= 'date', y=yarg_n, data= df, kind = 'box')
    boxplt.fig.autofmt_xdate()
    
    # Making a dataframe with outlier values removed.
    df_noOutliers = dataF[~dataF['yarg_n'].isin(flat)]

    # Making a dataframe of the outliers only.
    df_outliersOnly = dataF[dataF['yarg_n'].isin(flat)]
    
    # Boxplots of normalised yarg at each timepoint with outliers removed.
    boxplt_clean = sns.catplot(x='date', y=yarg_n, data= df_noOutliers, kind = 'box')
    boxplt_clean.fig.autofmt_xdate()
    
    # Line plot of the normalised yarg variable over time (without outliers). SD shown as shadow behind line.
    sns.set_style('darkgrid')
    gmeans = sns.relplot(x='date', y=yarg_n, kind='line', ci='sd', data=df_noOutliers)
    gmeans.fig.autofmt_xdate()

    # Scatterplot of only the outliers.
    goutliers = sns.relplot(x='date', y=yarg_n, kind='scatter', ci='sd', data=df_outliersOnly)
    goutliers.fig.autofmt_xdate()

    # Line plot of the normalised yarg variable with outlier scatterpot overlaid. SD shown as shadow, as before.
    sns.set_style('darkgrid')
    sns.lineplot(x='date', y=yarg_n, ci='sd', data=df_noOutliers),
    sns.scatterplot(x='date', y=yarg_n, data=df_outliersOnly)
    plt.title('Mean normalised " + yarg + " per month (with outliers)')
    fig.autofmt_xdate()
    

# If both the below options are used, this will subset the dataframe by both.
if groupSubset != "all" and dateRange != "all":
    dr = dateRange.split('|')
    start = datetime.datetime.strptime(dr[0], '%Y-%m-%d')
    end = datetime.datetime.strptime(dr[1], '%Y-%m-%d')
    gS = groupSubset.split('|')
    df_both = df.loc[(pd.to_datetime(df['date']) >= start) & (pd.to_datetime(df['date']) <= end) & df[group].isin(gS)]
    plotGraphs(df_both)

# If a date range is specified, this will create a subset of the main dataframe, within the date range.
elif dateRange != "all":
    dr = dateRange.split('|')
    start = datetime.datetime.strptime(dr[0], '%Y-%m-%d')
    end = datetime.datetime.strptime(dr[1], '%Y-%m-%d')
    df_dateRange = df.loc[(pd.to_datetime(df['date']) >= start) & (pd.to_datetime(df['date']) <= end)]
    plotGraphs(df_dateRange)
    
# If a subset of the grouping option is specified, this will create a subset of the dataframe, constrained to that subset.
elif groupSubset != "all":
    gS = groupSubset.split('|')
    df_groupSubset = df.loc[df[group].isin(gS)]
    plotGraphs(df_groupSubset)
    
# Plot xarg against yarg, grouped by group (no subset).
else:
    plotGraphs(df)

#Display the graphs.
print('Displaying graphs...')
plt.show()

input()
