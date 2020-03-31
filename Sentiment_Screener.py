## 1. this file will request data of the trending stocks using stocktwit api
#  2.and will filter through the results, finding stocks with the ideal share float, percentage gain for the day
#  3. think of how you can incorporate spy and its % because it definitely plays a role 
# i will have a command that will bring me 5 min updates
#use finnhub to get current days close and yesterdays close to determine change %
from Config import st_client_id, st_client_secret, st_twt_user, st_twt_pass
from selenium.webdriver.chrome.options import Options
from splinter import Browser
from time import sleep
from Finn_Hub_API_Calls import Finn_Hub_API_Calls
import requests
import urllib



class Sentiment_Screener:

	def __init__(self):
		self.auth_code = None
		self.access_code = None
		self.list_of_names = []
		self.finn_data = Finn_Hub_API_Calls()
		self.filtered_stocks = []

	def authorize_stock_twit(self):
		#options = Options()
		#options.add_argument("window-size=800,500")
		executable_path = {'executable_path' : r'C:\Users\isaks\Desktop\chromedriver_win32\chromedriver'}

		#create a new instance of the chrome browser
		browser = Browser('chrome', **executable_path, headless = True)


		endpoint = "https://api.stocktwits.com/api/2/oauth/authorize"

		payload = {'client_id' : st_client_id,
				   'response_type' : 'code',
				   'redirect_uri' : 'https://www.tdameritrade.com/home.page',
				   } 

		method = 'GET'
		#build the url
		build_url = requests.Request(method,endpoint, params= payload).prepare()
		build_url = build_url.url

		#go to the url
		browser.visit(build_url)

		browser.find_by_id("user_session_login").fill(st_twt_user)
		browser.find_by_id("user_session_password").fill(st_twt_pass)
		browser.find_by_xpath("//input[@name='commit']").first.click()

		#browser.find_by_xpath("//a[@class='button btn-glow allow']").first.click()

		new_url = browser.url

		auth_code = urllib.parse.unquote(new_url.split('code=')[1])

		self.auth_code = auth_code

		#print(auth_code)

		
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

		#print(data)

	def request_trending(self):

		endpoint = "https://api.stocktwits.com/api/2/trending/symbols/equities.json"

		payload = { 'limit' : 20,
					'access_token' : self.access_code }

		content = requests.get(url = endpoint, params = payload)

		data = content.json()

		#print(data)

		for name in data['symbols']:
			self.list_of_names.append(name['symbol'])

		print(self.list_of_names)

	def filter_trending(self):

		for stock in self.list_of_names:
			data_d = self.finn_data.day_data(stock)
			try:
				change = (data_d['c'][1] - data_d['c'][0]) / data_d['c'][0]
				if change > 0.05:
					#print(stock)
					self.filtered_stocks.append(stock)
			except:
				pass

		print(self.filtered_stocks)
		self.filtered_stocks.clear()
		self.list_of_names.clear()

	def all_in_one(self):
		self.authorize_stock_twit()
		self.get_access_token()
		self.request_trending()
		self.filter_trending()
