# Long_Intraday_Trend_Model

This project is a direct attempt to automate as much of my trading decisions as I see fit under different circumstances.

This program allows me autonomously to:
1) exit a trade based on a crude 1:2 reward (after manual entry)
2) exit a trade using overextended indicators (after manual or autonomous entry)
3) enter a trade and exit am intraday trending stock (after manually analyzing a stock and determining it's fit for a strategy)
4) scan through trending stocks based StockTwits Trending feed and filer them to show in-play long potentials

This program also now supports simulations for different technical analysis functions defined in Risk_Reward.py file (manual date and ticker name)

!!! Run TD_Console.py for a menu !!!

Some of the pivotal libraries in this project: Selenium (+Splinter), TA, Pandas, Requests, Time 

Currently used APIs : TD Ameritrade, Finn Hub, StockTwits
