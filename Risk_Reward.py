## this class is for calculations:
# 1. Retrives my latest Opening trades on the TD platform of today's date (records a new order in the file with today's date)
# 2. Retrieves intraday price data -> Finn Hub (the most viable option, with accurate results in the fastest time) 
# 3. Calculates:
#    A. R/R (1:2) based on the entry and the lowest 5 min low of the last two candles (intraday trend)
#    B. R/R (1:2) based on the lowest low after the high in a pullback (momentum)
#    C. Hot exit 						(run through model integrated)
#    D. Cold entry (based on macd, rsi) + its risk (1. 20 min low, 2. atr * factor, 2. current 5 min 10 ema low)		    (run through model integrated)
# 4. It is also capable of running simulations on intraday basis if ticker and date are specified

import FH_News_API_Calls as FH_N
from TD_API_Calls import TD_price_history
from datetime import datetime
from dateutil import parser
import time 
import requests
import json
import winsound
import pandas as pd
import ta

Money_to_Risk = 1


class Risk_Reward:

	def __init__(self):
		self.open_order_info = {'time': 0, 'ticker' : 0, 'shares' : 0, 'price' : 0, }
		self.risk_reward_setup ={'risk': 0, 'current': 0, 'reward': 0, 'shares' : 0, 'ticker' : 0, 'time' : 0, 'result': 0}
		self.five_min_data = None
		self.one_min_data = None
		self.data_pd = None
		self.vwap_dict = None
		self.spy_pd = None
		self.spy_yest = None
		self.pro_loss_list = []
		

	# saving opened orders into a file 
	# in case I will reopen the program and will be prompted to apply r/r again
	def push_new_orders_in_file(self, new_order):
		today_date = datetime.date(datetime.now())
		f = open("./old_open_orders/{}".format(str(today_date) + '.txt'),"a")
		result = json.dumps(new_order) 
		f.write(result + '\n')
		f.close()

	#checking the incoming orders to make sure they haven't been dealt with before 
	#by opening the file in which they should have been written in previously, had they been already viewed
	def check_if_open_order_old(self, received_order):
		today_date = datetime.date(datetime.now())
		name_of_file = str(today_date) + '.txt'
		result = json.dumps(received_order)

		try:
			f = open("./old_open_orders/{}".format(name_of_file),"r")
			contents_lines = f.readlines()
			for x in contents_lines:
				if x == (result + '\n'):
					f.close()
					return True
			f.close()
			return False
		except:
			f = open("./old_open_orders/{}".format(name_of_file),'w+')
			f.close()
			return False

	# function finds most recent manually entered orders in TD_ameritrade account
	def checking_opening_positions(self, data): #cheking Opening positions

		received_order_info = {}

		#locating opening position and grabbing the time stamp, the name, # of share
		for opening in data:
			if opening['orderLegCollection'][0]['positionEffect'] == 'OPENING':
				received_order_info['time'] = opening['orderActivityCollection'][0]['executionLegs'][0]['time']
				received_order_info['ticker'] = opening['orderLegCollection'][0]['instrument']['symbol']
				received_order_info['shares'] = opening['quantity']
				received_order_info['price'] = opening['orderActivityCollection'][0]['executionLegs'][0]['price']
				if self.check_if_open_order_old(received_order_info) == True:
					print("No new orders")
					return "None"
				else:
					winsound.Beep(1000, 980)
					self.open_order_info = received_order_info
					print("Found new opened order: {}".format(received_order_info))
					#self.push_new_orders_in_file(received_order_info) temp
					return received_order_info['ticker']

		print("No new orders")
		return "None"

	#formatting function
	#converting 2020-03-18T15:24:09+0000 into epoch time (milliscons), for -> TD and finn hub api send request
	def time_conversion_retrieved_into_send(self):
		date = parser.parse(self.open_order_info['time'], ignoretz=True)
		epoch = datetime.utcfromtimestamp(0)
		self.open_order_info['time'] = ((date - epoch).total_seconds() * 1000.0)
		return

	#formating function
	#given the iteration, it finds the timestamp of the index and converts into legible format
	def sec_into_time_convert(self, iterations):
		unix_sec = self.data_pd['Timestamp'].iloc[iterations]
		date = datetime.fromtimestamp(unix_sec)
		date = (date.strftime('%Y-%m-%d %H:%M:%S'))
		return date

	# for manually entered trades
	# calculates 1 Risk / 2 Reward ratio, basing the risk off of either the current or previous lowest 5 min low
	def five_min_calc_r_r(self, stock_ticker): #3.0
		self.five_min_data = FH_N.five_min_data(stock_ticker)
		self.time_conversion_retrieved_into_send()

		test_candle_time = self.open_order_info['time'] / 1000  - 60 # - 14400 #adjusting to seconds and local time
		test_candle_time = test_candle_time - test_candle_time % 300 # get 5 min candle that test candle was part of 
		

		# get the index of the 5 min candle where the 1 min entry candle is
		time_of_last_5min = self.five_min_data['t'].index(test_candle_time) 
		#get the low of 5min, entry acndle was in 
		current_five_min = self.five_min_data['l'][time_of_last_5min] 
		#get the 5min low before that
		prev_five_min = self.five_min_data['l'][time_of_last_5min - 1]          

		#compare the two 
		five_min_stop_loss = current_five_min - 0.03 if current_five_min < prev_five_min else prev_five_min -0.03
		target = round((self.open_order_info['price'] - 0.03 + (self.open_order_info['price'] - five_min_stop_loss) * 1.9), 2)

		self.risk_reward_setup = {'risk' : round(five_min_stop_loss, 2),
									'reward' : target, 
									'shares' : int(self.open_order_info['shares']), 
									'ticker' : self.open_order_info['ticker']}

		print("Calculated 5 min R/R:  ",  self.risk_reward_setup)
		return self.risk_reward_setup


	# for manually entered trades
	# calculates 1 Risk / 2 Reward ratio, basing the risk off of the lowest low in 3-6 minute pullback (excluding the highest candle's low)
	# returns a dictionary with final values to close the trade at, ticker name, and # of shares bought in the opening trade
	def one_min_calc_r_r(self, stock_ticker): #3.0

		self.one_min_data = FH_N.one_min_data(stock_ticker)
		self.time_conversion_retrieved_into_send() 

		test_candle_time = self.open_order_info['time'] / 1000  - 60 #- 14400 #adjusting to seconds and local time
		test_candle_time = test_candle_time - test_candle_time % 60 # get 5 min candle that test candle was part of

		# get index of control candle
		time_of_last_min = int(self.one_min_data['t'].index(test_candle_time)) #1585057500

		#find the highest in the range of pullback
		pullback_list = self.one_min_data['h'][time_of_last_min-6:time_of_last_min+1] #including test candle
		pullback_list_low = self.one_min_data['l'][time_of_last_min-6:time_of_last_min+1] #including test candle
		highest_candle = max(pullback_list)

		#find the index of that highest candle
		index_o_highest = pullback_list.index(highest_candle)
		#find the lowest after the highest value
		lowest_after_highest = min(pullback_list_low[index_o_highest+1:])

		#get test candle high 
		test_high = pullback_list[-1]

		#r/r
		risk = round(lowest_after_highest - 0.03, 2)
		reward = round(((test_high - risk) * 2) + test_high, 2)

		self.risk_reward_setup = {'risk' : risk, 
									'reward' : reward, 
									'shares' : self.open_order_info['shares'], 
									'ticker' : self.open_order_info['ticker']}

		print("Calculated 1 min R/R: ", self.risk_reward_setup)
		return self.risk_reward_setup

