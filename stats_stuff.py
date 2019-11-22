#making a list of dates found in the df

startdate = datetime.date(2014,10,1)
enddate = datetime.date(2019, 8, 1)
dates = [startdate.strftime('%Y-%m-%d')]

while startdate <= enddate:
    startdate += datetime.timedelta(days=32)
    startdate = startdate.replace(day=1)
    dates.append(startdate.strftime('%Y-%m-%d'))
print(dates)
len(dates)


#making a dictionary of dataframes for each timepoint(month)
d={}
for i in dates:
    d[i] = df[df.date == i]
print(d.keys())
print(d['2014-10-01'])


#dataframe of quantity stats for each timepoint
dfstats = df.groupby('date')['quantity'].describe().reset_index()
