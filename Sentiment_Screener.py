## using server authentication. so first authentication token and then access token 
# 1. this file will request data of the trending stocks using stocktwit api
#  2.and will filter through the results, finding stocks with the ideal share float, percentage gain for the day
#  3. think of how you can incorporate spy and its % because it definitely plays a role 
# i will have a command that will bring me 5 min updates
#use finnhub to get current days close and yesterdays close to determine change %
from Config import st_client_id, st_client_secret, st_twt_user, st_twt_pass
from Finn_Hub_API_Calls import Finn_Hub_API_Calls
from datetime import datetime
from splinter import Browser
from time import sleep
import pandas as pd
import requests
import urllib
import csv




class Sentiment_Screener:

	def __init__(self):
		self.auth_code = None
		self.access_code = None
		self.list_of_names = []
		self.finn_data = Finn_Hub_API_Calls()
		self.filtered_stocks = []
		self.auth_url = None
		self.second_time_writing = False

		# #create a new instance of the chrome browser
		# executable_path = {'executable_path' : r'C:\Users\isaks\Desktop\chromedriver_win32\chromedriver'}
		# self.browser = Browser('chrome', **executable_path, headless = True )

	#the first time launching the program
	def authorize_stock_twit(self):

		#create a new instance of the chrome browser
		executable_path = {'executable_path' : r'C:\Users\isaks\Desktop\chromedriver_win32\chromedriver'}
		browser = Browser('chrome', **executable_path, headless = True )

		#running the first time to get the url of the 
		#if self.auth_url == None: #if statement start
		endpoint = "https://api.stocktwits.com/api/2/oauth/authorize"

		payload = {'client_id' : st_client_id,
				'response_type' : 'code',
				'redirect_uri' : 'https://www.google.com/',
				} 

		method = 'GET'

		#build the url
		build_url = requests.Request(method, endpoint, params= payload).prepare()
		build_url = build_url.url
		self.auth_url = build_url #if statement end
			
		browser.visit(self.auth_url)


		browser.find_by_id("user_session_login").fill(st_twt_user)
		browser.find_by_id("user_session_password").fill(st_twt_pass)
		browser.find_by_xpath("//input[@name='commit']").first.click()


		new_url = browser.url

		auth_code = urllib.parse.unquote(new_url.split('code=')[1])

		self.auth_code = auth_code

		#browser.quit()

	# getting an access token which is required for the api call i am going to make later
	def get_access_token(self):

		endpoint = "https://api.stocktwits.com/api/2/oauth/token" 

		payload = { 'client_id' : st_client_id,
					'code' : self.auth_code,
					'grant_type' : 'authorization_code',
					'client_secret' : st_client_secret,
					'redirect_uri' : "https://www.tdameritrade.com/home.page"}

		content = requests.post(url = endpoint, params = payload)

		data = content.json()

		self.access_code = data['access_token']

	#this function makes an api call to stock twits to retrieve most trending stocks in community
	#the list gets updates every 5 minutes
	def request_trending(self):

		endpoint = "https://api.stocktwits.com/api/2/trending/symbols/equities.json"

		payload = { 'limit' : 20,
					'access_token' : self.access_code }

		content = requests.get(url = endpoint, params = payload)

		data = content.json()

		for name in data['symbols']:
			self.list_of_names.append(name['symbol'])

		print(self.list_of_names)

	#passing all trending stocks throught finn hubb api to find gapped up stocks 
	#change that you are comparing to close of 3:59 of the prev day.
	def filter_trending(self):

		for stock in self.list_of_names:
			#returning a dict with two keys of last day's close and current price
			data_d = self.finn_data.prev_day_data(stock)
			try:
				change = (data_d['now'] - data_d['prev']) / data_d['prev']
				if change > 0.05:
					self.filtered_stocks.append(stock)
			except:
				pass

		print(self.filtered_stocks)

		
		# want this operation run only once a day, but here safety only set for one run of the program
		# for the day is set in write funcion itself
		if self.second_time_writing == False:
			#writing todays tickers into the file
			self.write_filtered()
			self.second_time_writing = True

		#cleanning up the lists to process in the same lists during the smae run
		self.filtered_stocks.clear()
		self.list_of_names.clear()
 
	
	# things to consider in development 
	# 1) when will i write the new stocks in? - so far i can only do it once a day
	# 2) what happens when I run the program twice in the day? will tickers be replaced or held the same? - held the same for now
	# 3) when will I check news for those stocks and will i do it repeatedly? - thats up to you, i can retrieve tickers any time (need to build a second option in console)
	# 4) what will be the process of deleting last date and its tickers? - from recent and down. deleting tail if > 20 tickers
	# 5) how will I cap number of stocks? go from api limit, but will I keep calender or just count of 20 days ex. - my api is maxed at 60 calls a minute, so 3 tickers * 20 days at once
	# 6) will I have to run this program every day? what happens if miss? - looks like for whatever days I miss, I'll add myself manually


	# this function writes todays trending stocks into a csv, which holds last 20 trading days
	# it moves data from a file into a dataframe, adds one row to the bottom, sorts df so that row gets to the top, and writes the completed df to the same file
	# room for improvement:
	# very inefficient because i am copying everything from one file, sort inefficiently, and write everything back to the file
	# BE CAREFUL using this function on weekends
	def write_filtered(self):

		try:
			recent_tickers = pd.read_csv("recent_runners.csv")
			today_date = str(datetime.date(datetime.now()))

			#.values returns dataframe's each row as numpy array 
			#return if todays tickers are already in frame
			for date in recent_tickers.values:
				if date[0] == today_date:
					print("Todays' tickers already recorded")
					return

			#deleting the last day if there are more than 20 days in the dataframe
			if len(recent_tickers.index) >= 20:
				recent_tickers.drop(recent_tickers.tail(1).index,inplace=True)

			#todays data to be added in the first row 
			data = {'date': str(today_date), 'ticker_1': self.filtered_stocks[0], 'ticker_2': self.filtered_stocks[1], 'ticker_3' :self.filtered_stocks[2]}
			
			#adding in chronological order
			recent_tickers.loc[-1] = data  # adding a row
			recent_tickers.index = recent_tickers.index + 1  # shifting index
			recent_tickers.sort_index(inplace=True) 
			recent_tickers.to_csv("recent_runners.csv", header = True, index = False)
				
		#in case I need to create a file first 
		except:
			with open('recent_runners1.csv', mode='w') as recent_runners_file:
				fieldnames = ['date', 'ticker_1', 'ticker_2', 'ticker_3']
				writer = csv.DictWriter(recent_runners_file, fieldnames=fieldnames)
				#always using to todays date to write 
				today_date = datetime.date(datetime.now())
				#writing in the csv file using dicts
				writer.writeheader()
				writer.writerow({'date': str(today_date), 'ticker_1': self.filtered_stocks[0], 'ticker_2': self.filtered_stocks[1], 'ticker_3' :self.filtered_stocks[2]})
		return 

	#retrieves tickers from csv and uses news api, to check if they have news
	def read_filtered_and_news(self):
		# retrieve all tickers from 3 existing columns, 
		# check for news, get the stocks that have news, 
		# show the news and ticker with it
		recent_tickers = pd.read_csv("recent_runners.csv")

		list_for_news = []

		for ticker in recent_tickers.values:
			list_for_news.append(ticker[1])
			list_for_news.append(ticker[2])
			list_for_news.append(ticker[3])


		today_date = datetime.date(datetime.now())
		for ticker in list_for_news:
			article = self.finn_data.news_ticker(ticker, today_date)
			if article != None:
				print(ticker)
				print(article)
				print (" ")
		return 

	# all the functions needed to get current trending tickers from StockTwit
	def all_in_one(self):

		self.authorize_stock_twit()
		self.get_access_token()
		self.request_trending()
		self.filter_trending()
