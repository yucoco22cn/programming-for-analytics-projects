import os
import csv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy import stats
from fractions import *

DATA=os.getcwd()

class TimeSeries(object):
    """Holds a date/value series of data"""
    def __init__(self, name, title=None, unit=None):
        self.name = name
        self.title = title
        self.unit = unit
        self.data = {}
        self.first_date = None
        self.last_date = None

    def get_dates(self, candidates=None, start=None, end=None):
        """Get the dates where this series has values
        ts.get_dates() - gets all dates where ts has values
        ts.get_dates(start=d1,end=d2) - get all valid dates, d, 
                                        where d1<=d<=d2
        ts.get_dates(candidates=dates) - get all valid dates, d, 
                                         for d in dates
        :param candidates: if set, start and end are ignored, and 
                           returns the subset of dates within 
                           candidates for which this series has data
        :param start:      minimum starting date of returned dates, 
                           defaults to beginning of this series
        :param end:        max ending date of returned dates, 
                           defaults to end of this series
        :return:           a list of dates, in order, for which
                           this series has values and that satisfy
                           the parameters' conditions
        """
        if candidates is not None:
            return [date for date in candidates if date in self.data]
        if start is None:
            start = self.first_date
        if end is None:
            end = self.last_date
        return [date for date in self.data if start <= date <= end]

    def get_values(self, dates):
        """Get the values for the specified dates.
        :param dates:      list of dates to get values for
        :return:           the values for the given dates in the same order
        :raises: KeyError  if any requested date has no value
        """
        ret = []
        for d in dates:
            ret.append(self.data[d])
        return ret

    def __sub__(self, other):
        """create a difference time series"""
        return Difference(self, other)

    def correlation(self, other):
        """Calculate the Pearson correlation coefficient between this series
        and another on all days when they both have values.
        Uses scipy.stats.pearsonr to calculate it.
        """
        dates=self.get_dates(other.get_dates())
        #print(len(self.get_values(dates)))
        #print(len(other.get_values(dates)))
        #print(self.get_values(dates))
        r,p=stats.pearsonr(self.get_values(dates), other.get_values(dates))
        return r
        


class Difference(TimeSeries):
    """A time series that is the difference between two other time series"""
    def __init__(self, a, b):
        super().__init__(a.name + '-' + b.name, unit=a.unit)
        self.data = {d: (a.data[d] - b.data[d]) for d in a.data if d in b.data}
        self.first_date = min(self.data)
        self.last_date = max(self.data)

class Fred(TimeSeries):
    """A time series that is based on a csv file downloaded from 
    fred.stlouis.org
    """
    def __init__(self, name, title=None, unit=None):
        """Opens and reads the csv file in DATA/name.csv"""
        super().__init__(name.lower(), title, unit)
        filename = os.path.join(DATA, name + '.csv')
        with open(filename) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                try:
                    value = float(row[name])
                except ValueError:
                    continue
                date = datetime.strptime(row['DATE'], "%Y-%m-%d")
                self.data[date] = value
        self.first_date = min(self.data)
        self.last_date = max(self.data)


class dgs3mo(Fred):
    """The 3-month treasury series from FRED"""
    def __init__(self):
        super().__init__('DGS3MO', '3-Month Treasury', 'percent')


class dgs10(Fred):
    """The 10-year treasury series from FRED"""
    def __init__(self):
        super().__init__('DGS10', '10-Year Treasury', 'percent')


class Bundesbank(TimeSeries):
    """A time series that is based on a csv file downloaded from 
    fred.stlouis.org
    """
    def __init__(self, className, name, title=None, unit=None):
        """Opens and reads the csv file in Lab3/BBEX3.D.XAU.USD.EA.AC.C04.csv"""
        self.className = className
        filename = os.path.join(DATA, name + '.csv')
        with open(filename,encoding='utf8') as csv_file:
            reader = csv.reader(csv_file)
            for row_number, row in enumerate(reader):
                if row[1] == filename:
                    continue
                if row[0] == '':
                    self.title = row[1]
                    continue
                if row[0] == 'unit':
                    self.unit = row[1]
                    continue
                try:
                    datetime.strptime(row[0], "%Y-%m-%d")
                    break
                except: ValueError
        super().__init__(name, title, unit)
        with open(filename,encoding='utf8') as csv_file:
            reader = csv.reader(csv_file)
            for skip in range(row_number):  # row_number is first data line
                next(reader)
            for row in reader:
                try:
                    self.data[datetime.strptime(row[0], "%Y-%m-%d")]=float(row[1])
                except: ValueError
            self.first_date=min(self.data.keys())
            self.last_date=max(self.data.keys())
              
