# Auxillary-Trading-Application

This is a multipurpose application to facilitate trading. It can be used for semi-autonomous and fully autonomous trading, for checking recent orders on brokerage platform, for as well as for simulating trading in the past runners.

This program allows me autonomously to:
1) exit a trade based on a crude 1:2 reward (after manual entry)
2) exit a trade using overextended indicators (after manual or autonomous entry)
3) enter a trade and exit intraday trending stock (after manually analyzing a stock and determining it's fit for a strategy)
4) a) scan through trending stocks based StockTwits Trending feed and filer them to show in-play long potentials
   b) check for today's news of 60 in play stocks of the last 20 sessions
5) run simulation on the last trending stocks, showing entries and exits and result of each trade
6) stream time&sales data to output total volume done on uptick and downtick within 1 minute increments


![image](https://user-images.githubusercontent.com/43397175/81631660-582f4a00-93d6-11ea-956b-8427684ea4ca.png)


Some of the pivotal libraries in this project: Selenium (+Splinter), TA, Pandas, Requests, Time, Async 

Currently used APIs : TD Ameritrade, Finn Hub, StockTwits, ApiNews

You need your own accounts and register your own applications for each API.