########################################################################################################################################################################
# purely discretionary until this point

	# PROGRAMMING ASPECT BEHIND THE FUNCTION:
	#this is a multipurpose function
	#used for simulation and live trading as well
	#if simulation == 0 i will request new data and make new RSI, BB, MA calculations each time I access the function
	#if simulation == 1 i will only get data and do technical indicators in the first run
	#I will also employ a_iterations which will help with data access at different locations of the dataframe
	#in live trading a_iterations should be -1 and simulation == 0

	# TECHNICAL ANALYSIS ASPECT BEHIND THE FUNCTION:
	# this function calculates the last candle's technical indicators and its body composition to determine whether it is oversold and I need to exit
	# Requirements for entry: can pass by either one of the two conditions, based on body of the candle, rsi, and BB
	# finding the candles that when they are oversold, they have a small probability of going up
	# process behind it -> keep indicators overextended but not too much. 
	# instead add more different specifications to have more accurate results
	def hot_exit(self, ticker, simulation, a_iteration):

		# keeping these separate becasuse I am creating local smaller dataframes for real time trading to increase performance
		if simulation == 0:
			self.data_pd = FH_N.one_min_data_csv(ticker)

			# if the price has not reached 1.8X Reward (for some leevay), oversold != need to exit
			if self.data_pd['Close'].iloc[a_iteration] < self.risk_reward_setup['reward'] * 1.8:
				return False

			##RSI indicator -> very lagging, performs closer to reality 100 away from head
			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["High"], n=7)
			self.data_pd['rsiHigh'] = indicator_rsi.rsi()

			#library.file.class instance declaration
			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=7, ndev=2)
			self.data_pd['bb_bbh'] = round(indicator_bb.bollinger_hband(),2)

			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=20, ndev=2)
			self.data_pd['bb_bbh20'] = round(indicator_bb.bollinger_hband(),2)

			##SMA indicator 
			self.data_pd['SMA'] = self.data_pd['Close'].rolling(window=9).mean()


		#not going to need to request data the first time because I'll have it from cold entry
		#but I will calculate all technical analysis 
		elif simulation == 1 and 'bb_bbh' not in self.data_pd.columns:

			# if the price has not reached 2X Reward, oversold != need to exit
			if self.data_pd['Close'].iloc[a_iteration] < self.risk_reward_setup['reward'] * 1.8:
				return False

			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=7, ndev=2)
			self.data_pd['bb_bbh'] = round(indicator_bb.bollinger_hband(),2)

			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=20, ndev=2)
			self.data_pd['bb_bbh20'] = round(indicator_bb.bollinger_hband(),2)

			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["High"], n=7)
			self.data_pd['rsiHigh'] = indicator_rsi.rsi()

			self.data_pd['SMA'] = self.data_pd['Close'].rolling(window=9).mean()

		
		current = {'Close' : self.data_pd['Close'].iloc[a_iteration],
					'High': self.data_pd['High'].iloc[a_iteration], 
					'Low': self.data_pd['Low'].iloc[a_iteration], 
					'Open': self.data_pd['Open'].iloc[a_iteration],
					'Timestamp': self.data_pd['Timestamp'].iloc[a_iteration],
					'Volume' : self.data_pd['Volume'].iloc[a_iteration],
					'rsiHigh' : self.data_pd['rsiHigh'].iloc[a_iteration],
					'bb_bbh' : self.data_pd['bb_bbh'].iloc[a_iteration],
					'bb_bbh20' : self.data_pd['bb_bbh20'].iloc[a_iteration], 
					'SMA' : self.data_pd['SMA'].iloc[a_iteration]
		}

		prev = {'Close' : self.data_pd['Close'].iloc[a_iteration-1],
				'High': self.data_pd['High'].iloc[a_iteration-1], 
				'Low': self.data_pd['Low'].iloc[a_iteration-1], 
				'Open': self.data_pd['Open'].iloc[a_iteration-1],
				'Timestamp': self.data_pd['Timestamp'].iloc[a_iteration-1],
				'Volume' : self.data_pd['Volume'].iloc[a_iteration-1],
				'rsiHigh' : self.data_pd['rsiHigh'].iloc[a_iteration-1],
				'bb_bbh' : self.data_pd['bb_bbh'].iloc[a_iteration -1],
				'bb_bbh20' : self.data_pd['bb_bbh20'].iloc[a_iteration -1], 
				'SMA' : self.data_pd['SMA'].iloc[a_iteration - 1]
		}


		###store the last element in a dictionary object to avoid calling back this big df
		##candles
		smaller_body = abs(current['Close'] - current['Open']) < abs(prev['Close'] - prev['Open'])

		current_sum_oflow_high_wicks = abs(current['Low'] - current['High']) - abs(current['Open'] - current['Close'])

		wick_vs_body = abs(current['Open'] - current['Close']) < current_sum_oflow_high_wicks

		#rsi and candle combos
		wick_and_rsi_high = (current['rsiHigh'] > 80) and wick_vs_body

		#sma from BB
		extended_from_sma = (abs(current['High'] - current['Low']) < (current['Low'] - current['SMA']))
					
		time_now = self.sec_into_time_convert(a_iteration)


		middle_out_bb = (current['High'] > current['bb_bbh20']) and (current['rsiHigh'] >= 85) and smaller_body
		if middle_out_bb : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", time_now) 
			return True


		bb_and_current_wick_rsi = wick_and_rsi_high and extended_from_sma and smaller_body
		if bb_and_current_wick_rsi : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", time_now) 
			return True

		
		return False



	# PROGRAMMING ASPECT BEHIND THE FUNCTION:
	#if simulation == 0 i will keep on requesting new data and make new RSI and MACD calculations
	#if simulation == 1 i will only do the RSI and MACD Calculations once for the whole data set and NOT request new data each turn
	#I will also employ a_iterations which will help with data access at different locations of the dataframe
	#in live trading a_iterations should be -1 and sim == 0
	#in trading it will be growing in the loop wherever this function is called

	# TECHNICAL ANALYSIS ASPECT BEHIND THE FUNCTION:
	# I am calculating MACD histogram fields. I want to enter in a red field that has a closer candle to 0 than previous,
	# and I want the previous red candle to be smaller than the highest candle of the previous green field (in absolute terms)
	# At the same time, I want rsi to be lower than 67.5, so I am not buying something overextended, despite macd signal

	def cold_entry(self, a_ticker, simulation, a_iteration):

		self.open_order_info['ticker'] = a_ticker
		
		###########################################################################################
		# calcualting technical indicators
		#if I am doing real time trading, I need to request data every time I use this function 
		if simulation == 0:
			self.data_pd = FH_N.one_min_data_csv(a_ticker)
			#i want to see what is going on live, how delayed the data is coming in 
			print(self.data_pd['Timestamp'].iloc[a_iteration] )


		#only need to collect this data once for simulation. It will be saved from then on
		#Either live or simulation -> both need to access these indicator calculations at least once
		if simulation == 0 or (simulation == 1 and 'Macd' not in self.data_pd.columns):
			#MACD indicator
			indicator_macd = ta.trend.MACD(close=self.data_pd["Close"], n_slow = 26, n_fast = 12, n_sign = 9)
			#round to 4 decimal places as I will be trading cheap stocks quite frequently
			self.data_pd['Macd'] = round(indicator_macd.macd_diff(),4)

			##RSI indicator
			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["Close"], n=14)
			self.data_pd['RsiClose14'] = indicator_rsi.rsi()

			##VWAP indicator
			indicator_vwap = ta.volume.VolumeWeightedAveragePrice(high=self.data_pd["High"], low=self.data_pd["Low"], close=self.data_pd["Close"], volume=self.data_pd["Volume"], n=len(self.data_pd.index))
			self.data_pd['VWAP'] = indicator_vwap.volume_weighted_average_price()
	
		###########################################################################################
		# if there is content in this list, I will check if curren price has reached any of the r's of any of the variables
		# consider those that will not be in 1pm ^
		if self.pro_loss_list:
			for setup in self.pro_loss_list:
				# if i hit the stop loss
				if setup['risk'] >= self.data_pd['Low'].iloc[a_iteration] and setup['result'] == 0:
					# only update the value if it has been unitialized. Otherwise the results will always be what happened last
					setup['result'] = -1
				# if i hit 
				elif setup['reward'] <= self.data_pd['High'].iloc[a_iteration] and setup['result'] == 0:
					setup['result'] = 2


		# calculating the conditions
		# initizaliing variables that will be compared to
		# i do not want a_iteration variable changed, so i reassigned it
		if self.data_pd['VWAP'].iloc[a_iteration] > self.data_pd['Low'].iloc[a_iteration]:
			return False

		iterations_v2 = a_iteration
		lowest_macd = 0.0000 #this will remain 0.00 in case the previous
		highest_macd = -0.0001
		
		#if macd is positive "i will send it back"
		if self.data_pd['Macd'].iloc[iterations_v2] > 0.0000 and self.data_pd['Macd'].iloc[iterations_v2 - 1] > 0.0000:
			return False
		
		
		#current must be higher than prev and prev must be lower than prev-prev
		cond1 = self.data_pd['Macd'].iloc[iterations_v2] > self.data_pd['Macd'].iloc[iterations_v2 - 1] 
		cond2 = self.data_pd['Macd'].iloc[iterations_v2 - 1] < self.data_pd['Macd'].iloc[iterations_v2 - 2] 
		cond3 = self.data_pd['Macd'].iloc[iterations_v2 - 2] < 0.0000
		
		if cond1 and cond2 and cond3:
				lowest_macd = self.data_pd['Macd'].iloc[iterations_v2 - 1]
		else:
			return False
		
		#finding the lowest bar in current macd field
		while self.data_pd['Macd'].iloc[iterations_v2] <= 0.0000:
			#if in the same red field the current is closer to 0 then prev- > not interested 
			if self.data_pd['Macd'].iloc[iterations_v2] < lowest_macd:
				return False
			iterations_v2 -= 1
			
		#keeping the same counter to start iterating through the green field
		#finding the biggest value in the previous green MACD field 
		while self.data_pd['Macd'].iloc[iterations_v2] >= 0.0000:
			if self.data_pd['Macd'].iloc[iterations_v2] > highest_macd:
				highest_macd = self.data_pd['Macd'].iloc[iterations_v2]
			iterations_v2 -=1 

		#if the previous green field's highest candle is smaller than the lowest candle of current red field
		# I do not want to engage
		if abs(highest_macd) < abs(lowest_macd):
			return False

		# rsi should be below 67.5 for the current candle, so I am not buying anything overextended
		if self.data_pd['RsiClose14'].iloc[a_iteration] > 67.5:
			return False
		

		# why did i place this here? for the most part, having significant red SPY days is not common
		# and since I have about 2-5 entries a day in a ticker, all the other times would be wasted
		# if this was placed higher. I want to check after I KNOW this candles is an entry for sure,
		# BUT i haven't done the calculations for R/R (some efficiency), so I return False
		# ^ store spy as a separate series  with only closes for simulation
		change = 0
		#if real time i am just using he conventional approach as in the sentiment screener function
		if simulation == 0:
			spy_dict = FH_N.prev_day_data("SPY")
			change = (spy_dict['now'] - spy_dict['prev']) / spy_dict['prev']
		elif simulation == 1:
			current_time = self.data_pd['Timestamp'].iloc[a_iteration]
			spy_index = self.spy_pd.index[self.spy_pd['Timestamp'] == current_time]

			change = self.spy_pd['Close'].iloc[spy_index[0]]
			change = (change - self.spy_yest) / self.spy_yest

		# i only want to trade if SPY is > -2%
		if change < -0.02:
			time_now = self.sec_into_time_convert(a_iteration)
			print(a_ticker, ": No trade at: ", time_now, "| Reason: SPY is below yesterday's close too much")
			return False

		if simulation == 1:
			# keeping track of cold entries (for simulation purposes)
			self.data_pd.loc[a_iteration, 'Cold Entry'] = 1
		
		###########################################################################################
		#start the risk/reward decision process
		
		final_decision = self.cold_entry_risk_reward_5_emas(a_iteration, simulation, a_ticker)

		if final_decision == False:
			return False
			
		return True


	## THIRD TYPE OF RISK DEFINITION for cold entry (the other two are in previous versions)
	# this risk will be based on 5 min 8 ema or 20 ema
	# if 1 min close > 8 ema and abs(1 min high - 1min low) >= abs(1min low -1min close) = risk current 8 ema
	# if 1min close > 8 ema and abs(1min high - 1min low) < abs(1min low - 1min close) = risk 20 ema
	# if none of 4 of the last 5 min candles touch the 8ema, risk = current 8 ema
	# if 1min close < 8 ema = risk current 20 ema
	def cold_entry_risk_reward_5_emas(self, a_iteration, simulation, a_ticker):

		# saving 1 min index for calculating time before 5 min manipulation with it
		one_min_iteration = a_iteration

		#calculating current five min bar start
		time_5_min = self.data_pd['Timestamp'].iloc[a_iteration]
		time_5_min = time_5_min - time_5_min % 300 


		# converting current 1 min index into the index of 5 min dataframe
		if simulation == 1:
			min_5_index = self.five_min_data.index[self.five_min_data['Timestamp'] == time_5_min]
			a_iteration = min_5_index[0]


		###########################################################################################
		# getting data, calculating technical indicators
		#steps in if real trading 
		#requests five min data, calculates emas
		if simulation == 0:
			self.five_min_data = FH_N.five_min_data_csv(a_ticker)
			ema_8 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=8)
			self.five_min_data['ema_8'] = round(ema_8.ema_indicator(), 2)
			ema_20 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=20)
			self.five_min_data['ema_20'] = round(ema_20.ema_indicator(), 2)

		#steps in if first run in simulation
		# calculates emas
		elif (simulation == 1 and 'ema_8' not in self.five_min_data.columns):
			ema_8 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=8)
			self.five_min_data['ema_8'] = round(ema_8.ema_indicator(), 2)
			ema_20 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=20)
			self.five_min_data['ema_20'] = round(ema_20.ema_indicator(), 2)

		###########################################################################################
		#calculating conditions
		# if close > 8 ema and abs(high - low) >= abs(low - close) = risk current 8 ema
		extended = abs(self.five_min_data['ema_8'].iloc[a_iteration] - self.five_min_data['Low'].iloc[a_iteration]) >= abs(self.five_min_data['High'].iloc[a_iteration] - self.five_min_data['Low'].iloc[a_iteration]) 
		final_extended = extended and self.five_min_data['Low'].iloc[a_iteration] > self.five_min_data['ema_8'].iloc[a_iteration]
		
		#using current 1 min close for calculations cause im entering right after this candle finishes
		current_1_min = self.data_pd['Close'].iloc[one_min_iteration]
		risk = 0
		reward = 0

		#if none of 4 of the last 5 min candles touch the 8ema, risk = current 8 ema
		iterations_back = a_iteration
		above_8ema = 0
		while iterations_back != a_iteration - 3:
			if self.five_min_data['Low'].iloc[iterations_back] > self.five_min_data['ema_8'].iloc[iterations_back]:
				above_8ema += 1
			# #if 4th and 5th candle are also above 8ema, its overextended-> no trade
			# if self.five_min_data['Low'].iloc[a_iteration - 4] > self.five_min_data['ema_8'].iloc[a_iteration - 4] and self.five_min_data['Low'].iloc[a_iteration - 5] > self.five_min_data['ema_8'].iloc[a_iteration - 5]:
			# 	return False
			iterations_back -= 1

		###########################################################################################
		# assigning R/R based on conditions above
		# in case 5 min is overextended
		## ^ is this one necessary im counting 5min candles? seems like if this one is overextended, the prev onces do not touch
		if final_extended:
			risk = self.five_min_data['ema_8'].iloc[a_iteration] - 0.04
			reward = abs(current_1_min - self.five_min_data['ema_8'].iloc[a_iteration]) * 2 + current_1_min

		#if none of 3 of the last 5 min candles touch the 8ema, risk = current 8 ema
		elif above_8ema == 3:
			risk = self.five_min_data['ema_8'].iloc[a_iteration] - 0.04
			reward = abs(current_1_min - self.five_min_data['ema_8'].iloc[a_iteration]) * 2 + current_1_min

		#if current 5min low is below 20 ema, risk is low of 5 min
		elif self.five_min_data['ema_20'].iloc[a_iteration] > self.five_min_data['Low'].iloc[a_iteration]:
			risk = self.five_min_data['Low'].iloc[a_iteration] - 0.04
			reward = abs(current_1_min - self.five_min_data['Low'].iloc[a_iteration]) * 2 + current_1_min

		#in case 5 min is not overextended
		else:
			risk = self.five_min_data['ema_20'].iloc[a_iteration] - 0.04
			reward = abs(current_1_min - self.five_min_data['ema_20'].iloc[a_iteration]) * 2 + current_1_min

		shares = round(Money_to_Risk / (current_1_min - risk), 2)

		self.risk_reward_setup ={'risk': round(risk, 2),
								 'reward' : round(reward, 2), 
								 'shares' : shares, 
								 'ticker' : self.open_order_info['ticker']}

		time_now = self.sec_into_time_convert(one_min_iteration)
		self.risk_reward_setup['time'] = time_now
		self.risk_reward_setup['current'] = current_1_min
		self.risk_reward_setup['result'] = 0

		#if this is a simulation, i'll keep track of setups
		if a_iteration != -1:
			self.pro_loss_list.append(self.risk_reward_setup)

		return True



	#this function iterates through every minute of a specified stock between 9:30 (+some pre market) and 13:00 on a specified date
	#and prints out cold_entry, stop loss, target and first overbought indicator in a dataframe, which is then graphed out
	#this is a powerful function because it should accomodate every strategy I map out for any stock
	#this would allow me to see results of my strategy in the past (past 30 day limit which FinnHub imposes)
	def run_through_model(self, a_ticker, a_date):

		#specifying the start time (seconds, which backtracks a hundred candles and a whole day) 
		# beware of the GMT TIME DIFFERENCE SAVINGS LIGHT
		dates = pd.to_datetime([a_date])
		second = (dates - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s') 
		new_time = second[0] + 48600

		# only going in if this is the first run during executable
		# or a new date is different from the one that was tested before
		if self.spy_yest == None  or new_time != self.open_order_info['time']:
			#getting the prev day's close to compare the difference between now and then
			spy_dict = FH_N.prev_day_data("SPY", new_time)
			self.spy_yest = spy_dict['prev']
			#getting new dataframe
			self.spy_pd = TD_price_history("SPY", new_time, 1)

		
		#adds 9:30 hours to the date
		self.open_order_info['time'] = second[0] + 48600
		self.open_order_info['ticker'] = a_ticker
	

		#used for entry calculation
		self.data_pd = TD_price_history(a_ticker, new_time, 1)
		#used for stop loss calculation 
		self.five_min_data = TD_price_history(a_ticker, new_time, 5)

		
		#adding the four hour difference cause UNIX in GMT and + 9:30 hours to the open
		nine_30 = self.open_order_info['time']  #+ 3600 for day light savings time ALSO changein finn hubb
		#starting from the index of 9:30 am
		index_time = self.data_pd.index[self.data_pd['Timestamp'] == nine_30]
		start_time = index_time[0]
		
		# adding to 1pm  temp subtracting 2 minutes cause of a bug, which does not return last values without subtracting
		one_00 = nine_30 + 12600 - 120
		#finding the index of 1 PM
		index_finish_time = self.data_pd.index[self.data_pd['Timestamp'] == one_00]
		#taking the int element of the list that it provides
		finish_time = index_finish_time[0]
		
		while start_time != finish_time: 
			#self.hot_exit(a_ticker, 1, start_time) # not calculating hot exit because I have not found it reliable enough to start using it.
			self.cold_entry(a_ticker, 1, start_time)
			start_time +=1

		for setup in self.pro_loss_list:
			print("R/R : ", setup) 

		#clear for the next ticker
		self.pro_loss_list.clear()

		return 0
