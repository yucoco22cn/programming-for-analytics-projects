from TimeSeries import dgs3mo, dgs10, gold_spot
from datetime import datetime
import matplotlib.pyplot as plt
from scipy import stats
def recession_visual():
    """Plot a graphic visual showing the inverted yield curve"""
    short = dgs3mo()
    long = dgs10()
    gold=gold_spot()
    dates = short.get_dates(start=datetime(1968, 4, 1))
    dates = long.get_dates(dates)
    dates=gold.get_dates(dates)
    diff = long - short
    y_diff = diff.get_values(dates)
    y_gold=gold.get_values(dates)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plot1=ax.plot(dates, y_gold)
    axr = ax.twinx() 
    plot2=axr.plot(dates, y_diff,color='red')
    fig.autofmt_xdate()  # nice dates on x axis
    ax.legend(plot1+plot2, ['gold_spot','dgs10-dgs3mo'], loc='best')
    ax.set_title('Gold vs. Yeild Curve Inversion')
    ax.set_xlabel('date')
    ax.set_ylabel('USD')
    axr.set_ylabel(r'percent')
    ax.set_ylim(250, 1750)
    axr.set_ylim(-1,5)
    axr.axhline(linewidth=1, color='r')
    plt.show()

if __name__=='__main__':
    #Bundesbank('BBEX3.D.XAU.USD.EA.AC.C04')
    recession_visual()