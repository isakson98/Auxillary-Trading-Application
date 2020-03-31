#from datetime import datetime
from Config import finn_hub
import pandas as pd
import datetime as dt
import requests
import json
import csv


## THIS class requests unfiltered data from Finn Hubb

#i do not like 
##consider how to avoid replacing certain parameters current vs. historical data search
#concern solved = both calls have count instead of to/from (parallelism), so I can use the same calls for different functions, like hot exit or auto entry 
class Finn_Hub_API_Calls:

	#for 5 min trend
	def five_min_data(self, open_order_info):
		endpoint = 'https://finnhub.io/api/v1/stock/candle'

		#test_candle = 1584629852 #temp

		payload = { 'symbol' : open_order_info['ticker'],
					'resolution' : 5,
					'count' : 5, #getting the last 4 candles #uncomment
					'token' : finn_hub
		}

		content = requests.get(url = endpoint, params = payload)

		five_min_data = content.json()

		return five_min_data

	#for calculating technical indicators
	def five_min_data_csv(self, open_order_info): 

		endpoint = 'https://finnhub.io/api/v1/stock/candle'

		payload = { 'symbol' : open_order_info['ticker'],
					'resolution' : 5,
					'count' : 12, 
					'token' : finn_hub,
		}

		content = requests.get(url = endpoint, params = payload)

		one_min_data = content.text

		data_pd = pd.read_json(one_min_data)#,index=[0])
		data_pd.drop(columns = ['s', 'h', 'o'], inplace = True)
		data_pd.columns = ['Close', 'Low', 'Timestamp' ,'Volume']
		data_pd['Close'] = round(data_pd['Close'],2)
		data_pd['Low'] = round(data_pd['Low'],2)

		return data_pd



	#for momentum
	def one_min_data(self, open_order_info): 

		endpoint = 'https://finnhub.io/api/v1/stock/candle'

		payload = { 'symbol' : open_order_info['ticker'],
					'resolution' : 1,
					'token' : finn_hub,
					'count' : 10
					#'from' : 1585318341, #10:00:14 AM 1585202114 temp
					#'to' : 1585325541    # 11:50:14 PM
		}

		content = requests.get(url = endpoint, params = payload)

		one_min_data = content.json()

		return one_min_data

	#for simulation
	def one_min_data_simulation(self, open_order_info):

		#going back 100 minutes (candles) to get accurate RSI for the first candle
		#subbing 4 hours cause its UTX and we in est
		#and adding 9:30 hours to get the open time
		backtrack =  open_order_info['time'] - 3000 # subbing 15 candles
		end_of_strat = backtrack + 12600 + 3000 #ending at 1 pm (+2.5 hours + 100 minutes)
		# print(backtrack)
		# print(end_of_strat)
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


	#for calculating technical indicators
	def one_min_data_csv(self, open_order_info): 

		endpoint = 'https://finnhub.io/api/v1/stock/candle'

		payload = { 'symbol' : open_order_info['ticker'],
					'resolution' : 1,
					'count' : 90, #7 temp
					'token' : finn_hub,
		}

		content = requests.get(url = endpoint, params = payload)

		one_min_data = content.text
		data_pd = pd.read_json(one_min_data)#,index=[0])
		data_pd.drop(columns = ['s'], inplace = True)
		data_pd.columns = ['Close','High', 'Low', 'Open', 'Timestamp' ,'Volume']
		data_pd['Close'] = round(data_pd['Close'],2)
		data_pd['High'] = round(data_pd['High'],2)
		data_pd['Low'] = round(data_pd['Low'],2)
		data_pd['Open'] = round(data_pd['Open'],2)

		return data_pd

	#for filtering through data coming from stock twits
	def day_data(self, open_order_info):
		endpoint = 'https://finnhub.io/api/v1/stock/candle'

		#mondays
		if (dt.date.today().isoweekday() == 1):
			payload = { 'symbol' : open_order_info,
						'resolution' : 'D',
						'count' : 3, #getting the last 4 candles #uncomment
						'token' : finn_hub,
						#'to' : test_candle, #temp
						#'from' : '1584628232' #temp
			}
		#other days of the week
		else:
			payload = { 'symbol' : open_order_info,
						'resolution' : 'D',
						'count' : 2, #getting the last 4 candles #uncomment
						'token' : finn_hub,
						#'to' : test_candle, #temp
						#'from' : '1584628232' #temp
			}

		content = requests.get(url = endpoint, params = payload)

		day = content.json()
		#print(day)

		return day
