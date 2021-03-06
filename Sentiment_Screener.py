## using server authentication. so first authentication token and then access token 
# 1. this file will request data of the trending stocks using stocktwit api
#  2.and will filter through the results, finding stocks with the ideal share float, percentage gain for the day
#  3. think of how you can incorporate spy and its % because it definitely plays a role 
# i will have a command that will bring me 5 min updates
#use finnhub to get current days close and yesterdays close to determine change %
from Config import st_client_id, st_client_secret, st_twt_user, st_twt_pass
from datetime import datetime
from splinter import Browser
from time import sleep
import FH_News_API_Calls as FH_N
import pandas as pd
import requests
import urllib
import csv




class Sentiment_Screener:

	def __init__(self):
		self.auth_code = None
		self.access_code = None
		self.list_of_names = []
		self.filtered_stocks = []
		self.second_time_writing = False

		# ^ create a new instance of the chrome browser

	#the first time launching the program
	# 1) first part is selenium
	# 2) second part is gettin the token
	def authorize_stock_twit(self):

		#create a new instance of the chrome browser
		executable_path = {'executable_path' : r'C:\Users\isaks\Desktop\chromedriver\chromedriver'}
		browser = Browser('chrome', **executable_path, headless = True )

		#running the first time to get the url of the 
		endpoint = "https://api.stocktwits.com/api/2/oauth/authorize"

		payload = {'client_id' : st_client_id,
				'response_type' : 'code',
				'redirect_uri' : 'https://www.google.com/',
				} 

		method = 'GET'

		#build the url
		build_url = requests.Request(method, endpoint, params= payload).prepare()
		build_url = build_url.url
		build_url 
			
		browser.visit(build_url)


		browser.find_by_id("user_session_login").fill(st_twt_user)
		browser.find_by_id("user_session_password").fill(st_twt_pass)
		browser.find_by_xpath("//input[@name='commit']").first.click()


		new_url = browser.url

		auth_code = urllib.parse.unquote(new_url.split('code=')[1])

		#browser.quit()
		
		### getting the token 
		endpoint = "https://api.stocktwits.com/api/2/oauth/token" 

		payload = { 'client_id' : st_client_id,
					'code' : auth_code,
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

		local_list = []

		for name in data['symbols']:
			local_list.append(name['symbol'])
		
		self.list_of_names = local_list

		print(local_list)

	#passing all trending stocks throught finn hubb api to find gapped up stocks 
	#change that you are comparing to close of 3:59 of the prev day.
	def filter_trending(self):

		local_filtered = []

		for stock in self.list_of_names:
			#returning a dict with two keys of last day's close and current price
			data_d = FH_N.prev_day_data(stock)
			try:
				change = (data_d['now'] - data_d['prev']) / data_d['prev']
				if change > 0.05:
					local_filtered.append(stock)
					#run only once during the process
					if self.second_time_writing == False:
						print(stock)
						# run the first yahoo headline. if its trending, there is a higher probability of news
						print(FH_N.yahoo_news_scraping(stock))
						print()
			except:
				pass

		self.filtered_stocks = local_filtered

		print(local_filtered)

		
		# want this operation run only once a day, but here i protect myself running more than once within one executable run
		# restrction for the day is set in write function itself
		if self.second_time_writing == False:
			#writing todays tickers into the file
			self.write_filtered()
			self.second_time_writing = True

		#cleanning up the lists to process in the same lists during the smae run
		self.filtered_stocks.clear()
		self.list_of_names.clear()
 
	
	# this function writes todays trending stocks into a csv, which holds last 20 trading days
	# it moves data from a file into a dataframe, adds one row to the bottom, sorts df so that row gets to the top, and writes the completed df to the same file
	# room for improvement:
	# very inefficient because i am copying everything from one file, sort inefficiently, and write everything back to the file
	# BE CAREFUL using this function on weekends, check if saturday, sunday and not do the writing
	def write_filtered(self):

		try:
			recent_tickers = pd.read_csv("recent_runners.csv")
			today_date = str(datetime.date(datetime.now()))

			#.values returns dataframe's each row as numpy array 
			#return if todays date is already recorded
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

	# retrieves tickers from csv, 
	#^  checks the % change beteween today and yesterday 
	# converts symbol into company name, and uses news api, to check if they have news TODAY
	def read_filtered_and_news(self):
		# retrieve all tickers from 3 existing columns, 
		recent_tickers = pd.read_csv("recent_runners.csv")

		list_for_news = []

		#getting available tickers from a row
		for ticker in recent_tickers.values:
			if ticker[1] != 'None':
				list_for_news.append(ticker[1])
			if ticker[2] != 'None':
				list_for_news.append(ticker[2])
			if ticker[3] != 'None':
				list_for_news.append(ticker[3])

		today_date = datetime.date(datetime.now())
		for ticker in list_for_news:
			#converting ticker symbol into company's official name
			name = FH_N.yahoo_scraping(ticker)
			article = FH_N.news_ticker(name, today_date)
			if article != None:
				print(ticker)
				print(article)
				print (" ")
				
		return 

	#checking today's news for a given stock
	def check_todays_news(self, a_ticker):
		today_date = datetime.date(datetime.now())
		name = FH_N.yahoo_scraping(a_ticker)
		article = FH_N.news_ticker(name, today_date)
		print(article)

		return 


	# all the functions needed to get current trending tickers from StockTwit
	def all_in_one(self):

		self.authorize_stock_twit()
		self.request_trending()
		self.filter_trending()
