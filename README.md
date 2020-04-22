# Auxillary-Trading-Application

This is a multipurpose application to facilitate trading. It can be used for semi-autonomous and fully autonomous trading, for checking recent orders on brokerage platform, for as well as for simulating trading in the past runners.

This program allows me autonomously to:
1) exit a trade based on a crude 1:2 reward (after manual entry)
2) exit a trade using overextended indicators (after manual or autonomous entry)
3) enter a trade and exit intraday trending stock (after manually analyzing a stock and determining it's fit for a strategy)
4) a) scan through trending stocks based StockTwits Trending feed and filer them to show in-play long potentials
   b) check for today's news of 60 in play stocks of the last 20 sessions
5) run simulation on the last trending stocks, showing entries and exits

![image](https://user-images.githubusercontent.com/43397175/79826642-4247df80-836a-11ea-83f7-a95572522bd9.png)



Some of the pivotal libraries in this project: Selenium (+Splinter), TA, Pandas, Requests, Time 

Currently used APIs : TD Ameritrade, Finn Hub, StockTwits, ApiNews

You need your own accounts and register your own applications to for passwords and tokens.
