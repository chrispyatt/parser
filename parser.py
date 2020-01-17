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
from bokeh.plotting import figure, show, output_notebook, output_file, ColumnDataSource
from bokeh.models import HoverTool

# Specify command line arguments (including defaults for optional args)
parser = argparse.ArgumentParser(description='''Input a data file (in the form of an API link) and see some summary statistics for a time period of your choice. Use the -h option for info.
                                                \n
                                                Authors: Chris Pyatt & Simon Lam''')
group = parser.add_mutually_exclusive_group()
parser.add_argument('-i', '--inFile', dest='inFile', default=None,
                    help='''Input data file URL (API) as a list encased in double-quotes and separated by single spaces, e.g. \"1\" or \"1 2\", etc. 
                    Failure to encase in quotes may result in parts of the URL being interpreted as commands.''')
parser.add_argument('-x', '--x_axis', dest='x_axis', default=None,
                    help='''What column would you like to use (from your API data) as the x-axis?''')
parser.add_argument('-y', '--y_axis', dest='y_axis', default=None,
                    help='''What column would you like to use (from your API data) as the y-axis?''')
parser.add_argument('-g', '--groupby', dest='groupby', default=None,
                    help='''What column would you like to use (from your API data) to group the data (e.g. by practice)?''')
parser.add_argument('--dateRange', dest='dateRange', default="all",
                    help='''The range of dates (if x axis is time) for which to plot. Format as [date1|date2].''')
parser.add_argument('--groupSubset', dest='groupSubset', default="all",
                    help='''The subset of values (from the groupby) to actually plot. Format as [value1|value2|value3] etc.''')
group.add_argument('--test', dest='test', action="store_true",
                    help='''Run the test dataset to make sure things are working. Requires internet connection for test API. You can supply other options if you wish, but they will be overridden. 
                    If no internet access use --testOffline instead).''')
group.add_argument('--testOffline', dest='testOffline', action="store_true",
                    help='''Run the offline test dataset to make sure things are working (if you have no internet access and therefore no access to the test API). 
                    You can supply other options if you wish, but they will be overridden. 
                    Bear in mind that this tests whether something is plotted, but is not useful data in itself.''')
parser.add_argument('--plots', dest='plots', choices=['1','2','3','4'], default='4',
                    help='''Choose which plots you\'d like to display. Option 1 will display a line graph of your chosen variables 
                    (this can be unwieldy with larger datasets so we advise only using this plot for smaller subsets). 
                    Option 2 will display boxplots and line graphs showing outliers and standard deviation. 
                    Option 3 will display an interactive graph of the same information as option 2, with mouse-over functionality.
                    Option 4 will display all of the above (this is the default behaviour).''')


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
plots = args.plots


def checkOptions():
    if inFile != None and xarg != None and yarg != None and group != None:
        return True
    else:
        return False


# If the test option is set to True, this will run a test analysis.
if test:
    inFile = 'https://openprescribing.net/api/1.0/spending_by_practice/?code=5.1&org=14L&format=json https://openprescribing.net/api/1.0/org_details/?org_type=practice&org=14L&keys=total_list_size&format=json'
    xarg = 'date'
    yarg = 'quantity'
    group = 'row_name'
    dateRange = '2017-04-01|2018-04-01'
    groupSubset = 'all'
    plots = '4'
    

# If the testOffline option is set to True, this will run a test analysis without reliance on an internet connection This messes up the dataframe a bit but the point is to test whether the program plots something..
if testOffline:
    inFile = 'spending-by-practice-0501.csv list_size.csv'
    xarg = 'date'
    yarg = 'quantity'
    group = 'row_name'
    dateRange = '2017-04-01|2018-04-01'
    groupSubset = 'all'
    plots = '4'
    df_list = []
    for inp in inFile.split(" "):
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
    # Check required command line options have been given.
    if checkOptions() != True:
        exit('\nPlease supply options using [-i], [-x], [-y], and [-g]. Otherwise use [--test] or [--testOffline] to test the program, or [-h] to see the user manual.')
    
    # Get data from each API (& check for error codes), then merge into single dataframe.
    print('\nRetrieving data...')
    df_list = []
    for inp in inFile.split(" "):
        try:
            resp = requests.get(inp)
            #print(resp.json())
            print(resp.status_code)
        except:
            exit("\nAn error occured! Please check the input API.")

        # Get nested json into flat dataframe.
        df_list.append(pd.io.json.json_normalize(resp.json()))
    
    # If df_list is longer than one, merge the dataframes one by one.
    if len(df_list) > 1:
        df = df_list[0]
        del df_list[0]
        for dframe in df_list:
            df = df.merge(dframe, how='inner')


