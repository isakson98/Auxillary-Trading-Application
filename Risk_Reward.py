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
from datetime import datetime
from dateutil import parser
import time 
import requests
import json
import winsound
import pandas as pd
import ta

Money_to_Risk = 10


class Risk_Reward:

	def __init__(self):
		self.open_order_info = {'time': 0, 'ticker' : 0, 'shares' : 0, 'price' : 0}
		self.risk_reward_setup ={'risk': 0, 'reward' : 0, 'shares' : 0, 'ticker' : 0}
		self.five_min_data = None
		self.one_min_data = None
		self.data_pd = None
		

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
					return False
				else:
					winsound.Beep(1000, 980)
					self.open_order_info = received_order_info
					print("Found new opened order: {}".format(self.open_order_info))
					self.push_new_orders_in_file(self.open_order_info)
					return True

		print("No new orders")
		return False

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
	def five_min_calc_r_r(self): #3.0
		self.five_min_data = FH_N.five_min_data(self.open_order_info)
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
		target = round((self.open_order_info['price'] + (self.open_order_info['price'] - five_min_stop_loss) * 1.9), 2)

		self.risk_reward_setup = {'risk' : five_min_stop_loss, 
									'reward' : target, 
									'shares' : int(self.open_order_info['shares']), 
									'ticker' : self.open_order_info['ticker']}

		print("Calculated 5 min R/R:  ",  self.risk_reward_setup)
		return self.risk_reward_setup


	# for manually entered trades
	# calculates 1 Risk / 2 Reward ratio, basing the risk off of the lowest low in 3-6 minute pullback (excluding the highest candle's low)
	# returns a dictionary with final values to close the trade at, ticker name, and # of shares bought in the opening trade
	def one_min_calc_r_r(self): #3.0

		self.one_min_data = FH_N.one_min_data(self.open_order_info)
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
	def hot_exit(self, simulation, a_iteration):


		#initializing in scope, so I can access later
		data_pd_short = None

		# keeping these separate becasuse I am creating local smaller dataframes for real time trading to increase performance
		if simulation == 0:
			self.data_pd = FH_N.one_min_data_csv(self.open_order_info)

			# if the price has not reached 2X Reward, oversold != need to exit
			if self.data_pd['Close'].iloc[a_iteration] < self.risk_reward_setup['reward']:
				return False

			##RSI indicator -> very lagging, performs closer to reality 100 away from head
			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["High"], n=7)
			self.data_pd['rsiHigh'] = indicator_rsi.rsi()

			# create a smaller df of the last 25 to calculate BB and bb20 and sma, to avoid inefficiency
			data_pd_short = self.data_pd.tail(25).copy()  
			#library.file.class instance declaration
			indicator_bb = ta.volatility.BollingerBands(close=data_pd_short["Close"], n=7, ndev=2)
			data_pd_short['bb_bbh'] = round(indicator_bb.bollinger_hband(),2)

			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=20, ndev=2)
			data_pd_short['bb_bbh20'] = round(indicator_bb.bollinger_hband(),2)

			##SMA indicator 
			data_pd_short['SMA'] = data_pd_short['Close'].rolling(window=9).mean()


		#not going to need to request data the first time because I'll have it from cold entry
		#but I will calculate all technical analysis 
		elif simulation == 1 and 'bb_bbh' not in self.data_pd.columns:

			# if the price has not reached 2X Reward, oversold != need to exit
			if self.data_pd['Close'].iloc[a_iteration] < self.risk_reward_setup['reward']:
				return False

			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=7, ndev=2)
			self.data_pd['bb_bbh'] = round(indicator_bb.bollinger_hband(),2)

			indicator_bb = ta.volatility.BollingerBands(close=self.data_pd["Close"], n=20, ndev=2)
			self.data_pd['bb_bbh20'] = round(indicator_bb.bollinger_hband(),2)

			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["High"], n=7)
			self.data_pd['rsiHigh'] = indicator_rsi.rsi()

			self.data_pd['SMA'] = self.data_pd['Close'].rolling(window=9).mean()


		#not active right now
		# this will be used either by realtime or simulation
		#data_pd_shorty = None
		# # to avoid repetitive calculations in simulation, I will repopulate 
		# if simulation == 0:
		# 	data_pd_shorty = data_pd_short.copy()
		# else:
		# 	data_pd_shorty = self.data_pd[a_iteration - 2 : a_iteration + 1].copy()

		##using dicts to avoid calling the last element of a big array using iloc (inefficient)
		#for the last 3 I am using the last element in either of the shortened lists
		
		current = {'Close' : self.data_pd['Close'].iloc[a_iteration],
					'High': self.data_pd['High'].iloc[a_iteration], 
					'Low': self.data_pd['Low'].iloc[a_iteration], 
					'Open': self.data_pd['Open'].iloc[a_iteration],
					'Timestamp': self.data_pd['Timestamp'].iloc[a_iteration],
					'Volume' : self.data_pd['Volume'].iloc[a_iteration],
					'rsiHigh' : self.data_pd['rsiHigh'].iloc[a_iteration],
					'bb_bbh' : self.data_pd['bb_bbh'].iloc[a_iteration],#data_pd_shorty['bb_bbh'].iloc[-1],
					'bb_bbh20' : self.data_pd['bb_bbh20'].iloc[a_iteration], #data_pd_shorty['bb_bbh20'].iloc[-1],
					'SMA' : self.data_pd['SMA'].iloc[a_iteration]
		}

		prev = {'Close' : self.data_pd['Close'].iloc[a_iteration-1],
				'High': self.data_pd['High'].iloc[a_iteration-1], 
				'Low': self.data_pd['Low'].iloc[a_iteration-1], 
				'Open': self.data_pd['Open'].iloc[a_iteration-1],
				'Timestamp': self.data_pd['Timestamp'].iloc[a_iteration-1],
				'Volume' : self.data_pd['Volume'].iloc[a_iteration-1],
				'rsiHigh' : self.data_pd['rsiHigh'].iloc[a_iteration-1],
				'bb_bbh' : self.data_pd['bb_bbh'].iloc[a_iteration -1],#data_pd_shorty['bb_bbh'].iloc[-2],
				'bb_bbh20' : self.data_pd['bb_bbh20'].iloc[a_iteration -1], #data_pd_shorty['bb_bbh20'].iloc[-2],
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
	# and I want this previous candle to be smaller than the highest candle of the previous green field (in absolute terms)
	# At the same time, I want rsi to be lower than 67.5, so I am not buying something overextended, despite macd 

	def cold_entry(self, ticker, simulation, a_iteration):

		self.open_order_info['ticker'] = ticker
		
		#if I am doing real time trading, I need to request data every time I use this function 
		if simulation == 0:
			self.data_pd = FH_N.one_min_data_csv(self.open_order_info)

		#only need to collect this data once for simulation. It will be saved from then on
		#Either live or simulation -> both need to access these indicator calculations
		if simulation == 0 or (simulation == 1 and 'Macd' not in self.data_pd.columns):
			#macd
			indicator_macd = ta.trend.MACD(close=self.data_pd["Close"], n_slow = 26, n_fast = 12, n_sign = 9)
			#print(indicator_macd)
			self.data_pd['Macd'] = round(indicator_macd.macd_diff(),4)

			##RSI indicator
			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["Close"], n=14)
			self.data_pd['RsiClose14'] = indicator_rsi.rsi()
			

		# will iterate through one negative macd before my test candle (which is supposed to be the start of green field) and one positive macd before that
		# i want to see the highest bar in green to be higher than the lowest bar in red (absolute value)
		iterations_v2 = a_iteration
		lowest_macd = 0.0000 #this will remain 0.00 in case the previous
		highest_macd = -0.0001
		
		#BASIC GIST OF THINGS -> 
		#iterating while current is in red and less then the previous candle (sign of strength)
		#comparing to the previous green field
		#the current histogram bar has to be red

		if self.data_pd['Macd'].iloc[iterations_v2] > 0.0000:
			return False
		
		
		#if current higher than prev and prev is lower than prevprev
		cond1 = self.data_pd['Macd'].iloc[iterations_v2] > self.data_pd['Macd'].iloc[iterations_v2 - 1] and self.data_pd['Macd'].iloc[iterations_v2] <= 0.0000
		cond2 = self.data_pd['Macd'].iloc[iterations_v2 - 1] < self.data_pd['Macd'].iloc[iterations_v2 - 2] and self.data_pd['Macd'].iloc[iterations_v2 -1] < 0.0000
		cond3 = self.data_pd['Macd'].iloc[iterations_v2 - 2] < 0.0000
		
		if cond1 and cond2 and cond3:
				lowest_macd = self.data_pd['Macd'].iloc[iterations_v2 - 1]
		else:
			return False
		
		#comparing in the red histogram field the current bar to the previous
		while self.data_pd['Macd'].iloc[iterations_v2] <= 0.0000:
			#if in the same red field the current is closer to 0 then prev- > not interested 
			if self.data_pd['Macd'].iloc[iterations_v2] < lowest_macd:
				return False
			iterations_v2 -= 1
			
		#keeping the same counter to start iterating through the green field
		#going through green, previous to the red field
		while self.data_pd['Macd'].iloc[iterations_v2] >= 0.0000:
			if self.data_pd['Macd'].iloc[iterations_v2] > highest_macd:
				highest_macd = self.data_pd['Macd'].iloc[iterations_v2]
			iterations_v2 -=1 


		#if the previous green field's highest candle is smaller than the lowest candle of previous red field
		# I do not want to engage
		if abs(highest_macd) < abs(lowest_macd):
			return False

		# rsi should be below 67.5 for the current candle, so I am not buying anything overextended
		if self.data_pd['RsiClose14'].iloc[a_iteration] > 67.5:
			return False
		
		#at this point a candle is a suitable sign for an entry position
		#keeping track of cold entries (for simulation purposes)
		if simulation == 1:
			self.data_pd.loc[a_iteration, 'Cold Entry'] = 1
		
		#start the risk/reward calculation
		#prompting user to select the stop loss
		answer = '0'
		if simulation == 0:
			while True:
				print("Select the stop loss [1] 20 min low, [2] candle ATR: ")
				answer = input()
				if (answer != '1') or (answer != '2'):
					break
		
		# if its a simulation calculating 20 by default
		elif simulation == 1:
			answer = '3'

		if answer == '1':
			self.cold_entry_risk_reward_20_min(a_iteration)
		elif answer == '2':
			self.cold_entry_risk_reward_atr(a_iteration, simulation)
		elif answer == '3':
			self.cold_entry_risk_reward_5_emas(a_iteration, simulation)

			
		return True

	## FIRST TYPE OF RISK DEFINITION
	# in case of using macd as the entry signal, the stop loss will be the lowest low in the last 15 minutes
	# same case in this function, passing the starting point, same as in the cold entry function
	# a_iteration = -1 in real time trading
	def cold_entry_risk_reward_20_min(self, a_iteration):

		iterations = a_iteration - 20
		lowest_low = self.data_pd['High'].iloc[a_iteration]


		#finding the lowest low of the last 10 minutes, including the 
		for candle in self.data_pd['Low'][iterations : a_iteration]:
			if lowest_low > candle:
				lowest_low = candle
			iterations += 1

	
		risk = round(lowest_low - 0.03, 2)
		reward = round(self.data_pd['High'].iloc[a_iteration] + ((self.data_pd['High'].iloc[a_iteration] - lowest_low) * 2), 2)

		shares = round(Money_to_Risk / (self.data_pd['High'].iloc[a_iteration] - lowest_low) * 2)

		self.risk_reward_setup ={'risk': risk,
								'reward' : reward, 
								'shares' : shares, 
								'ticker' : self.open_order_info['ticker']}

		time_now = self.sec_into_time_convert(a_iteration)
		print("R/R based on entry: ", self.risk_reward_setup, time_now ) 

		return True
	
	## FIRST TYPE OF RISK DEFINITION
	## this function calculates risk for a one-minute cold entry
	## using atr-type strategy, 
	def cold_entry_risk_reward_atr(self, a_iteration, simulation):

		Pd = 10 #period
		Factor = 2 

		self.data_pd['Up'] = 0.00

		#steps in if real trading or first simulation run
		if simulation == 0 or (simulation == 1 and 'Atr' not in self.data_pd.columns):
			atr = ta.volatility.AverageTrueRange(high=self.data_pd['High'], low= self.data_pd['Low'], close = self.data_pd['Close'], n=Pd)
			self.data_pd['Atr'] = round(atr.average_true_range(), 2)


		iterations = Pd 
		for atr in self.data_pd['Atr'][Pd : a_iteration]:

		    hl2 = (self.data_pd['High'].iloc[iterations] + self.data_pd['Low'].iloc[iterations]) / 2
		    hl2 = round(hl2,2)

		    up = hl2 - (Factor * atr)
		    up = round(up,2)


		    if self.data_pd['Up'].iloc[iterations-1] == 0:
		        up1 = up
		    else:
		        up1 = self.data_pd['Up'].iloc[iterations-1]

		    if self.data_pd['Close'].iloc[iterations-1] > up1:
		        self.data_pd.at[iterations,'Up'] = max(up, up1)
		    else:
		        self.data_pd.at[iterations,'Up'] = up

		    iterations += 1


		# ^ why do i have iterations here?
		risk = 0
		# if the last Low is lower than chandelier, I want my stop loss to be below Low
		if self.data_pd['Up'].iloc[iterations-1] > self.data_pd['Low'].iloc[iterations-1]:
			risk = self.data_pd['Low'].iloc[iterations-1] - 0.04
		else:
			risk = self.data_pd['Up'].iloc[iterations-1] - 0.04

		reward = self.data_pd['High'].iloc[iterations-1] + ((self.data_pd['High'].iloc[iterations-1] - risk) * 2)

		shares = round(Money_to_Risk / (self.data_pd['High'].iloc[iterations-1] - risk) * 2)


		self.risk_reward_setup ={'risk': risk,
								 'reward' : reward, 
								 'shares' : shares, 
								 'ticker' : self.open_order_info['ticker']}

		time_now = self.sec_into_time_convert(a_iteration)
		print("R/R based on entry: ", self.risk_reward_setup, time_now ) 

		return True


	## THIRD TYPE OF RISK DEFINITION
	# this risk will be based on 5 min 8 ema or 20 ema
	# if close > 8 ema and abs(high - low) >= abs(low - close) = risk current 8 ema
	# if close > 8 ema and abs(high - low) < abs(low - close) = risk 20 ema
	# if close < 8 ema = risk current 20 ema
	def cold_entry_risk_reward_5_emas(self, a_iteration, simulation):
