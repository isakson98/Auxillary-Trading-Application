## this class is for calculations:
# 1. Retrives my latest Opening trades on the TD platform of today's date (records a new order in the file with today's date)
# 2. Retrieves intraday price data -> Finn Hub (the most viable option, with accurate results in the fastest time) 
# 3. Calculates:
#    A. R/R (1:2) based on the entry and the lowest 5 min low of the last two candles (intraday trend)
#    B. R/R (1:2) based on the lowest low after the high in a pullback (momentum)
#    C. Hot exit 						(run through model integrated)
#    D. Cold entry + its risk		    (run through model integrated)
# 4. It is also capable of running simulations on intraday basis if ticker and date are specified

from Finn_Hub_API_Calls import Finn_Hub_API_Calls
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
		self.FH_connect = Finn_Hub_API_Calls()
		

	#saving opened orders for the day in case I will reopen the program and will be prompted to apply r/r again
	def push_new_orders_in_file(self, new_order):
		today_date = datetime.date(datetime.now())
		f = open("./old_open_orders/{}".format(str(today_date) + '.txt'),"a")
		result = json.dumps(new_order) 
		f.write(result + '\n')
		f.close()

	#checking the incoming orders to make sure they haven't been dealt with before 
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

	#converting 2020-03-18T15:24:09+0000 into epoch time (milliscons), for -> TD and finn hub api send request
	def time_conversion_retrieved_into_send(self):
		date = parser.parse(self.open_order_info['time'], ignoretz=True)
		epoch = datetime.utcfromtimestamp(0)
		self.open_order_info['time'] = ((date - epoch).total_seconds() * 1000.0)
		return

	# calculates 1 Risk / 2 Reward ratio, basing the risk off of either the current or previous lowest 5 min low
	def five_min_calc_r_r(self): #3.0
		self.five_min_data = self.FH_connect.five_min_data(self.open_order_info)
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



	# calculates 1 Risk / 2 Reward ratio, basing the risk off of the lowest low in 3-6 minute pullback (excluding the highest candle's low)
	# returns a dictionary with final values to close the trade at, ticker name, and # of shares bought in the opening trade
	def one_min_calc_r_r(self): #3.0

		self.one_min_data = self.FH_connect.one_min_data(self.open_order_info)
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
	#if simulation == 0 i will keep on requesting new data and make new RSI, BB, MA calculations
	#if simulation == 1 i will only do technical indicators once.
	#I am using a smaller dataframe for BB and MA calculations
	#I will also employ a_iterations which will help with data access at different locations of the dataframe
	#in live trading a_iterations should be -1 and simulation == 0

	# TECHNICAL ANALYSIS ASPECT BEHIND THE FUNCTION:
	# this function calculates the last candle's technical indicators and its body composition to determine whether it is oversold and I need to exit
	# finding the candles that when they are oversold, they have a small probability of going up
	#process behind it -> keep indicators overextended but not too much. 
	#instead add more different specifications to have more accurate results
	def hot_exit(self, simulation, a_iteration):

		# this will be used either by realtime or simulation
		data_pd_shorty = None

		#initializing in scope, so I can access later
		data_pd_short = None

		# keeping these separate becasuse I am creating local smaller dataframes for real time trading to increase performance
		if simulation == 0:
			self.data_pd = self.FH_connect.one_min_data_csv(self.open_order_info)

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


		# to avoid repetitive calculations in simulation, I will repopulate 
		if simulation == 0:
			data_pd_shorty = data_pd_short.copy()
		else:
			data_pd_shorty = self.data_pd[a_iteration - 2 : a_iteration + 1].copy()



		##using dicts to avoid calling the last element of a big array using iloc (inefficient)
		#for the last 3 I am using the last element in either of the shortened lists
		current = {'Close' : self.data_pd['Close'].iloc[a_iteration],
					'High': self.data_pd['High'].iloc[a_iteration], 
					'Low': self.data_pd['Low'].iloc[a_iteration], 
					'Open': self.data_pd['Open'].iloc[a_iteration],
					'Timestamp': self.data_pd['Timestamp'].iloc[a_iteration],
					'Volume' : self.data_pd['Volume'].iloc[a_iteration],
					'rsiHigh' : self.data_pd['rsiHigh'].iloc[a_iteration],
					'bb_bbh' : data_pd_shorty['bb_bbh'].iloc[-1],
					'bb_bbh20' :data_pd_shorty['bb_bbh20'].iloc[-1],
					'SMA' :data_pd_shorty['SMA'].iloc[-1]
		}

		prev = {'Close' : self.data_pd['Close'].iloc[a_iteration-1],
				'High': self.data_pd['High'].iloc[a_iteration-1], 
				'Low': self.data_pd['Low'].iloc[a_iteration-1], 
				'Open': self.data_pd['Open'].iloc[a_iteration-1],
				'Timestamp': self.data_pd['Timestamp'].iloc[a_iteration-1],
				'Volume' : self.data_pd['Volume'].iloc[a_iteration-1],
				'rsiHigh' : self.data_pd['rsiHigh'].iloc[a_iteration-1],
				'bb_bbh' : data_pd_shorty['bb_bbh'].iloc[-2],
				'bb_bbh20' : data_pd_shorty['bb_bbh20'].iloc[-2],
				'SMA' : data_pd_shorty['SMA'].iloc[-2]
		}


		###store the last element in a dictionary object to avoid calling back this big df
		##candles
		smaller_body = abs(current['Close'] - current['Open']) < abs(prev['Close'] - prev['Open'])

		current_sum_oflow_high_wicks = abs(current['Low'] - current['High']) - abs(current['Open'] - current['Close'])

		prev_sum_oflow_high_wicks = abs(prev['Low'] - prev['High']) - abs(prev['Open'] - prev['Close'])

		wick_vs_body = abs(current['Open'] - current['Close']) < current_sum_oflow_high_wicks

		sum_wick_dif = current_sum_oflow_high_wicks >= (2 * prev_sum_oflow_high_wicks)

		volume_low_price_high = current['Volume'] < prev['Volume'] and ((current['High'] - current['Low']) > 1.5 * (prev['High'] - prev['Low']))

		candle_middle = round((current['Low'] + (current['High'] - current['Low']) / 2), 2)


		#rsi and candle combos
		wick_and_rsi_high = (current['rsiHigh'] > 80) and wick_vs_body

		sum_prev_wick_rsi = (current['rsiHigh'] > 80) and sum_wick_dif

		#sma from BB
		extended_from_sma = (abs(current['High'] - current['Low']) < (current['Low'] - current['SMA']))
					

		# any one of these conditions is a good reason to exit, I do need to wait for all of them to finish
		## bb, rsi, candle combos 
		middle_out_bb = (candle_middle > current['bb_bbh20']) and (current['rsiHigh'] >= 85) and smaller_body
		if middle_out_bb : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", self.data_pd['Timestamp'].iloc[a_iteration])
			return True

		big_green_but_low_vol_and_rsi = (current['rsiHigh'] >=80) and volume_low_price_high and current['High'] >= prev['High'] and smaller_body
		if big_green_but_low_vol_and_rsi : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", self.data_pd['Timestamp'].iloc[a_iteration])
			return True

		bb_and_sum_prev_wick_rsi = (current['High'] >= current['bb_bbh']) and sum_prev_wick_rsi and smaller_body
		if bb_and_sum_prev_wick_rsi : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", self.data_pd['Timestamp'].iloc[a_iteration])
			return True

		bb_and_current_wick_rsi = wick_and_rsi_high and extended_from_sma and smaller_body
		if bb_and_current_wick_rsi : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", self.data_pd['Timestamp'].iloc[a_iteration])
			return True
			

		bb_and_current_wick_rsi_out = wick_and_rsi_high and (current['High'] >= current['bb_bbh']) and smaller_body
		if bb_and_current_wick_rsi_out : 
			self.data_pd.loc[a_iteration, 'Hot Exit'] = 1
			print("Hot Exit: ", self.data_pd['Timestamp'].iloc[a_iteration])
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
			self.data_pd = self.FH_connect.one_min_data_csv(self.open_order_info)

		#only need to collect this data once for simulation. It will be saved from then on
		#Either live or simulation -> both need to access these indicator calculations
		if simulation == 0 or (simulation == 1 and 'Macd' not in self.data_pd.columns):
			#macd
			indicator_macd = ta.trend.MACD(close=self.data_pd["Close"], n_slow = 26, n_fast = 12, n_sign = 9)
			#print(indicator_macd)
			self.data_pd['Macd'] = round(indicator_macd.macd_diff(),3)

			##RSI indicator
			indicator_rsi = ta.momentum.RSIIndicator(close=self.data_pd["Close"], n=14)
			self.data_pd['RsiClose14'] = indicator_rsi.rsi()
			

		# will iterate through one negative macd before my test candle (which is supposed to be the start of green field) and one positive macd before that
		# i want to see the highest bar in green to be higher than the lowest bar in red (absolute value)
		iterations_v2 = a_iteration
		lowest_macd = 0.000 #this will remain 0.00 in case the previous
		highest_macd = -0.001
		
		#BASIC GIST OF THINGS -> 
		#iterating while current is in red and less then the previous candle (sign of strength)
		#comparing to the previous green field
		#the current histogram bar has to be red
		if self.data_pd['Macd'].iloc[iterations_v2] > 0.000:
			return False
		
		
		#if current higher than prev and prev is lower than prevprev
		cond1 = self.data_pd['Macd'].iloc[iterations_v2] > self.data_pd['Macd'].iloc[iterations_v2 - 1] and self.data_pd['Macd'].iloc[iterations_v2] <= 0.000
		cond2 = self.data_pd['Macd'].iloc[iterations_v2 - 1] < self.data_pd['Macd'].iloc[iterations_v2 - 2] and self.data_pd['Macd'].iloc[iterations_v2 -1] < 0.000
		cond3 = self.data_pd['Macd'].iloc[iterations_v2 - 2] < 0.000
		
		if cond1 and cond2 and cond3:
				lowest_macd = self.data_pd['Macd'].iloc[iterations_v2 - 1]
		else:
			return False
		
		#comparing in the red histogram field the current bar to the previous
		while self.data_pd['Macd'].iloc[iterations_v2] <= 0.000:
			#if in the same red field the current is closer to 0 then prev- > not interested 
			if self.data_pd['Macd'].iloc[iterations_v2] < lowest_macd:
				return False
			iterations_v2 -= 1
			
		#keeping the same counter to start iterating through the green field
		#going through green, previous to the red field
		while self.data_pd['Macd'].iloc[iterations_v2] >= 0.000:
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
		self.cold_entry_risk_reward(a_iteration)
			
		return True

	# in case of using macd as the entry signal, the stop loss will be the lowest low in the last 15 minutes
	# same case in this function, passing the starting point, same as in the cold entry function
	# a_iteration = -1 in real time trading
	def cold_entry_risk_reward(self, a_iteration):

		iterations = a_iteration - 10
		lowest_low = self.data_pd['High'].iloc[a_iteration]

		for candle in self.data_pd['Low'][iterations:]:
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

		print("R/R based on entry: ", self.risk_reward_setup, self.data_pd['Timestamp'].iloc[a_iteration] )

		return True


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
		
		self.data_pd = self.FH_connect.one_min_data_simulation(self.open_order_info)
		
		#adding the four hour difference cause UNIX in GMT and + 9:30 hours to the open
		nine_30 = self.open_order_info['time']  #+ 3600 for day light savings time ALSO changein finn hubb
		#starting from the index of 9:30 am
		index_time = self.data_pd.index[self.data_pd['Timestamp'] == nine_30]
		start_time = index_time[0]
		
		
		one_00 = nine_30 + 12600 # adding to 1pm 
		#finding the index of 1 PM
		index_finish_time = self.data_pd.index[self.data_pd['Timestamp'] == one_00]
		#taking the int element
		finish_time = index_finish_time[0]

		
		while start_time != finish_time: 
			self.hot_exit(1, start_time)
			self.cold_entry(self.open_order_info['ticker'], 1, start_time)
			start_time +=1

		return 0
			


	## concern -> include saved AND opened orders and be able to delete EITHER one of them as well
	## make it possible to look at two stocks at the same time (more than one) threading?
	## build a simulation class in which you can see your entries and exits on a graph and a print out results
	## store cold entry + hot exit results on a minute bases and record in a separate dataframe, save it as a file with a name 

	## multithreading -> build a GUI with two terminal windows which allow to have to processes at the same time
	## easy level would be to allow two threads to work on two different files (sentiment screener and cold entry)
	## medium level would be allowing two cold entries (I would need to create two object of the same file, obv)
