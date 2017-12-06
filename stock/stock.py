import re
import time
import requests

from bs4 import BeautifulSoup
from datetime import datetime

CRUMB_REGEX = '.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}'
REQUEST_URL = "https://query1.finance.yahoo.com/v7/finance/download/%s" \
              "?period1=%s&period2=%s&interval=%s&events=%s&crumb=%s"
STATS_URL = "https://finance.yahoo.com/quote/%s/key-statistics?p=%s"

class Stock:
    """

    """

    #--------------------------------------------------------------------------
    # Class attributes
    #----
    _YAHOO_COOKIE = None
    _YAHOO_CRUMB = None

    # Yahoo Finance historical data
    OPEN_IDX = 0
    HIGH_IDX = 1
    LOW_IDX = 2
    CLOSE_IDX = 3
    ADJ_CLOSE_IDX = 4
    VOLUME_IDX = 5

    FIRST_DAY_KEY = 'first_day'

    def __init__(self, ticker, start=None, end=None, interval='1d', advanced=False):
        """
        :param ticker: Stocks ticker
        :param start: Start date for historical data
        :param end: End date for historical data
        :param interval: Interval for data points
            '1d' - daily
            '1wk' - weekly
            '1mo' - monthly
        :param advanced: 
            Flag to indicate if the stock should have an advanced structure built.
            The advanced structure improves efficiency for more demanding calculations by buidling
            out a more advanced data structure.

            If you're planning on doing many calculations on a stock, using the advanced flag is
            recommended. More details on the data structure can be found below.
        """

        self.ticker = ticker = ticker.upper()
        self.advanced = advanced
        self.stock_index = {}
        self.stock = self._get_stock(ticker, start, end, interval, advanced)
        self.stats = {}
        self._request_statistics(ticker)

        if __debug__:
            print("Created {}.\n\n".format(self.ticker))
            #print(self.stock)
            #print(self.stock_index)
            #print(self.stats)
            
    #--------------------------------------------------------------------------
    # Public functions
    #----
    
    def day_info(self, date=None, end_date=None):
        """
        Return a days data tuple.
        
        If date is outside of available range, None is returned.
        If date is a holiday or weekend, the nearest preceding day is returned.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: Tuple of available day data.
        """
        return self._day_info(date, end_date)
    
    def open(self, date=None, end_date=None):
        """
        Return open price for given date.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: Opening price
        """
        return self._get_day_info_piece(Stock.OPEN_IDX, date, end_date)

    def close(self, date=None, end_date=None):
        """
        Return closing price for given date.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: Closing price
        """
        return self._get_day_info_piece(Stock.CLOSE_IDX, date, end_date)
        
    def high(self, date=None, end_date=None):
        """
        Return high price for given date.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: High price
        """
        return self._get_day_info_piece(Stock.HIGH_IDX, date, end_date)
        
    def low(self, date=None, end_date=None):
        """
        Return low price for given date.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: Low price
        """
        return self._get_day_info_piece(Stock.LOW_IDX, date, end_date)
        
    def adj_close(self, date=None, end_date=None):
        """
        Return adjusted closing price for given date.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: Adjusted closing price
        """
        return self._get_day_info_piece(Stock.ADJ_CLOSE_IDX, date, end_date)
        
    def volume(self, date=None, end_date=None):
        """
        Return daily volume for given date.
        
        :param date: Date for which to get data for - start range.
        :param end_date: Date for which to get a range for.
        :returns: Daily trade volume
        """
        return self._get_day_info_piece(Stock.VOLUME_IDX, date, end_date)

    #
    # Data available on the 'Statistics' tab of Yahoo finance (TODO:all data is parsed, not all is exposed atm)
    #

    def market_cap(self):
        """
        Get market cap.
        
        :returns: Market cap
        """
        return self.stats['Market Cap (intraday)']

    def avg_volume_10day(self):
        """
        Get average volume.
        
        :returns: Average volume
        """
        return self.stats['Avg Vol (10 day)']

    def avg_volume_3month(self):
        """
        Get average volume.
        
        :returns: Average volume
        """
        return self.stats['Avg Vol (3 month)']

    def pe_ratio(self):
        """
        Get P/E ratio.
        
        :returns: P/E ratio.
        """
        return self.stats['Trailing P/E']
        
    def eps(self):
        """
        Get Earnings per Share (EPS).
        
        :returns: EPS
        """
        return self.stats['Diluted EPS (ttm)']

    def beta(self):
        """
        Get beta.
        
        :returns: Beta
        """
        return self.stats['Beta']

    # Any data piece from the financials page can exposed here via self.stats[<label on website>]

    #--------------------------------------------------------------------------
    # Static functions
    #----
    
    @staticmethod
    def _get_cookie_crumb():
        """
        Retrieve a valid cookie and crumb for Yahoo finance.

        This is required to download historical data properly via https request.
        """

        response = requests.get('https://finance.yahoo.com/quote/SPY/history')

        Stock._YAHOO_COOKIE = response.cookies['B']

        pattern = re.compile(CRUMB_REGEX)

        for line in response.text.splitlines():
            match = pattern.match(line)
            if match:
                # Protect against unicode characters in crumb (different between 2.x and 3+)
                Stock._YAHOO_CRUMB = \
                    bytes(match.groupdict()['crumb'], encoding='ascii').decode('unicode_escape')

        if __debug__:
            print('\n ======================================')
            print('| Cookie: ' + Stock._YAHOO_COOKIE)
            print('| Crumb: ' + Stock._YAHOO_CRUMB)
            print(' ======================================\n')

    #--------------------------------------------------------------------------
    # Private functions
    #----
    
    def _day_info(self, date=None, end_date=None):
        """
        Return all information for a particular date. A day is comprised of a date, yahoo data,
        and any additional data saved off in the following format:

        [date, (yahoo_data), [<additional data>]]

        :param date: Date for which to retrieve data for
        :param end_date: End date for a range of date (preceding date)
        :returns: Daily data (oldest first)
        """

        # Parse date range into indicies
        if date is None:
            date = datetime.today() # default
        elif not isinstance(date, datetime):
            date = parse_date(date)

        start_idx = self._get_date_index(date)

        if __debug__:
            print('Starting date : %s at index %s' % (date, start_idx))

        if end_date:
            if not isinstance(end_date, datetime):
                end_date = parse_date(end_date)

            end_idx = self._get_date_index(end_date)

            if __debug__:
                print('Ending date %s at index %s' % (end_date, end_idx))

            if start_idx > end_idx:
                return None # Or raise an error for dates? TODO:

            return self.stock[start_idx:end_idx]

        return self.stock[start_idx]

    def _get_day_info_piece(self, idx, date=None, end_date=None):
        """
        Return a piece of day_info from yahoo historical data.

        :param idx: Index of data piece
        :param date: Start date
        :param end_date: End date for range
        :returns: Data or range of date for a particular piece.
        """
        open_data = []
        day_info = self._day_info(date, end_date)

        # Single days aren't lists
        if not end_date:
            return day_info[1][idx]

        # Extract the data
        for data in day_info:
            print(data)
            open_data.append(data[1][idx])

        return open_data

    def _get_date_index(self, date):
        """
        Get index of data for the corresponding date. If the date is outside of the range,
        return the closest date possible.
        
        :param date: datetime instance
        :returns: index for data
        """
        max_index = len(self.stock)-1

        try:
            curr_index = self.stock_index[date.year][date.month][Stock.FIRST_DAY_KEY]
        except KeyError:
            # Non-indexed year/month - out of range.
            return 0 if self._compare_dates(self.stock[0][0], date) < 0 else max_index

        # Loop over to find exact date
        done = False

        while not done:
            curr_date = self.stock[curr_index][0]
            
            if __debug__:
                print('\t%s at index: %s' % (curr_date, curr_index))

            # Check exact date
            ret = self._compare_dates(curr_date, date)
            if ret > 0: # Keep looking forward
                if curr_index < max_index:
                    curr_index += 1
                else:
                    return curr_index
            elif ret < 0: # Date is in the past
                return (curr_index - 1) if curr_index > 0 else curr_index
            else: # Exact match
                return curr_index


    def _compare_dates(self, date_1, date_2):
        """
        Compare two dates and return the difference as whether date 1 is before, after, or equal
        to the compared date.
        
        :param date_1: Date 1
        :param date_2: Date 2
        :returns: 0 if dates match, 1 if Date 2 follows Date 1, -1 otherwise.
        """
        year_delta = date_2.year - date_1.year
        month_delta = date_2.month - date_1.month
        day_delta = date_2.day - date_1.day

        if year_delta != 0:
            return -1 if year_delta < 0 else 1

        if month_delta != 0:
            return -1 if month_delta < 0 else 1

        return 1 if day_delta > 0 else (0 if day_delta == 0 else -1)

    def _request_statistics(self, ticker):
        """
        Request and parse out the statistic page of yahoo finance for a stock.
        
        This data is then saved off in a dictionary on the object.
        TODO: Error checking and such?
        """
        request_url = STATS_URL % (ticker, ticker)

        response = requests.get(request_url)

        parsed_resp = BeautifulSoup(response.text, 'html.parser')
        # Ugly, but it works here
        stats_values = parsed_resp.find_all('div', 'Mstart(a) Mend(a)')[0].find_all('td', 'Fz(s) Fw(500) Ta(end)')

        # Iterate all statistic data pieces
        for values in stats_values:
            val = values.get_text()
            val = self._parse_stat(val)
            label = values.previous_sibling.find('span').get_text()
            
            # Save it off
            self.stats[label] = val

    # Used for properly scaling numbers from Yahoo finance
    suffix_multiplier = {
        'M' : 1000000,
        'B' : 1000000000,
        'T' : 1000000000000,
    }

    # Transition statistical string months into numerical values
    month_map = {
        'Jan' : 1,
        'Feb' : 2,
        'Mar' : 3,
        'Apr' : 4,
        'May' : 5,
        'Jun' : 6,
        'Jul' : 7,
        'Aug' : 8,
        'Sep' : 9,
        'Oct' : 10,
        'Nov' : 11,
        'Dec' : 12,
    }

    def _parse_stat(self, val):
        """
        Parse stat to save in more computer friendly manner.
        
        Dates become datetimes.
        Numbers are converted to proper integers.
        Percentages are reduced to decimal representation.
        'N/A' is changed to None.
        
        :returns: parsed value if it can be parsed.
        """
        date_regex = re.compile('^([\w]+)\s(\d{1,2})[,]\s(\d{4})')
        percent_regex = '^([\d]+[.][\d]{2})[%]'
        number_regex = '^([\d]+[.][\d]{2})([M|B|T])*'

        if val == 'N/A':
            return None

        # Simple numbers with potential Million/Billion suffixes
        match=re.match(number_regex, val)
        if match:
            number = match.groups()[0]
            val = round(float(number),2)

            suffix = match.groups()[1]
            if suffix:
                val *= Stock.suffix_multiplier[suffix]

            return val

        # Percentages
        match=re.match(percent_regex, val)
        if match:
            number = match.groups()[0]
            val = round(float(number),2)
            return val

        # Date of event of some sorts
        match=re.match(date_regex, val)
        if match:
            g = match.groups()
            month = Stock.month_map[g[0]]
            day = int(g[1])
            year = int(g[2])
            return datetime(year, month, day)

        return val

    def _get_stock(self, ticker, start, end, interval, advanced=False):
        """
        Request and parse out stock data for further manipulation.

        :param ticker: Stocks ticker
        :param start: Start date for historical data
        :param end: End date for historical data
        :param interval: Interval for data points
        :param advanced: Flag to indicate if the stock should have an advanced structure built.
        :returns: Stock data structure - simple or advanced
        """

        if not Stock._YAHOO_COOKIE or not Stock._YAHOO_CRUMB:
            Stock._get_cookie_crumb()

        # Request raw CSV
        csv = self._request_csv(ticker, start, end, interval)

        if not csv:
            #TODO: Retry with new cookie/crumb? At least once might help...
            print("***ERROR*** Could not retrieve stock")
            return None

        # Parse out data for easier manipulation
        return self._parse_stock_csv(csv, advanced)

    def _request_csv(self, ticker, start, end, interval):
        """
        Build request URL to download historical financial data from Yahoo finance.

        :param ticker: Stocks ticker
        :param start: Start date for historical data
        :param end: End date for historical data
        :param interval: Interval for data points
        :returns: Response from request URL, None if failed.
        """

        # Format Parameters
        start, end = self._format_dates(start, end)

        if not interval:
            interval = '1d'

        # Build request URL
        url = REQUEST_URL % (ticker, start, end, interval, 'history', Stock._YAHOO_CRUMB)

        if __debug__:
            print("\nTicker: %s Start: %s End: %s Interval: %s Crumb: %s" 
                  % (ticker, start, end, interval, Stock._YAHOO_CRUMB))
            print(url)

        # Request data
        response = requests.get(url, cookies={'B': Stock._YAHOO_COOKIE}).text
        #TODO: Error check a bit?
        return response

    def _parse_stock_csv(self, raw_csv, advanced=False):
        """
        Build out a simple index on a list containing all data from requested stock.
        
        :param raw_csv: string CSV as returned from yahoo finance
        :param advanced: Flag indicating advanced features to be calculated
        :returns: Populated data structure for stock data
        """
        stock_data = raw_csv.split('\n')[1:-1] # Exclude header and last blank line
        
        for i,data in enumerate(stock_data):
            stock_data[i] = self._parse_day_str(data)

        self._index_stock_data(stock_data)

        # Check for advanced mode for more complicated calculations
        if advanced:
            return self._advanced_index(stock_data) #TODO: Does nothing yet
        else:
            return stock_data

    def _index_stock_data(self, stock_data):
        """
        Loop over stock data and index dates for easier access in the future.
        
        Data is indexed as follows - to access more easily:
        { <year> : { <month> : {FIRST_DAY_KEY:<index of first day in the month>}, ... }, ... }
        
        TODO: Consider creating a pseudo-hash function for dates to just key into an array index
        given a date. Then there's not need to a dictionary for indexing, and we simply run date
        values through a function to get indicies.
        
        Downside is that it's not as universally applicable across many dates IMO. But, I also
        didn't think about it that hard...
        """
        n_day = 0
        
        for day in stock_data:
            curr_date = day[0]
            if self._is_new_first_day(curr_date):
                self._index_first_day(curr_date, n_day)
                
            n_day += 1
    
    def _index_first_day(self, date, day_idx):
        """
        Index a day index for a particular month as the first day available.
        
        :param year: Year
        :param month: Month
        :param day_idx: Index in stock_data
        """
        if date.year not in self.stock_index:
            self.stock_index[date.year] = {}
        
        if date.month not in self.stock_index[date.year]:
            self.stock_index[date.year][date.month] = {}
            
        self.stock_index[date.year][date.month][Stock.FIRST_DAY_KEY] = day_idx
        
        if __debug__:
            print('\tIndexed new first date: {} as index {}.'.format(date, day_idx))
        
    def _is_new_first_day(self, date):
        """
        Check if year/month was already indexed for the first day index.
        
        This shouldn't be called out of order, so first instance of year/month should
        resolved to the first day...
        
        :param date: datetime instance
        :returns: True if this date isn't indexed yet for a year/month combo
        """
        if date.year not in self.stock_index:
            return True
        
        if date.month not in self.stock_index[date.year]:
            return True
            
        return False
    
        
    def _advanced_index(self, stock_data):
        """
        Build an additional data structure for indexing key data for more advanced
        computation.

        TODO:
        Store earning data on year level? Each year has a date and data for specific
        earnings - maybe also on month level?
        """
        if __debug__:
            print('Generating advanced data structure')
            
        #TODO: What should we do about Dividends and Splits?

        #TODO: What should we do about Earnings? (dates/expectations vs actual etc.)

        return stock_data #TODO:

    def _parse_day_str(self, day_str):
        """
        Return a tuple corresponding to the parsed data.

        The raw string is broken into the following pieces:
            Date:datetime
            Open:float (2 decimal points)
            High:float (2 decimal points)
            Low:float (2 decimal points)
            Close:float (2 decimal points)
            Adj Close:float (2 decimal points)
            Volume:int
        """
        data = day_str.split(',')

        date = parse_date(data[0])
        open = round(float(data[1]),2)
        high = round(float(data[2]),2)
        low = round(float(data[3]),2)
        close = round(float(data[4]),2)
        adj_close = round(float(data[5]),2)
        volume = int(data[6])

        return [date, (open, high, low, close, adj_close, volume)]

    def _format_dates(self, start, end):
        """
        Return formatted date stamps as accepted by Yahoo finance API's - Unix timestamps.

        :param start: Date string for starting date
        :param end: Date string for ending date
        :returns: Unix timestamps for both start and end dates
        """

        if not start or not end:
            # Default to YTD
            today = datetime.now()
            start = unix_date(datetime(today.year, 1, 1))
            end = unix_date(today)
        else:
            # Parse dates
            start = unix_date(parse_date(start))
            end = unix_date(parse_date(end))

        return start, end

