sits-srl-analysis
=================

A python script for checking SITS log files for long running SRL's and those which never finish

Sometimes you just get UServers locking up, using CPU or memory and never stopping, or become unresponsive. Normally this is down to an SRL that's gone a bit wonky. Can we try and identify the issues without having to turn on PAL and WTL?

We can give it a shot. Below is a script that scrapes through log files, and finds the start and end times of letters, and tries to match them up. It's not perfect, but it helps. It will output the results to a nice excel file for you, and do a bit of analysis.

What's the aim:
It will identify (or try to identify):

* Letters that never complete
* Long running letters

What are it's limitations? Well it's not going to work on SRL's that have the Message log mode set to 'No generation messages'.

You can find it compiled into a standalone windows executable [here](/uploads/standalone_srl_no_completes.zip).

How to run:

```bat
c:\temp>srl_no_completes.exe -h
usage: srl_no_completes.exe [-h] [-i I] [-d D] [-o O] [-l L]
	
Create an Excel file from a eVision log file to find non completing letters.
	
optional arguments:
  -h, --help  show this help message and exit
  -i I        input log file, if not present will load all txt and log files
              in current working directory
  -d D        input log dir, if present will load all txt and log files in
              this directory, will override -i
  -o O        name of the excel file (default: letter-analysis.xlsx)
  -l L        time in ms before SRL is considered long running (default: 1000)
```


Some worked examples:

Analyse a single log file:

```bat
c:\temp>srl_no_completes.exe -i wsvrsite_log_30589.txt
```

Analyses all *.log and *.txt files in current working directory:

```bat
c:\temp>srl_no_completes.exe
```

Analyses all *.log and *.txt files in target dir (this can be absolute or relative path) with a long running srl defined as more than 500 ms:

```bat
C:\temp>dist\srl_no_completes.exe -d "E:\DATA\Code\letters\logs" -l 500
```

It will create an Excel file with up to 4 sheets:

* A pivot output like you can get from using excel
* A breakdown of letters indicating how long each took, with mean and average times
* A sheet containing those that didn't complete 
* A sheet containing those that took a long time to run (default 1000 ms). This can be changed with the -l flag.

If you don’t get the last two sheets, it’s because all the SRL’s completed or were not long running.
