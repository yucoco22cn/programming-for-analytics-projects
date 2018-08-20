"""P1, Yue Yu, cpsc 5910, R18, Seattle University
 
visualize(player) - simulate and plot results of a blackjack strategy
simulate(player) - simulate playing an evening's worth of blackjack
overlay_bell_curve(mu, sigma, n, bins) - plot a normal curve atop an 
                                    histogram in current pylab figure
"""

from Blackjack import Blackjack, Soft17, Basic
from CardDeck import CardDeck
from Card import Card
import numpy as np
import pylab
from math import pi, sqrt, e

def simulate(player,
             dealer=Soft17(),
             hands=100,
             ndecks=6,
             penetration=0.7,
             nplayers=7):
    """simulate playing an evening's worth of blackjack
    :param player:           Blackjack object representing the player
    :param dealer:           Blackjack object representing the dealer
    :param hands:            Number of hands to simulate
    :param ndecks:           Number of decks in each shoe
    :param penetration:      Depth of shoe before reshuffling
    :param nplayers:         Number of other players present (not simulated, but cards seen)
    :return: (final, lo, hi) player's accumulated winnings
    """

    def simulateOneHand(player, dealer, nplayers):
        player.payoff(0)
        dealer.payoff(0)

        otherPlayerCards = []
        playerCards = []
        dealerCards = []

        # bet
        money = player.bet()

        # first round
        for i in range(nplayers):
            otherPlayerCards.append(cardDeck.deal())
        playerCards.append(cardDeck.deal())
        dlr_up = cardDeck.deal()
        dealerCards.append(dlr_up)
        # second round
        for i in range(nplayers):
            otherPlayerCards.append(cardDeck.deal())
        playerCards.append(cardDeck.deal())
        dealerCards.append(cardDeck.deal())

        player.dealt(playerCards)
        dealer.dealt(dealerCards)
        
        # dealer has blackjack
        if(dealer.has_bj()):
            if(player.has_bj()):
                return 0
            else:
                return -1 * money
        
        # player
        choice = player.choose(dlr_up)
        isDouble = False
        while(choice != 'stay'):
            if(choice == 'double'):
                isDouble = True
                money = money * 2
            player.hit(cardDeck.deal())
            if(player.busted() or isDouble):
                break
            choice = player.choose(dlr_up)

        # dealer
        choice = dealer.choose(dlr_up)
        while(choice != 'stay'):
            dealer.hit(cardDeck.deal())
            if(dealer.busted()):
                break
            choice = dealer.choose(dlr_up)

        # compare
        if(player.beats(dealer)):
            return money
        elif(dealer.beats(player)):
            return -1*money
        else:
            return 0

    def summary(final, lo, hi, current):
        final += current
        lo = final if final < lo  else lo
        hi = final if final > hi else hi
        return (final, lo, hi)

    cardDeck = CardDeck(ndecks)
    cardDeck.shuffle()
    totalCount = cardDeck.count()

    final = 0
    lo = 10000
    hi = -10000

    for i in range(hands):
        money = simulateOneHand(player, dealer, nplayers)
        (final, lo, hi) = summary(final, lo, hi, money)
        if cardDeck.undealt()< penetration*totalCount:
            cardDeck.shuffle()
            player.new_shoe()
            dealer.new_shoe()

    return (final, lo, hi)

def visualize(trials, player=Basic()):
    """simulate and plot results of a blackjack strategy
    :param trials:   number of trials to simulate
    :param player:   player Blackjack object to simulate
    """
    dealer=Soft17()
    hands=100
    ndecks=6
    penetration=0.7
    # total player = nplayers +1
    nplayers=6

    binsNumber = 20
    #finalRecords={}
    records=[]
    for i in range(trials):
        (final, lo, hi) = simulate(player, dealer, hands, ndecks, penetration, nplayers)
        #finalRecords[final]=finalRecords.get(final, 0) +1
        records.append(final)
    mu = np.mean(records)
    sigma = np.std(records)
    times, winnings, patches = pylab.hist(records,binsNumber,edgecolor="None")

    worstMoment = min(records)
    pylab.xlim(min(mu-3.5*sigma, min(winnings)), max(mu+3.5*sigma, max(winnings)))
    ymin,ymax=pylab.ylim()

    if isinstance(player, CardCounting):
        title = 'winnings for {0}-hand night of Blackjack,\n \$10-\$1000 wager, hi-lo counting({1} trials)'.format(hands, trials)
    else:
        title = 'winnings for {0}-hand night of Blackjack,\n \$100 wager, basic strategy ({1} trials)'.format(hands, trials)
       
    pylab.title(title)
    pylab.xlabel('\$-winnings')
    pylab.ylabel('Trials')
    pylab.annotate('Mean= \$'+str(mu),xy=(mu,ymax*9/10))
    pylab.annotate('Std.Dev= \$'+str(int(sigma)),xy=(mu+sigma,(ymax-ymin)/2))
    pylab.annotate('Worst Moment= \$'+str(worstMoment),xy=(worstMoment,(ymax-ymin)/5))
    pylab.annotate('', 
                    xy=(worstMoment,0),
                    xytext=(worstMoment,(ymax-ymin)/5),
                    horizontalalignment='center',
                    arrowprops={'arrowstyle': '->', 'lw': 4, 'color': 'red'})
    c=[mu-3*sigma,mu-2*sigma,mu-sigma,mu,mu+sigma,mu+2*sigma,mu+3*sigma]
    for i in c:
        pylab.axvline(x=i, ymin=0, ymax=1, hold=None, color='gray',linestyle='dashed') 
    overlay_bell_curve(mu, sigma, trials, binsNumber)


def overlay_bell_curve(mu, sigma, n, bins):
    """Overlay a normal curve atop an histogram on current pylab figure.
    :param mu:    mean
    :param sigma: standard deviation
    :param n:     number of events tracked in histogram
    :param bins:  number of bins in histogram
    """
    left=mu-sigma*3.5
    right=mu+sigma*3.5
    x=np.linspace(left,right,1000)

    scale=bins*(abs(left-right)/bins)*(n/bins)

    def f(x):
        return e**(-((x-mu)**2)/(2*sigma**2)) / (sigma*sqrt(2*pi))
        """probability density function of normal distribution"""
    
    pylab.plot(x,f(x)*scale)


class CardCounting(Basic):
    """Hi-lo card counting ideal strategy."""
    count = 0

    def title(self):
        """Descriptive heading for reports for this player"""
        return 'Hi-lo card counting strategy'

    def bet(self):
        """Gets the bet from the player prior to the hand being played"""
        if self.count<=0:
            return 10
        elif self.count == 1:
            return 50
        elif self.count == 2:
            return 100
        elif self.count == 3:
            return 200
        elif self.count == 4:
            return 500
        else:
            return 1000

    def new_shoe(self):
        """Called when the deck has been reshuffled"""
        self.count = 0

    def sees(self, cards):
        """Informs the player of any visible cards besides those she has been dealt"""
        for card in cards:
            if card.rank_value() <=6:
                self.count += 1
            elif card.rank_value() >= 10:
                self.count -= 1

if __name__ == "__main__":
    trials = 1000
    basicPlayer=Basic()
    pylab.figure()
    pylab.subplot(2,1,1)
    visualize(trials, basicPlayer)

    pylab.subplot(2,1,2)
    cardCourtingPlayer=CardCounting()
    visualize(trials, cardCourtingPlayer)
    pylab.tight_layout()
    pylab.show()   
