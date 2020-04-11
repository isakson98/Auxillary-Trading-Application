from Risk_Reward import Risk_Reward 
from TD_API_Calls import TD_API_Calls #solved = TD_API only called from this file to reduce the need for selenium to run twice
from Sentiment_Screener import Sentiment_Screener
from datetime import datetime
from dateutil import parser
import time

#This file controls the user interface and makes necessary calls to Risk_Reward and TD_API_Calls

fox = Risk_Reward()
TD = TD_API_Calls()
sent = Sentiment_Screener()


#placing orders after manual entry
#continuously checking with TD_ameritrade whether an order has been placed
#propmpts the user for the type of strategy used,
#makes a call to risk_reward to calculatte
def one_r_two_r_exit_placement():
	##continue requesting the data for an opening trade until there is one
	try:
		while True:
		    history_orders = TD.retrieve_orders()
		    if fox.checking_opening_positions(history_orders) == True:
		        break
		    time.sleep(2)

		#asking which r/r to employ, depending on the strategy
		print("Choose the exit strategy [5] for 5 min R/R, [1] for 1 min R/R")
		resp = 0
		while True:
		    resp = input() 
		    if (resp == '5') or (resp == '1') or (resp == '0'):
		        break

		#getting price data, parsing/calculating the R/R, placing the trade
		if (resp == '5'):
		    final_r_r = fox.five_min_calc_r_r() #retriving data from the r/r class
		elif (resp == '1'):
		    final_r_r = fox.one_min_calc_r_r() #same deal here
		elif (resp == '0'):
		    print("No action")

		TD.sending_oco(final_r_r)


	except KeyboardInterrupt:
		print("Stop checking for opening positions")
		print()


#FOR VISIBILITY (not automation)
#concern -> include saved AND opened orders 
def check_opened_orders():
	##retrieve in a way that the order id can be read (maybe multiple orders deleted at once)
	##so the can be deleted ( call check_opened_orders in the delete function)
	##query all saved orders and then delete one of them
	data = TD.query_saved_orders()

	#order_id = data[0]['savedOrderId']
	collection_of_orders = []
	for order in data:
	    order_data = { 'OrderId' : order['savedOrderId'], #change this temp 
	                  'symbol' : order['orderLegCollection'][0]['instrument']['symbol'],
	                  'instruction': order['orderLegCollection'][0]['instruction'],
	                  'quantity' : order['orderLegCollection'][0]['quantity'],
	                  'time' : order['savedTime']} #time
	        
	    collection_of_orders.append(order_data)
	    
	## list the orders in a eye-friendly manner
	
	date = parser.parse(order_data['time'], ignoretz = True)
	est_hour = date.hour - 4
	if est_hour < 0:
		est_hour += 24
	print(est_hour)
	date= date.replace(hour = est_hour)

	iteration = 1
	print("Opened Orders: ")
	for order in collection_of_orders:
	    print(iteration,"->", order['symbol'], order['quantity'], order['instruction'], date)
	    iteration +=1

	collection_of_orders.append(iteration)
#creating an extra element, which can create a crash if I choose the last element to delete cause it will be an iteration number     	
	return collection_of_orders


#FOR VISIBILITY (not automation)
#deleting orders manually
def delete_opened_orders():
	formated_orders = check_opened_orders() ##calling function in this file
	iteration = formated_orders[-1]

	while True:
		print("Select an order to delete: ")
		resp = input()
		if int(resp) <= (iteration-1): #-1 adrresse the problem described above
			break

	order_id = formated_orders[int(resp) - 1]['OrderId']
	TD.deleting_one_saved_order(order_id) ## td call
	return


#  because i am using this function also for exiting trades out of the cold entry
#so far it only works from the start 
# process::
# 1. check opened orders
# 2. find out which orders are opened 
# 3. find out what their 2r is to start hot exit only after that price 
# 4. initiate the function in risk reward two seconds before the current candle expires
##continue requesting the data for an opening trade until there is one
def start_hot_exit(token):

	try:
		#if token is zero, I entered the trade manually and need specify what strategy I am using 
		resp = 0
		if token == 0:
			##find a placed order first 
			while True:
			    history_orders = TD.retrieve_orders()
			    if fox.checking_opening_positions(history_orders) == True:
			        break
			    time.sleep(2)

			#asking which r/r to employ, depending on the strategy
			print("Choose the exit strategy [5] for 5 min R/R, [1] for 1 min R/R, or [0] for no action")
			while True:
			    resp = input() 
			    if (resp == '5') or (resp == '1') or (resp == '0'):
			        break

			final_r_r = None
			#getting price data, parsing/calculating the R/R, placing the 4trade
			if (resp == '5'):
			    final_r_r = fox.five_min_calc_r_r() #retriving data from the r/r class
			elif (resp == '1'):
			    final_r_r = fox.one_min_calc_r_r() #same deal here
			elif (resp == '0'):
			    print("No action")

			TD.sending_RISK_exit_order(final_r_r) 


		# need an order id for the risk order so I can first delete it and then inititate the reward order
		# ^ find if there is something in json that you can do 
		order_info = find_risk_exit_order_id()


		#keep going through the loop until there is an exit indicator
		# I will enter a loop only if I specify the manual strategy (1 or 5) or if it is automated (token ==1)
		# That way, I am creating a safety net in case I manually enter and get switched to here
		# and decide not to exit using hot exit strategy
		while True and (resp == '1' or resp == '5' or token == 1) :
			time.sleep(1)
			# start indicator 3 seconds before current minute ends
			result = False
			if round(time.time()) % 60 ==56:
				result = fox.hot_exit(0, -1)
			if result == True:
				TD.deleting_one_saved_order(order_info['Order_Id']) #temp
				TD.sending_REWARD_exit_order(final_r_r) #temp
				break


	except KeyboardInterrupt:
		print("Stop checking for opening positions")
		print()



