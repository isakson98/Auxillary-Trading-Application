from Config import finn_hub, news_api, yahoo_rap, yah_host
import pandas as pd
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
import time
import requests
import json
import csv


## THIS class requests unfiltered data from Finn Hubb and filters it according to the needs of TA module and the code already in place for calc


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

	payload = { 'symbol' : 'WORX', #ticker,
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
	#print("end of ", end_of_strat)
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
	backtrack =  open_order_info['time'] - 3000   # subbing 15 candles #subbing more to show 20 ema calc earlier
	end_of_strat = backtrack + 12600 + 3000  #ending at 1 pm (+2.5 hours + 100 minutes)
	# print(backtrack)
	#print("end of ", end_of_strat)
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
# ^ not adjsuted for holidays
# i need to access 3pm of last trading day to compare %change.
# using hourly data as that is going to be the shortest intraday json
# using default argument for real time checking, 2nd parameter to include timestamp from simulation
def prev_day_data(open_order_info , now = datetime.now()):
	endpoint = 'https://finnhub.io/api/v1/stock/candle'

	#creating a copy to save the timestamp value
	datetime_now = now

	# if it is a simulation, convert timestamp to datetime.datetime object
	if isinstance(now, (datetime)) == False:
		datetime_now = datetime.fromtimestamp(now)
	#getting yesterday's date
	yesterday = (datetime_now - timedelta(1)).date()

	#converting yesterdays date to unix seconds and add 15 hours, going to get the close value of the power hour 
	timestamp = time.mktime(time.strptime(str(yesterday), '%Y-%m-%d'))
	timestamp += 54000

	#mondays
	if (date.today().isoweekday() == 1):
		timestamp -= 172800 # subbing two days to account for saturday and sunday 
		#timestamp -= 86400 # for holidays # temp

	#sunday
	elif (date.today().isoweekday() == 7):
		timestamp -= 86400 # subbing 1 day to account for saturday

	json_now = None
	# it is a simulation if 'now' is a timestamp because that's what I am passing from Risk_Reward
	if isinstance(now, (datetime)) == False:
		json_now = float(now)
	#otherwise it's realtime
	else:
		json_now = time.time()
		

	payload = { 'symbol' : open_order_info,
			'resolution' : '60',
			'token' : finn_hub,
			'to' : json_now, 
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
		print("returned")
		return

	# a lof of data is returning for a whole month for some reason,
	# so i specify that I want to find from a specific hour
	# time consuming but it works
	prev_day_now_close = {'prev' : day['c'][time_of_last_min],
							'now' : day['c'][-1]}

	return prev_day_now_close



#using an api from the website, which is just as slow as what I am doing myself
def yahoo_api(a_ticker):

	endpoint = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/get-detail"

	header = {
		"x-rapidapi-host": yah_host,
		"x-rapidapi-key": yahoo_rap
	}

	payload = { 
		"region" : "US",
		"lang" : "en",
		"symbol" : a_ticker
	}

	content = requests.get(url = endpoint, headers = header, params = payload)

	news = content.json()

	return news['price']['shortName']


# web scraping personall y from the yahoo website
# returns the full name of the company as a string
def yahoo_scraping(a_ticker):

	endpoint = "https://finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch".format(a_ticker, a_ticker)

	#request object
	page = requests.get(endpoint)

	#access text portion of the object -> page.text
	soup = BeautifulSoup(page.text, 'html.parser')
	
	#grabbing tag and its content
	ticker_name = soup.find('h1')

	soup = BeautifulSoup((str(ticker_name)), features="lxml")
	td = soup.find('h1')

	# the format i am gettin is [TSLA - Tesla, Inc.]
	ticker_name = td.contents[0]

	ticker_name = ticker_name.split("- ")

	ticker_name = ticker_name[1].split(',')
	return ticker_name[0]

#returns the first news headline found on the yahoo page of the company
#disadvantage: i do cannot extract date of the article, which loses the point of 
def yahoo_news_scraping(a_ticker):

	endpoint = "https://finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch".format(a_ticker, a_ticker)

	#request object
	page = requests.get(endpoint)

	#access text portion of the object -> page.text
	soup = BeautifulSoup(page.text, 'html.parser')

	#grabbing tag and its content for the news headline
	ticker_news = soup.find('h3', {"class" : "Mb(5px)"})
	ticker_news = str(ticker_news).split("-->")
	ticker_news = str(ticker_news[1]).split("<!--")

	return ticker_news[0]


#getting news from NewsAPI
#using the name of the company in the title as query
#sends todays headlines, but is inconsistent (does not have all the articles.)
def news_ticker(a_ticker, date):

	convert_date = date.isoformat()

	endpoint = "https://newsapi.org/v2/everything?qInTitle={}".format(a_ticker)
	#endpoint = "https://newsapi.org/v2/everything?q={}".format(a_ticker)

	params = { 'apiKey' : news_api,
				'from' : convert_date,
				'domains' : 'yahoo.com',
				'language' : 'en'

	}

	content = requests.get(url = endpoint, params = params)
	news = content.json()

	#ideally i need to find the name of the company and search that in the headline

	try:
		news = news['articles'][0]['title']
		return news
	except:
		return
		

 
