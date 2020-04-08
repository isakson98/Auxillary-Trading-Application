## using server authentication. so first authentication token and then access token 
# 1. this file will request data of the trending stocks using stocktwit api
#  2.and will filter through the results, finding stocks with the ideal share float, percentage gain for the day
#  3. think of how you can incorporate spy and its % because it definitely plays a role 
# i will have a command that will bring me 5 min updates
#use finnhub to get current days close and yesterdays close to determine change %
from Config import st_client_id, st_client_secret, st_twt_user, st_twt_pass
from splinter import Browser
from time import sleep
from Finn_Hub_API_Calls import Finn_Hub_API_Calls
import requests
import urllib
import pickle



class Sentiment_Screener:

	def __init__(self):
		self.auth_code = None
		self.access_code = None
		self.list_of_names = []
		self.finn_data = Finn_Hub_API_Calls()
		self.filtered_stocks = []
		self.auth_url = None

		# #create a new instance of the chrome browser
		# executable_path = {'executable_path' : r'C:\Users\isaks\Desktop\chromedriver_win32\chromedriver'}
		# self.browser = Browser('chrome', **executable_path, headless = True )
	
	#beta
	#saving cookies from the first time
	def save_cookies(self, browser):
		path = "./cookies/stock_twits.txt"
		pickle.dump(browser.cookies.all(), open(path, "wb"))

	#beta
	#loading cookies into subsequent launches of the browser
	def load_cookies(self, browser):
		path = "./cookies/stock_twits.txt"
		cookies = pickle.load(open(path, "rb"))
		browser.cookies.delete()

		#have to be on some page to start 
		browser.visit("https://google.com")
		for cookie in cookies:
			print(cookie)
			#browser.cookies.add(cookie)

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

		#cleanning up the lists to process in the same lists during the smae run
		self.filtered_stocks.clear()
		self.list_of_names.clear()

	def all_in_one(self):

		self.authorize_stock_twit()
		self.get_access_token()
		self.request_trending()
		self.filter_trending()