# ^ find a way to convert current 1min index into the index of 5 min dataframe

		print(self.data_pd['Timestamp'].iloc[a_iteration])
		print(a_iteration)
		#getting five minute indeces
		if simulation == 1:
			a_iteration = self.five_min_data[self.five_min_data['Timestamp'].index.values]
		print(a_iteration)
		print(self.five_min_data['Timestamp'].iloc[a_iteration])

		#steps in if real trading 
		if simulation == 0:
			self.five_min_data = FH_N.five_min_data_csv(self.open_order_info)
			ema_8 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=8)
			self.five_min_data['ema_8'] = round(ema_8.ema_indicator(), 2)
			ema_20 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=20)
			self.five_min_data['ema_20'] = round(ema_20.ema_indicator(), 2)

		#steps in if first run in simulation
		elif (simulation == 1 and 'ema_8' not in self.five_min_data.columns):
			ema_8 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=8)
			self.five_min_data['ema_8'] = round(ema_8.ema_indicator(), 2)
			ema_20 = ta.trend.EMAIndicator(close = self.five_min_data['Close'], n=20)
			self.five_min_data['ema_20'] = round(ema_20.ema_indicator(), 2)

		# if close > 8 ema and abs(high - low) >= abs(low - close) = risk current 8 ema
		extended = abs(self.five_min_data['ema_8'].iloc[a_iteration] - self.five_min_data['Low'].iloc[a_iteration]) and abs(self.five_min_data['High'].iloc[a_iteration] - self.five_min_data['Low'].iloc[a_iteration]) 
		final_extended = extended and self.five_min_data['Low'].iloc[a_iteration] > self.five_min_data['ema_8'].iloc[a_iteration]

		risk = 0
		reward = 0
		
		# in case 5 min is overextended
		if final_extended:
			risk = self.five_min_data['ema_8'].iloc[a_iteration] - 0.04
			reward = abs(self.five_min_data['Close'].iloc[a_iteration] - self.five_min_data['ema_8'].iloc[a_iteration]) * 2 + self.five_min_data['Close'].iloc[a_iteration]
		#in case 5 min is not overextended
		else:
			risk = self.five_min_data['ema_20'].iloc[a_iteration] - 0.04
			reward = abs(self.five_min_data['Close'].iloc[a_iteration] - self.five_min_data['ema_20'].iloc[a_iteration]) * 2 + self.five_min_data['Close'].iloc[a_iteration]

		shares = round(Money_to_Risk / (self.data_pd['High'].iloc[a_iteration] - risk) * 2)

		self.risk_reward_setup ={'risk': risk,
								 'reward' : reward, 
								 'shares' : shares, 
								 'ticker' : self.open_order_info['ticker']}

		time_now = self.sec_into_time_convert(a_iteration)
		print("R/R based on entry: ", self.risk_reward_setup, time_now, self.five_min_data['ema_20'].iloc[a_iteration]) 










	#not safe against DAY TIME SAVINGS and HALTS ??
	#this function iterates through every minute of a specified stock between 9:30 (+some pre market) and 13:00
	#and records cold_entry, stop loss, target and first overbought indicator in a dataframe, which is then graphed out
	#this is a powerful function because it should accomodate every strategy I map out for any stock
	#this would allow me to see results of my strategy in the past (past 30 day limit which TradingView imposes)
	def run_through_model(self, name, date):
		#specifying the start time (seconds, which backtracks a hundred candles and a whole day) 
		# beware of the GMT TIME DIFFERENCE SAVINGS LIGHT
		dates = pd.to_datetime([date])
		second = (dates - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s') 
		
		self.open_order_info['time'] = second[0] + 48600
		self.open_order_info['ticker'] = name
		
		#used for entry
		self.data_pd = FH_N.one_min_data_simulation(self.open_order_info)
		#used for stop loss calculation 
		self.five_min_data = FH_N.five_min_data_simulation(self.open_order_info)

		
		#adding the four hour difference cause UNIX in GMT and + 9:30 hours to the open
		nine_30 = self.open_order_info['time']  #+ 3600 for day light savings time ALSO changein finn hubb
		#starting from the index of 9:30 am
		index_time = self.data_pd.index[self.data_pd['Timestamp'] == nine_30]
		start_time = index_time[0]
		
		
		one_00 = nine_30 + 12600 - 120# adding to 1pm  temp subtraction cause of a bug, which does not return last values
		#finding the index of 1 PM
		
		index_finish_time = self.data_pd.index[self.data_pd['Timestamp'] == one_00]
		#taking the int element
		finish_time = index_finish_time[0]
		
		while start_time != finish_time: 
			#self.hot_exit(1, start_time)
			self.cold_entry(self.open_order_info['ticker'], 1, start_time)
			start_time +=1

		
		return 0


	## concern -> include saved AND opened orders and be able to delete EITHER one of them as well
	## make it possible to look at two stocks at the same time (more than one) threading?
	## build a simulation class which can track profit or loss, not just entries
	## store cold entry + hot exit results on a minute bases and record in a separate dataframe, save it as a file with a name 
	## use AWS for password protection


	## 1)  multithreading -> build a GUI with two terminal windows which allow to have to processes at the same time
	## 2)  easy level would be to allow two threads to work on two different files (sentiment screener and cold entry)
	## 3)  medium level would be allowing two cold entries (I would need to create two object of the same file, obv)
