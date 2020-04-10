# Long_Intraday_Trend_Model

This project is a direct attempt to automate as much of my trading decisions as I see fit under different circumstances. It still needs a lot of supervision, like telling which stocks to trade and what the risk is for a trade, like in automatic entry

This program allows me autonomously to:
1) exit a trade based on a crude 1:2 reward (after manual entry)
2) exit a trade using overextended indicators (after manual or autonomous entry)
3) enter a trade and exit am intraday trending stock (after manually analyzing a stock and determining it's fit for a strategy)
4) a) scan through trending stocks based StockTwits Trending feed and filer them to show in-play long potentials
   b) check for today's news of the 60 stocks in play of the last 20 sessions

This program also now supports simulations for different technical analysis functions defined in Risk_Reward.py file (manual date and ticker name)

!!! Run TD_Console.py for a menu !!!

Some of the pivotal libraries in this project: Selenium (+Splinter), TA, Pandas, Requests, Time 

Currently used APIs : TD Ameritrade, Finn Hub, StockTwits, ApiNews

You need your own accounts and register your own applications to input passwords (I stored mine in Config.py)
