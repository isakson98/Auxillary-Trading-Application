from Config import finn_hub, news_api
import pandas as pd
from datetime import date, timedelta, datetime
import time
import requests
import json
import csv


## THIS class requests unfiltered data from Finn Hubb

##consider how to avoid replacing certain parameters current vs. historical data search
#concern solved = both calls have count instead of to/from (parallelism), so I can use the same calls for different functions, like hot exit or auto entry 




#for momentum
def one_min_data(stock_ticker): 

	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	payload = { 'symbol' : stock_ticker,
				'resolution' : 1,
				'token' : finn_hub,
				'count' : 10
				#'from' : 1585318341, #10:00:14 AM 1585202114 temp
				#'to' : 1585325541    # 11:50:14 PM
	}

	content = requests.get(url = endpoint, params = payload)

	one_min_data = content.json()

	return one_min_data

#for calculating technical indicators
def one_min_data_csv(ticker): 

	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	payload = { 'symbol' : ticker,
				'resolution' : 1,
				'count' : 90, #7 temp
				'token' : finn_hub,
	}

	content = requests.get(url = endpoint, params = payload)

	one_min_data = content.text
	data_pd = pd.read_json(one_min_data)
	data_pd.drop(columns = ['s'], inplace = True)
	data_pd.columns = ['Close','High', 'Low', 'Open', 'Timestamp' ,'Volume']
	data_pd['Close'] = round(data_pd['Close'],2)
	data_pd['High'] = round(data_pd['High'],2)
	data_pd['Low'] = round(data_pd['Low'],2)
	data_pd['Open'] = round(data_pd['Open'],2)

	return data_pd

#for simulation
def one_min_data_simulation(open_order_info):

	#going back 100 minutes (candles) to get accurate RSI for the first candle
	#subbing 4 hours cause its UTX and we in est
	#and adding 9:30 hours to get the open time
	backtrack =  open_order_info['time'] - 3000  # subbing 15 candles
	end_of_strat = backtrack + 12600 + 3000  #ending at 1 pm (+2.5 hours + 100 minutes)
	# print(backtrack)
	print("end of ", end_of_strat)
	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	payload = { 'symbol' : open_order_info['ticker'],
				'resolution' : 1,
				'token' : finn_hub,
				'to' : end_of_strat,
				'from' : backtrack 
				}

	content = requests.get(url = endpoint, params = payload)

	one_min_data = content.text
	data_pd = pd.read_json(one_min_data) #,index=[0])
	data_pd.drop(columns = ['s'], inplace = True)
	data_pd.columns = ['Close','High', 'Low', 'Open', 'Timestamp' ,'Volume']
	data_pd['Close'] = round(data_pd['Close'],2)
	data_pd['High'] = round(data_pd['High'],2)
	data_pd['Low'] = round(data_pd['Low'],2)
	data_pd['Open'] = round(data_pd['Open'],2)
	data_pd['Cold Entry'] = data_pd.apply(lambda row: 0, axis=1)
	data_pd['Hot Exit'] = data_pd.apply(lambda row: 0, axis=1)

	return data_pd

#for 5 min trend
def five_min_data(ticker):
	endpoint = 'https://finnhub.io/api/v1/stock/candle'


	payload = { 'symbol' : ticker,
				'resolution' : 5,
				'count' : 5, #getting the last 4 candles #uncomment
				'token' : finn_hub,

	}

	content = requests.get(url = endpoint, params = payload)

	five_min_data = content.json()

	return five_min_data

#for calculating technical indicators
def five_min_data_csv(ticker): 

	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	payload = { 'symbol' : ticker,
				'resolution' : 5,
				'count' : 20, 
				'token' : finn_hub
	}

	content = requests.get(url = endpoint, params = payload)

	five_min_data = content.text
	data_pd = pd.read_json(five_min_data)
	data_pd.drop(columns = ['s'], inplace = True)
	data_pd.columns = ['Close','High', 'Low', 'Open', 'Timestamp' ,'Volume']
	data_pd['Close'] = round(data_pd['Close'],2)
	data_pd['High'] = round(data_pd['High'],2)
	data_pd['Low'] = round(data_pd['Low'],2)
	data_pd['Open'] = round(data_pd['Open'],2)

	return data_pd

#for simulation
def five_min_data_simulation(open_order_info):

	#going back 100 minutes (candles) to get accurate RSI for the first candle
	#subbing 4 hours cause its UTX and we in est
	#and adding 9:30 hours to get the open time
	backtrack =  open_order_info['time'] - 3000  # subbing 15 candles
	end_of_strat = backtrack + 12600 + 3000  #ending at 1 pm (+2.5 hours + 100 minutes)
	# print(backtrack)
	print("end of ", end_of_strat)
	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	payload = { 'symbol' : open_order_info['ticker'],
				'resolution' : 5,
				'token' : finn_hub,
				'to' : end_of_strat,
				'from' : backtrack 
				}

	content = requests.get(url = endpoint, params = payload)

	one_min_data = content.text
	data_pd = pd.read_json(one_min_data) #,index=[0])
	data_pd.drop(columns = ['s'], inplace = True)
	data_pd.columns = ['Close','High', 'Low', 'Open', 'Timestamp' ,'Volume']
	data_pd['Close'] = round(data_pd['Close'],2)
	data_pd['High'] = round(data_pd['High'],2)
	data_pd['Low'] = round(data_pd['Low'],2)
	data_pd['Open'] = round(data_pd['Open'],2)
	data_pd['Cold Entry'] = data_pd.apply(lambda row: 0, axis=1)
	data_pd['Hot Exit'] = data_pd.apply(lambda row: 0, axis=1)

	return data_pd


#for filtering through data coming from stock twits
# i need to access 3pm of last trading day to compare %change.
# using hourly data as that is going to be the shortest intraday json
def prev_day_data(open_order_info):
	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	#getting yesterday's date
	yesterday = (datetime.now() - timedelta(1)).date()

	#converting yesterdays date to unix seconds and adding 15 hours, going to get the close value of the power hour 
	timestamp = time.mktime(time.strptime(str(yesterday), '%Y-%m-%d'))
	timestamp += 54000
	#mondays
	if (date.today().isoweekday() == 1):
		timestamp -= 172800 # subbing two days to account for saturday and sunday

	#sunday
	elif (date.today().isoweekday() == 7):
		timestamp -= 86400 # subbing 1 day to account for saturday


	payload = { 'symbol' : open_order_info,
			'resolution' : '60',
			'token' : finn_hub,
			'to' : time.time(), 
			'from' : timestamp 
	}

	content = requests.get(url = endpoint, params = payload)
	
	day = content.json()

	if day['s'] == 'no_data':
		return

	#if can't find the value of the last days 3pm
	try:
		time_of_last_min = int(day['t'].index(timestamp))
	except:
		return

	# a lof of data is returning for a whole month for some reason,
	# so i specify that I want to find from a specific hour
	# time consuming but it works
	prev_day_now_close = {'prev' : day['c'][time_of_last_min],
							'now' : day['c'][-1]}

	return prev_day_now_close


#getting news from NewsAPI
def news_ticker(a_ticker, date):

	convert_date = date.isoformat()

	endpoint = "https://newsapi.org/v2/everything?q={}".format(a_ticker)

	params = { 'apiKey' : news_api,
				'from' : convert_date,
				'domains' : 'yahoo.com',
				'language' : 'en'

	}

	content = requests.get(url = endpoint, params = params)

	news = content.json()

	try:
		news = news['articles'][0]['title']
	except:
		return

	return news 