#AUTOMATED finder of order id
# i need to find the order id to delete the stop loss order in case I need to initiate a hot exit order
def find_risk_exit_order_id():
	data = TD.query_real_orders()
	#locating opening position and grabbing the time stamp, the name, # of share
	received_order_info = {}
	for opening in data:
		#print(opening)
		if opening['orderLegCollection'][0]['positionEffect'] == 'CLOSING':
			received_order_info['ticker'] = opening['orderLegCollection'][0]['instrument']['symbol']
			received_order_info['shares'] = opening['quantity']
			received_order_info['price'] = opening['orderActivityCollection'][0]['executionLegs'][0]['price']
			received_order_info['Order_Id'] = opening['orderId']
			received_order_info['time'] = opening['orderActivityCollection'][0]['executionLegs'][0]['time']

			print("Deleting stop loss order: {}".format(received_order_info))
			return received_order_info

	print("No active stop loss orders found")
	return 



## this function prompts the user to name a ticker to trade
def start_cold_entry():

	print("Write a stock to trade in UPPER case: ")
	name_of_stock = input()
	# ^ have a function that will upper case the value
	#name_of_stock = name_of_stock.isupper()
	
	starttime=round(time.time())
	# basically, from the amount of time you want you it to sleep
	# you subtract how much is left before the next time it should ran in that sequence
	# start the loop only when the current seconds 

	while True:
		# simulation == 0 (not simulation), and -1 = index of current candle (last one in the df)
		entry_complete = fox.cold_entry(name_of_stock, 0, -1)
		if entry_complete == True:
			break
		time.sleep(60.0 - ((time.time() - starttime) % 60.0))


	#part of sending the order
	final_r_r = fox.risk_reward_setup

	#sending a 1:2 R/R
	#TD.sending_oco(final_r_r) temp

	return 0

#
def repeat_trending_stocks():

	print("Review current trending [1] or recent trending [2]")
	options = input()

	#if option is one, use StockTwit api to get currently trading
	if options == '1':
		try:
			starttime=round(time.time())
			sent.all_in_one()
			while True:
				time.sleep(300.0 - ((time.time() - starttime) % 300.0))
				sent.all_in_one()
		except:
			print("Exiting viewing trending stocks")
	
	#if 2, open csv with previously trading stocks, check for today's news
	elif options == '2':
		sent.read_filtered_and_news()


def model_init():

	print("Enter ticker symbol: ")
	name = input()

	print("Enter date (yyyy-mm-dd') or [now] for today to analyze: ")
	date = input()

	#now means i need to get todays date and format it 
	if date == "now":
		today_date = datetime.date(datetime.now())
		date = today_date.isoformat()

	fox.run_through_model(name, date)



while True:
	print('--------------------------------------')
	print("Select from the options below: ")
	print("[0] - Place 1R / 2R exit trades")  
	print("[1] - Check opened / saved orders") 
	print("[2] - Delete opened / saved orders") 
	print("[3] - Start hot exit")
	print("[4] - Start cold entry")
	print("[5] - See trending stocks") 
	print("[6] - Run simulation model")
	print("[10] - Find risk order ID")
	print("[q] - Quit the program")
	print('--------------------------------------')

	decision = input() 
	if decision == '0':
		one_r_two_r_exit_placement()
	elif decision == '1':
		check_opened_orders()
	elif decision == '2':
		delete_opened_orders()
	elif decision == '3':
		start_hot_exit(0)
	elif decision == '4':
		start_cold_entry()
	elif decision == '5':
		repeat_trending_stocks()
	elif decision == '6':
		model_init()
	elif decision == '10':
		find_risk_exit_order_id()
	elif decision == 'q':
		quit(0)



