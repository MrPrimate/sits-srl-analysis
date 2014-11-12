# -*- coding: utf-8 -*-

import os
from datetime import datetime
import re
import pandas as pd
import numpy as np
from sys import argv
from pandas import ExcelWriter

import argparse

parser = argparse.ArgumentParser(prog='srl_no_completes', 
                                 description='Create an Excel file from a eVision log file(s) to find non completing letters.')
parser.add_argument('-i', help='input log file, if not present will load all txt and log files in current working directory')
parser.add_argument('-d', help='input log dir, if present will load all txt and log files in this directory, will override -i')
parser.add_argument('-o', default='letter-analysis.xlsx',
                   help='name of the excel file (default: letter-analysis.xlsx)')
parser.add_argument('-l',  default=1000, type=int,
                   help='time in ms before SRL is considered long running (default: 1000)')

args = parser.parse_args()
logfile = args.i
excelfile = args.o
longrun = args.l
logdir = args.d

if logdir is None: logdir = os.getcwd()

re1='.*?'	# Non-greedy match on filler
re2='(\\\'.*?\\\')'	# Single Quote String 1
re3='.*?'	# Non-greedy match on filler
re4='(?:[a-z][a-z]+)'	# Uninteresting: word
re5='.*?'	# Non-greedy match on filler
re6='((?:[a-z][a-z]+))'	# Word 1
re7='.*?'	# Non-greedy match on filler
re8='((?:(?:[0-2]?\\d{1})|(?:[3][01]{1}))[-:\\/.](?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[-:\\/.](?:(?:[1]{1}\\d{1}\\d{1}\\d{1})|(?:[2]{1}\\d{3})))(?![\\d])'	# DDMMMYYYY 1
re9='.*?'	# Non-greedy match on filler
re10='((?:(?:[0-1][0-9])|(?:[2][0-3])|(?:[0-9])):(?:[0-5][0-9])(?::[0-5][0-9])?(?:\\s?(?:am|AM|pm|PM))?)'	# HourMinuteSec 1
re11='.*?'	# Non-greedy match on filler
re12='(\\d+)'	# Integer Number 1

rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12,re.IGNORECASE|re.DOTALL)

casts = []
casts_times = []

# Find lines
def search(in_text):
    return rg.search(in_text)
    
# Read in the log file function
def readlogfile(logfile):
    localcasts = []
    with open(logfile) as fp:
        for line in fp:
            if line.startswith('Letter \''):
                # found a cast
                letter_code, letter_state, date_stamp, time_stamp, mseconds = rg.search(line).groups()
                clock_stamp = datetime.strptime(date_stamp + time_stamp + mseconds + '0000', '%d/%b/%Y%H:%M:%S%f')
                cast = {
                        'letter': letter_code,
                        'state': letter_state,
                        'date_time_stamp': datetime.strptime(date_stamp + time_stamp + mseconds + '0000', '%d/%b/%Y%H:%M:%S%f'),
                        'counter': 1,
                        # '{0} {1}.{2}\n'.format(date_stamp, time_stamp, seconds),
                        }
                casts.append(cast)
                #second casting
                cast2 = {
                        'letter': letter_code,
                        'start_date_time_stamp': get_real_clock_stamp(letter_state, 'started', clock_stamp),
                        'stop_date_time_stamp': get_real_clock_stamp(letter_state, 'finished', clock_stamp),
                        'time_taken': None,
                        'success': False,
                        'counter': 1,
                            }
                #print cast
                if cast2['start_date_time_stamp'] is not None:
                    localcasts.append(cast2)
                elif cast2['stop_date_time_stamp'] is not None:
                    localcasts.reverse()
                    try:
                        for index, item in enumerate(localcasts):
                            if (item['stop_date_time_stamp'] is None) and (item['letter'] == cast2['letter']):
                                td = cast2['stop_date_time_stamp'] - localcasts[index]['start_date_time_stamp']
                                localcasts[index]['stop_date_time_stamp'] = cast2['stop_date_time_stamp']
                                localcasts[index]['success'] = True
                                localcasts[index]['time_taken'] = td.microseconds/1000
                    finally:
                        localcasts.reverse()
    return localcasts

# Get a time stamp
def get_real_clock_stamp(letter_state, stamp_type, clock_stamp):
    if letter_state == stamp_type: return clock_stamp
    else: return None

# Begin code
# loop through log file dir or load logfile
if logdir is not None or logfile is None:
    for fn in os.listdir(logdir):
        file_loc =  os.path.join(logdir, fn)
        if os.path.isfile(file_loc):
            if file_loc.lower().endswith(('.log', '.txt')):
                print "Parsing log {0}...".format(file_loc)
                casts_times.extend(readlogfile(file_loc))
                print "Log parsed..."
else: readlogfile(logfile)

# Inform user and begin file creation
print "Calculating sums 'n things."
writer = ExcelWriter(excelfile, engine='xlsxwriter')
df = pd.DataFrame(casts)
if not df.empty:
    analysis = pd.pivot_table(df, values=['counter'], rows=['letter', 'state'], aggfunc=np.count_nonzero, margins=True)
    analysis.to_excel(writer, sheet_name='Letters')

df2 = pd.DataFrame(casts_times)
if not df2.empty:
    analysis_advanced = pd.pivot_table(df2, values=['time_taken', 'counter'], rows=['letter', 'success'], aggfunc=[np.sum, np.average], margins=True)
    analysis_advanced.to_excel(writer, sheet_name='Analysis')

    print "Finding failed SRL's."
    df2_1 = df2[(df2.success == False)]
    if not df2_1.empty:
        analysis_failures = pd.pivot_table(df2_1, values=['time_taken', 'counter'], rows=['letter', 'success'], aggfunc=[np.sum, np.average], margins=True)
        analysis_failures.to_excel(writer, sheet_name='Failed Letters')

    print "Finding Long running SRL's."
    df2_2 = df2[(df2.time_taken >= longrun)]
    print("begin analysis")
    if not df2_2.empty:
        analysis_longrun = pd.pivot_table(df2_2, values=['time_taken', 'counter'], rows=['letter', 'success'], aggfunc=[np.sum, np.average, np.mean], margins=True)
        analysis_longrun.to_excel(writer, sheet_name='Long running')

print "Writing file..."
writer.save()

# Finished!
print "Finished! {0} created".format(excelfile)