class gold_spot(Bundesbank):
    """Spot gold prices from London morning fix
    >>> gold = gold_spot()
    >>> gold.first_date, gold.last_date, gold.data[gold.first_date]
    (datetime.datetime(1968, 4, 1, 0, 0), datetime.datetime(2018, 7, 30, 0, 0), 38.0)
    >>> gold.title, gold.unit
    ('Price of gold in London / morning fixing / 1 ounce of fine gold = USD ...', 'USD')
    """
    def __init__(self):
        """Bundesbank's constructor wants time series name and filename in
        the DATA directory (automatically appending '.csv' to it).
        Bundesbank will automatically pull title and unit from within
        the file.
        """
        super().__init__(self.__class__.__name__, 'BBEX3.D.XAU.USD.EA.AC.C04')

class lag(TimeSeries):
    """Time series that is a right-shifted copy of another.
    Shifting is done across a given number of data points, ignoring actual
    time intervals (e.g., a lag of one on a weekday-only series goes from
    Thursday to Friday and Friday to Monday, ignoring the weekend where
    there are no points)
    >>> lagger = lag(TimeSeries('a', data={datetime(2018,1,i):i for i in range(10,20,3)}), 2)
    >>> lagger.get_dates()
    [datetime.datetime(2018, 1, 16, 0, 0), datetime.datetime(2018, 1, 19, 0, 0)]
    >>> lagger.get_values(lagger.get_dates())
    [10, 13]
    """
   
    def __init__(self, timeSeries, shift_days=0):
        self.name = timeSeries.name
        self.title = timeSeries.title
        self.unit = timeSeries.unit
        self.shift_days = shift_days

        self.data = self.get_right_shifted_data(timeSeries)
        self.first_date = min(self.data)
        self.last_date = max(self.data)

    def get_right_shifted_data(self, timeSeries):
        data = {}
        for key, value in timeSeries.data.items():
            days_to_add = self.shift_days
            while days_to_add > 0:
                key += timedelta(days=1)
                if key > timeSeries.last_date:
                    break
                if key in timeSeries.data:
                    days_to_add -= 1
                else:
                    continue
            if key <= timeSeries.last_date:        
                data[key] = value
        return data
 
class returns(TimeSeries):
    """Time series that is profit ratio of buying the asset at time t[0]
    and selling it at time t[n]. Value is (t[n]-t[0])/t[0].
    >>> inv = returns(TimeSeries('a', data={datetime(2018,1,i):i for i in range(10,20,3)}), 1)
    >>> inv.get_dates()
    [datetime.datetime(2018, 1, 13, 0, 0), datetime.datetime(2018, 1, 16, 0, 0), datetime.datetime(2018, 1, 19, 0, 0)]
    >>> inv.get_values(inv.get_dates()) == [3/10, 3/13, 3/16]
    True
    """
    def __init__(self, timeSeries, hold_days=0):
        self.name = timeSeries.name
        self.title = timeSeries.title
        self.unit = timeSeries.unit
        self.hold_days = hold_days
        self.data = self.get_return_data(timeSeries)
        self.first_date = min(self.data)
        self.last_date = max(self.data)

    def get_return_data(self, timeSeries):
        data = {}
        for key, value in timeSeries.data.items():
            old_date = key
            days_to_add = self.hold_days
            while days_to_add > 0:
                key += timedelta(days=1)
                if key > timeSeries.last_date:
                    break
                if key in timeSeries.data:
                    days_to_add -= 1
                else:
                    continue
            if key <= timeSeries.last_date:        
                data[key] = (timeSeries.data[key] - value)/value
                #data[key] = Fraction(timeSeries.data[key] - value,value)
        return data


if __name__=='__main__':
    #Bundesbank('BBEX3.D.XAU.USD.EA.AC.C04')
    #times = TimeSeries('a', data={datetime(2018,1,i):i for i in range(10,20,3)})
    #print(times.get_dates())
    #lagger = lag(times, 2)
    #print(lagger.get_dates())
    #print(lagger.get_values(lagger.get_dates()))
    #times = TimeSeries('a', data={datetime(2018,1,i):i for i in range(10,20,3)})
    #print(times.data)
    #inv = returns(times,1)
    #print(inv.get_dates())
    #print(inv.get_values(inv.get_dates()) == [3/10, 3/13, 3/16])

    print(gold_spot().correlation(dgs10() - dgs3mo()))
    

    signal = dgs10() - dgs3mo()
    #print(signal.data)
    gold = gold_spot()
    buy_lag = 3
    hold_time = 20
    investment = returns(gold, hold_time)
    compare_to = lag(signal, buy_lag + hold_time)
    signal_to_result_correlation = investment.correlation(compare_to)
    print(signal_to_result_correlation)

    
    

       
