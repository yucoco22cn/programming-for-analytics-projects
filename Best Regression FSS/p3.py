"""P3, Yue Yu, cpsc 5910, R18, Seattle University

Classes:
TimeSeries - class to hold a date/value series of data
Fred - a time series that is based on a csv file downloaded from p3
USDForex-take the reciprical of values,
         has subclasses of foreign exchange series: chy, inr,krw,mxn,myr
USDCommodity-replicate prior days' values for all weekdays within the range
             for first to last dates
             has subclasses of commodity series: wti, copper,silver
Basket-investigate various proxy baskets (subsets of the whole risk basket)
"""

import os
import csv
from datetime import datetime, timedelta
import numpy as np
import itertools

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


class Fred(TimeSeries):
    def __init__(self, name, title=None, unit=None, data_column=None):
        """Opens and reads the csv file in DATA/name.csv"""
        super().__init__(name.lower(), title, unit)
        filename = os.path.join(DATA, name + '.csv')
        if data_column is None:
            data_column = name
        with open(filename) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                try:
                    value = float(row[data_column])
                except ValueError:
                    continue
                date = datetime.strptime(row['DATE'], "%Y-%m-%d")
                self.data[date] = value
        self.first_date = min(self.data)
        self.last_date = max(self.data)


class USDForex(Fred):
    """take the reciprical of values"""
    def __init__(self, data_column):
        super().__init__('fx_' + self.__class__.__name__, unit='USD', data_column=data_column)
        self.data = {d: 1/self.data[d] for d in self.data}
        self.name = self.__class__.__name__

class chy(USDForex):
    """Foreign exchange series of chy"""
    def __init__(self):
        super().__init__('DEXCHUS')  # data column is labeled DEXMAUS in file

class inr(USDForex):
    """Foreign exchange series of inr"""
    def __init__(self):
        super().__init__('DEXINUS')  # data column is labeled DEXINUS in file

class krw(USDForex):
    """Foreign exchange series of krw"""
    def __init__(self):
        super().__init__('DEXKOUS')  # data column is labeled DEXKOUS in file

class mxn(USDForex):
    """Foreign exchange series of mxn"""
    def __init__(self):
        super().__init__('DEXMXUS')  # data column is labeled DEXMXUS in file

class myr(USDForex):
    """Foreign exchange series of myr"""
    def __init__(self):
        super().__init__('DEXMAUS')  # data column is labeled DEXMAUS in file

class USDCommodity(Fred):
    """replicate prior days' values for all weekdays"""
    def __init__(self, name, data_column):
        super().__init__('cmdty_' + self.__class__.__name__, unit='USD', data_column=data_column)
        data = {}
        d = self.first_date
        last_value = self.data[d]
        while d <= self.last_date:
            if d in self.data:
                last_value=self.data[d]
            if d.weekday() < 5:  # Mon - Fri
                data[d]=last_value
            d += timedelta(days=1)
        self.data = data
        self.name = name

class copper(USDCommodity):
    """Commodity serires of copper"""
    def __init__(self):
        super().__init__(self.__class__.__name__, 'PCOPPUSDM')
            
class silver(USDCommodity):
    """Commodity serires of silver"""
    def __init__(self):
        super().__init__(self.__class__.__name__, 'PCU2122221222')


class wti(USDCommodity):
    """Commodity series of oil"""
    def __init__(self):
        super().__init__(self.__class__.__name__, 'DCOILWTICO')
 
