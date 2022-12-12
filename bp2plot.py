#!/usr/bin/python3
""" 
Input: markdown from obsidian journal

Output: A plot showing blood pressure using plotly with a side histogram

""" 

import numpy as np
import pandas as pd
import plotly.express as px
import re
import argparse
import glob
import datetime 
import time


# This makes sure that it will display everything if we print to check out work.
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)

# Read in the script parameters
# https://docs.python.org/3/library/argparse.html#module-argparse
parser = argparse.ArgumentParser(
                    prog = 'journal2plot',
                    description = 'Read in obsidian journal entries and plot blood pressure',
                    epilog = '');

parser.add_argument("vault",help="directory of vault that contains daily/YYYY-MM/* logs")
parser.add_argument("--days","-d",default=14,help="Days of data to display.")
parser.add_argument("--verbose","-v",action="store_true",help="Whether to print the raw dataframe before displaying a plot",default=False)
args = parser.parse_args()

pattern = re.compile("^\s*(.*)\s*::\s*(.*)$")
daily_pattern = re.compile("(\d{4}-\d+-\d+).md$")


days = {}
for daily_path in glob.glob(args.vault + "/daily/*/*"):
     daily_match = daily_pattern.search(daily_path)
     if ( daily_match ):
       with open(daily_path, 'r') as daily_file:
         row = {}
         for line in daily_file:
             m = pattern.search(line)
             if ( m ):
               row[m.group(1)] = m.group(2)
             else:
               continue # for line in daily_file
         days[daily_match.group(1)]=row
     else:
         continue # for daily path

# Confused why the outer dictionary is the columns, but that isn't great.
df = pd.DataFrame.from_dict(days)
daily_data = df.transpose()
daily_data.dropna(inplace=True,how='all')


daily_data.index = daily_data.index.set_names('day')
daily_data.reset_index(inplace=True)
daily_data.sort_index(ascending = False,inplace = True)

# Systolic is top number
# Diastolic is bottom number
bp_pattern = re.compile('^\s*(\d+)\s*/\s*(\d+)\s*$')

# TODO: Figure out way to do this in one step.
daily_data['Systolic'] = daily_data.apply(lambda r: bp_pattern.match(r.BP).group(1),axis=1,result_type="expand")
daily_data['Diastolic'] = daily_data.apply(lambda r: bp_pattern.match(r.BP).group(2),axis=1,result_type="expand")

daily_data['Systolic'] = pd.to_numeric(daily_data.Systolic,errors="coerce")
daily_data['Diastolic'] = pd.to_numeric(daily_data.Diastolic,errors="coerce")

# any zero is something that was not captured, and not a real value for BP, weight, or exercise
daily_data.replace(0, np.nan, inplace=True)

bp_data = pd.melt(daily_data,id_vars="BP_Time",value_vars=("Systolic","Diastolic"),value_name="Reading")
bp_data['BP_Time'] = pd.to_datetime(bp_data['BP_Time'], format='%Y-%m-%d %H:%M')

# Cut early data from the list.  
bp_data = bp_data.loc[bp_data['BP_Time'] > pd.to_datetime('2022-11-01')]
bp_data = bp_data.loc[bp_data['BP_Time'] > pd.to_datetime(datetime.date.today() - datetime.timedelta(days = int(args.days) ))]
if ( args.verbose ):
  print(bp_data)


# Plot a scatterplot, with a different color and dot shape for each Name.
fig = px.scatter(bp_data, x="BP_Time", y="Reading",color="variable" ,marginal_y="histogram", color_discrete_sequence=px.colors.qualitative.Dark2,)
fig.show()