# Normalising yarg per 1000 patients.
print('\nNormalising ' + yarg + '...')
yarg_n = pd.Series(df[yarg]/(0.001*df['total_list_size']))
# Merging normalised yarg into whole dataframe.
norm = 'normalised_' + yarg
df = df.merge(yarg_n.rename(norm), how='inner', left_index=True, right_index=True)


# Shows datatypes of variables.
print("\nDataframe information:")
print(df.info())
# Shows if there are any null values in the dataframe.
print("\nNumber of NULL values:")
print(df.isna().sum())


# Subsetting the data by timepoints using dictionaries.
print('\nCreating timepoint dictionaries...')
date={}
for i in df['date']:
    date[i] = df[df['date'] == i]
    
    
def plotLine(dataF):
    '''
    This function plots a line graph based on whatever dataframe it is given. 
    The variables plotted are the same as for the rest of the script, but possibly a subset.
    This can be difficult to interpret if given a very large dataset as it is plotting the raw data.
    '''
    # Line graph of specified columns.
    dataF.set_index(xarg, inplace=True)
    lineplot = dataF.groupby(group, as_index=False)[yarg].plot(legend=True)
    plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
    dataF.reset_index(inplace=True)
    
    return


def outlierDF(dataF, subs):
    '''
    This function takes a dataframe and a subset dictionary and returns (a) a subset with outliers removed, and (b) only the outliers, both as dataframes.
    '''
    # Making local copy of dataframe (to avoid changing input).
    df_local = dataF.copy()
    
    # Extracting outliers for each time point using matplotlib.cbook's boxplot_stats, and putting it into a list.
    print('\nExtracting outliers...')
    outliers = []
    for i in subs:
        outliers.append([y for stat in boxplot_stats(subs[i][norm]) for y in stat['fliers']])
        
    # Flatten to 2D list (non nested).
    flat = []
    for sublist in outliers:
        for item in sublist:
            flat.append(item)
            
    # Makes new column which determines if the yarg_n value is an outlier.
    print('\nAssessing outliers...')
    df_local['outlier'] = df_local[norm].isin(flat)
    
    # Make a list of dataframes, one with outliers removed, one with only outliers.
    outDFs = []
    # Making a dataframe of the outliers only.
    outDFs.append(df_local[df_local[norm].isin(flat)])
    # Making a dataframe with outlier values removed.
    outDFs.append(df_local[~df_local[norm].isin(flat)])
    
    return outDFs


def getDFstats(dataF):
    '''
    This function takes a dataframe and calculates some basic statistics for use in plotting, in the form of another dataframe.
    '''
    # Making a dataframe of general stats of the data.
    dfstats = dataF.groupby('date')[norm].describe().reset_index()

    # Convert data type for the date column into datetime.
    dfstats['date'] = pd.to_datetime(dfstats['date'])

    # Create columns for 1std over and under the mean.
    dfstats['1std.over']=(dfstats['mean'] + dfstats['std'])
    dfstats['1std.under']=(dfstats['mean'] - dfstats['std'])
    
    return dfstats


def plotBoxes(dataF):
    '''
    This function takes a dataframe and will plot boxplots of the specified Y variable over time, with and without outliers, and a line graph showing the mean value and standard deviations.
    '''

    # Boxplots of normalised yarg at each timepoint showing outliers.
    boxplt = sns.catplot(x='date', y=norm, data= dataF, kind = 'box')
    plt.title('Boxplot of normalised ' + yarg + ' over time, with outliers.')
    boxplt.fig.autofmt_xdate()
    
    # Getting modified dataframes with only the outliers, and then with outliers removed.
    df_outliersOnly = outlierDF(dataF, date)[0]
    df_noOutliers = outlierDF(dataF, date)[1]

    # Boxplots of normalised yarg at each timepoint with outliers removed.
    boxplt_clean = sns.catplot(x='date', y=norm, data= df_noOutliers, kind = 'box')
    plt.title('Boxplot of normalised ' + yarg + ' over time, without outliers.')
    boxplt_clean.fig.autofmt_xdate()
    
    # Line plot of the normalised yarg variable over time (without outliers). SD shown as shadow behind line.
    sns.set_style('darkgrid')
    gmeans = sns.relplot(x='date', y=norm, kind='line', ci='sd', data=df_noOutliers)
    plt.title('Line plot of normalised ' + yarg + ' over time.')
    gmeans.fig.autofmt_xdate()
    
    # Set figure size for later plots.
    fig = plt.figure(figsize=(16,10))
    
    # Line plot of the normalised yarg variable with outlier scatterpot overlaid. SD shown as shadow, as before.
    sns.set_style('darkgrid')
    sns.lineplot(x='date', y=norm, ci='sd', data=df_noOutliers),
    sns.scatterplot(x='date', y=norm, data=df_outliersOnly)
    plt.title('Mean normalised ' + yarg + ' per month (with outliers)')
    fig.autofmt_xdate()
    
    return
    