class Basket(object):
    """investigate various proxy baskets (subsets of the whole risk basket)"""
    def __init__(self, baskets, weights):
        self.baskets_num = len(baskets)
        self.baskets=baskets
        self.weights=weights

        # get the first_date and last_date
        self.first_date = baskets[0].first_date
        self.last_date = baskets[0].last_date
        for basket in baskets:
            if self.first_date < basket.first_date:
                self.first_date = basket.first_date
            if self.last_date > basket.last_date:
                self.last_date = basket.last_date

        # get all the valid dates available in all the baskets
        self.valid_dates = baskets[0].get_dates(start = self.first_date, end = self.last_date)
        for i in range(1,len(baskets)):
            self.valid_dates = baskets[i].get_dates(candidates = self.valid_dates)

        self.basket_name_mapping = {}
        for i in range(len(baskets)):
            self.basket_name_mapping[baskets[i].name] = i

        self.response_all = {}
        for date in self.valid_dates:
            response = 0
            for i in range(len(baskets)):
                response += baskets[i].data[date] * self.weights[i]
            self.response_all[date] = response

    def regression(self, basket_names,first=None,last=None):
        m_subset = len(basket_names)

        if first is None:
            first = self.first_date
        else:
            first = max(first, self.first_date)
        if last is None:
            last = self.last_date
        else:
            last = min(last, self.last_date)
        dates = [date for date in self.valid_dates if first <= date <= last]
        predictors_T = []
        response = [self.response_all[date] for date in dates]
        for basket_name in basket_names:
            column_index = self.basket_name_mapping[basket_name]
            predictors_T.append(self.baskets[column_index].get_values(dates))
        intercept_column=np.empty(len(dates)); 
        intercept_column.fill(1/np.sqrt(m_subset))
        predictors_T.append(intercept_column)

        big_x_T = np.matrix(predictors_T, )
        big_x = big_x_T.T
        bold_y = np.matrix(response).T
        gramian = big_x_T * big_x
        beta_hat = gramian.I * big_x_T * bold_y
        residuals = bold_y - big_x * beta_hat
        
        result = {}
        beta = beta_hat.A[:, 0]
        for i in range(m_subset):
            result[basket_names[i]] = beta[i]
        result['intercept'] = beta[m_subset]
        result['rss'] = sum(residuals.A[:, 0] ** 2)
        result['start'] = first.strftime('%Y-%m-%d')
        result['end'] = last.strftime('%Y-%m-%d')
        return result

    def best_regression_n(self, k, first=None,last=None):
        all_combinations = self.get_all_combinations(k)
        min_rss = np.Inf
        for combination in all_combinations:
            result = self.regression(combination, first, last)
            if result['rss'] < min_rss:
                min_rss = result['rss']
                best_result = result
        return best_result

    def get_all_combinations(self, k):
        # get k numbers from 0 to self.baskets_num-1, then based on the index to get the selected baskets' names
        all_combinations_indexes = get_combinations(self.baskets_num,k)

        all_combinations = []
        for combinaiton_index in all_combinations_indexes:
            combination = []
            for index in combinaiton_index:
                combination.append(self.baskets[int(index)].name)
            all_combinations.append(combination)
        return all_combinations

    def best_regression_backtest(self, k, split_date):
        result = self.best_regression_n(k, last = split_date)
        first_day = split_date + timedelta(days=1)
        
        dates = [date for date in self.valid_dates if first_day <= date]
        response = [self.response_all[date] for date in dates]

        basket_names = []
        suggested_hedges = []
        for i in range(self.baskets_num):
            if self.baskets[i].name in result:
                basket_names.append(self.baskets[i].name)
                suggested_hedges.append(result[self.baskets[i].name])

        holdout_T = []
        for basket_name in basket_names:
            column_index = self.basket_name_mapping[basket_name]
            holdout_T.append(self.baskets[column_index].get_values(dates))

        big_x_T = np.matrix(holdout_T, )
        big_x = big_x_T.T
        bold_response = np.matrix(response).T
        bold_suggested_hedges = np.matrix(suggested_hedges).T

        delta = bold_response - big_x * bold_suggested_hedges
        return(np.std(delta))

def get_combinations(n,k):
    # get all the combinations: choose k numbers from 0 to n-1
    def combination_help(current, start, total, k, result):
        if (total-start+len(current) < k):
            return None
        for i in range(start, total):
            current.append(i)
            if len(current) == k:
                result.append(list(current))
            else:
                combination_help(current, i+1, total, k, result)
            current.pop()

    result = []
    combination_help([], 0,n,k, result)
    return result

if __name__ == "__main__":
    b = Basket([wti(), copper(), silver(), chy(), inr(), krw(), mxn(), myr()], [10485, 172, 13, 30e6, 57e6, 1.3e6, 94e6, 1.4e9])
    print(b.regression(['wti']))
    print(b.regression(['silver'], first=datetime(2001,1,1), last=datetime(2001,12,31)))
    print(b.regression(['wti', 'copper', 'krw', 'chy'], last=datetime(2001,1,23)))
    print(b.regression(['wti', 'copper', 'silver', 'chy', 'inr', 'krw', 'mxn', 'myr']))

    # Note that in best_regression_n, I found a small rss=7327826733475.723compare with the solution in the pdf
    print(b.best_regression_n(4, last=datetime(2004,7,1)))
    print(b.regression(['inr', 'krw', 'mxn', 'myr', ], last=datetime(2004,7,1)))  # solution in the pdf with 'rss': 96456734368157.03
    print(b.regression(['copper', 'chy', 'mxn', 'myr', ], last=datetime(2004,7,1))) # solution of my best_regression_n with 'rss': 7327826733475.723

    print(b.best_regression_backtest(4, datetime(2004,7,1)))

    