#--------------------------------------------------------------------------
# Helper functions
#----
def parse_date(date_str):
    """
    Parses string for a valid date.

    Acceptable formats always lead with the year, followed by month and day. Mixed
    seperators are NOT supported.

    Examples of dates this function will match:
        "1990/1/15"
        "1990.1.15"
        "1990-01-15"

    :param date_str: Date string which may or may not contain a valid date
    :return: A valid datetime instance
    """
    date_regex = re.compile('(\d{4})(?P<seperator>[./-])(\d{1,2})(?P=seperator)(\d{1,2})')

    match = re.match(date_regex, date_str)

    if match:
        groups = match.groups()
        year = int(groups[0])
        month = int(groups[2])
        day = int(groups[3])
    else:
        year, month, day = 1970, 1, 1 # We should probably throw an exception here?

    #TODO: Support dates prior to epoch (1970/1/1) on various platforms 
    #   https://stackoverflow.com/questions/2518706/python-mktime-overflow-error

    return datetime(year, month, day)

def unix_date(date):
    """
    Convert a datetime instance to a Unix time stamp.

    :param date: Datetime instance of a date
    :type date: class datetime.datetime
    :return: Unix time stamp
    :rtype: int
    """
    return int(time.mktime(date.timetuple()))

# Notes:        
#       
# https://query1.finance.yahoo.com/v7/finance/download/CERN?period1=534146400&period2=1511503200&interval=1d&events=history&crumb=VX/TqG4FNwE
#
# Parameters
#   period1: start date
#       1 day = 86400 = 24hrs * 60 min * 60 sec
#       
#       01/01/2000 = 946706400
#       01/03/1950 = -630957600
#
#       Must be within +-86400 on a given day to resolve to that day.
#       
#       0 = 01/01/1970
#
#   period2: end date
#
#   interval: frequency of data *weirdness for dividends - just use history...
#       1d  - daily
#       1wk - weekly
#       1mo - monthly
#
#   filter:
#       history - historical stock data *includes dividends (and likely splits)
#       dividends - dividends only
#       split - stock splits only

