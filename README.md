# README #

## Overview ##

### Quick summary ###

Python interface for Yahoo finance data. This can be used for a variety of modeling for the stock market.

### Version ###

* v0.1 - 12/17
    * Initial Version
    * Get historical Yahoo finance data for any available ticker

## Setup ##

### Installation ###

* Install Python 3+
* TODO: more detailed info?

### Dependencies ###

* TODO: if needed to install BeautifulSoup and such via PyPI

## Usage ##
- - - -

### Examples ###

Creating a Stock object will request historical data given a date range. If no
date is specified, the stock requests YTD information.

~~~~
D:\Programming Projects\stockbot>python -O
Python 3.6.0 (v3.6.0:41df79263a11, Dec 23 2016, 07:18:10) [MSC v.1900 32 bit (I
tel)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> from stock.stock import Stock
>>> amd = Stock('AMD')
>>> amd.day_info()
[datetime.datetime(2017, 12, 5, 0, 0), (9.89, 10.34, 9.7, 9.91, 9.91, 66913300)
>>> amd.open()
9.89
>>> amd.close()
9.91
>>> amd.high()
10.34
>>> amd.low()
9.7
>>> amd.adj_close()
9.91
>>> amd.volume()
66913300
~~~~

You can also get range of data by providing a range of dates. These dates must
fall within the range originally requested for the Stock otherwise it will be
truncated to what is available.

Dates are provided via YYYY-MM-DD format.

~~~~
>>> from pprint import pprint
>>> pprint(amd.day_info('2017-10-10','2017-10-13'))
[[datetime.datetime(2017, 10, 10, 0, 0),
  (13.72, 13.79, 13.44, 13.7, 13.7, 43304000)],
 [datetime.datetime(2017, 10, 11, 0, 0),
  (13.62, 13.96, 13.61, 13.88, 13.88, 38746600)],
 [datetime.datetime(2017, 10, 12, 0, 0),
  (13.85, 14.37, 13.81, 14.2, 14.2, 69874100)]]
>>>
~~~~

### Available API's ###

Single dates **and** ranges:

* day_info()
* open()
* close()
* high()
* low()
* adj_close()
* volume()

Unique to stock based on Yahoo finance statistics:

* market_cap()
* avg_volume_10day()
* avg_volume_3month()
* pe_ratio()
* eps()
* beta()

## Limitations ##

* Doesn't retrieve current day's data (yet)
* Can't retrieve data prior to 1/1/1970 (fixable)
* Not all statistical data is available via public API (fixable)
* Python 2.7 support may require changes.

- - - -
[Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)