[![GitHub Actions status | neatc0der/zdf-auto-dl](https://github.com/neatc0der/zdf-auto-dl/workflows/CI/badge.svg)](https://github.com/neatc0der/zdf-auto-dl/actions?workflow=CI)

zdf-auto-dl
===========

ZDF Mediathek Auto Downloader 1.0.2


## Requirements
* python 2.7 - 3.6 (supposed, please verify yourself)
* pip
    * argparse
    * colorlog
    * ConfigParser
    * cssselect
    * lxml
    * python-dateutil
    * requests
    * six


## Installation

    pip install -Ur requirements.txt


## Usage
* setup config file zdf.ini
* start downloader (e.g. as cron job)

~~~
Usage:
./src/zdf_auto_dl/main.py [OPTIONS]

OPTIONS:
  -h, --help       print help message
  -c, --config     set path to configuration file
  -f, --find       display available episodes only (no download)
  -l, --log-level  set log level
  -p, --progress   print download progress
  --no-color       disable colorize output
~~~

## ToDo
* ensure support for all python versions
    * Python 2.7: verified (2.7.6)
    * Python 3.5: verified (3.5.2)
    * Python 3.6: verified (3.6.1)
* add setup.py
    * include command to bind main.py