def plotBokeh(dataF):
    '''
    This function takes a dataframe and plots an interactive graph with mouse-over info.
    '''
    # Create a CDS for bokeh to interact with pandas DF.
    source = ColumnDataSource(getDFstats(dataF))
    sourceOutliers = ColumnDataSource(outlierDF(dataF, date)[0])

    output_file('Mean normalised ' + yarg + ' per month, with outliers. (mouse-over for values).html')
    #output_notebook()

    # Creating a bokeh figure.
    plot = figure(title='Mean normalised ' + yarg + ' per month, with outliers. (mouse-over for values)', x_axis_label='date', y_axis_label='mean ' + yarg,
               x_axis_type='datetime')

    # Creating each plot.
    mean = plot.line('date','mean',line_color='red', source=source)
    outliers = plot.circle('date',norm, source=sourceOutliers, size =5)
    upperci = plot.line('date', '1std.over', line_dash = 'dashed', source=source)
    lowerci = plot.line('date', '1std.under', line_dash = 'dashed', source=source)

    # Configuring mouse-over tooltip.
    tooltips = [
        ('Date','@date{%F}'),
        ('Normalised ' + yarg, '@'+ norm +'{0,0.000}'),
        ('practice','@row_name')
    ]
    formatters = {'date':'datetime'}
    plot.add_tools(HoverTool(tooltips=tooltips, formatters=formatters, renderers=[outliers]))
               
    tooltips2= [
        ('Date', '@date{%F}'),
        ('Mean normalised ' + yarg, '@mean{0,0.000}')
    ]
    formatters2 = {'date':'datetime'}
    plot.add_tools(HoverTool(tooltips=tooltips2, formatters=formatters2, mode='vline', renderers=[mean]))
    
    show(plot)
    
    return
    
    
def plotGraphs(dataF, choice):
    '''
    This function takes a dataframe and a choice of plots to display, and plots those graphs.
    '''
    if choice == '1':
        plotLine(dataF)
    elif choice == '2':
        plotBoxes(dataF)
    elif choice == '3':
        plotBokeh(dataF)
    elif choice == '4':
        plotLine(dataF)
        plotBoxes(dataF)
        plotBokeh(dataF)
    else:
        return 'Something went wrong!'
    

# If both the below options are used, this will subset the dataframe by both.
if groupSubset != "all" and dateRange != "all":
    dr = dateRange.split('|')
    start = datetime.datetime.strptime(dr[0], '%Y-%m-%d')
    end = datetime.datetime.strptime(dr[1], '%Y-%m-%d')
    gS = groupSubset.split('|')
    df_both = df.loc[(pd.to_datetime(df['date']) >= start) & (pd.to_datetime(df['date']) <= end) & df[group].isin(gS)]
    plotGraphs(df_both, plots)

# If a date range is specified, this will create a subset of the main dataframe, within the date range.
elif dateRange != "all":
    dr = dateRange.split('|')
    start = datetime.datetime.strptime(dr[0], '%Y-%m-%d')
    end = datetime.datetime.strptime(dr[1], '%Y-%m-%d')
    df_dateRange = df.loc[(pd.to_datetime(df['date']) >= start) & (pd.to_datetime(df['date']) <= end)]
    plotGraphs(df_dateRange, plots)
    
# If a subset of the grouping option is specified, this will create a subset of the dataframe, constrained to that subset.
elif groupSubset != "all":
    gS = groupSubset.split('|')
    df_groupSubset = df.loc[df[group].isin(gS)]
    plotGraphs(df_groupSubset, plots)
    
# Plot xarg against yarg, grouped by group (no subset).
else:
    plotGraphs(df, plots)

#Display the graphs.
print('Displaying graphs...')
plt.show()

input()
