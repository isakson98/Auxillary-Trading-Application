from Config import client_id, account_number
from datetime import datetime
import pandas as pd
import requests
import json
import urllib
import dateutil

# Import the client -> new library to use instead of the old one
from td.client import TDClient
from td.orders import Order, OrderLeg

#THIS class requests unfiltered TD API calls 

class TD_API_Calls:

    def __init__(self):
        # Create a new session, credentials path is optional.
        self.TDSession = TDClient(
            client_id=client_id,
            redirect_uri='https://localhost'
        )
        # Login to the session
        self.TDSession.login()
        

    ### get data for a stock, for a simulation
    ### the delay in this case becomes irrelevant because i'm talking about the past
    # formatting below to fit the current code and structure for the TA library in Risk_Reward.py
    def TD_price_history(self, a_symbol, date, a_frequency):
        # date is supposed to be 9:30 am of that day
        
        date = date * 1000
        ##query all orders
        
        data_pd = self.TDSession.get_price_history(symbol= a_symbol, period_type= 'day', 
                                                   start_date=str(date + 10), end_date=str(date),
                                                   frequency_type= 'minute', frequency=a_frequency)
        if a_symbol != "SPY":
            ## td's data comes a candle as one row, where I need one column for all closes, opens, etc
            open_list = []
            close_list = []
            high_list = []
            low_list = []
            volume_list = []
            timestamp_list = []

            #adding miliseconds to 1pm
            one_oclock = date + 12600000

            for candle in data_pd['candles']:
                open_list.append(candle['open'])
                close_list.append(candle['close'])
                high_list.append(candle['high'])
                low_list.append(candle['low'])
                volume_list.append(candle['volume'])
                timestamp_list.append(candle['datetime'] / 1000)
                
                #if the time is one_oclock i'm done
                if candle['datetime'] == one_oclock:
                    #print("broke at ", timestamp_list[-1])
                    break

            columnZ = ['Close','High', 'Low', 'Open', 'Timestamp']
            data_pd = pd.DataFrame(columns = columnZ)
            
            data_pd['Close'] = close_list
            data_pd['High'] = high_list
            data_pd['Open'] = open_list
            data_pd['Low'] = low_list
            data_pd['Timestamp'] = timestamp_list
            data_pd['Volume'] = volume_list
            data_pd['Cold Entry'] = data_pd.apply(lambda row: 0, axis=1)
            data_pd['Hot Exit'] = data_pd.apply(lambda row: 0, axis=1)
        
        # for spy i only need close and timestamps
        else:
            ## td's data comes a candle as one row, where I need one column for all closes, opens, etc
            close_list = []
            timestamp_list = []

            #adding miliseconds to 1pm
            one_oclock = date + 12600000

            for candle in data_pd['candles']:
                close_list.append(candle['close'])
                timestamp_list.append(candle['datetime'] / 1000)
                
                #if the time is one_oclock i'm done
                if candle['datetime'] == one_oclock:
                    break

            columnZ = ['Close', 'Timestamp']
            data_pd = pd.DataFrame(columns = columnZ)
            
            data_pd['Close'] = close_list
            data_pd['Timestamp'] = timestamp_list

        return data_pd

    ##getting the info to access the websocket for data
    def get_cred(self, a_ticker):

        TDStreamingClient = self.TDSession.create_streaming_session()
        TDStreamingClient.timesale('TIMESALE_EQUITY', [a_ticker], [0,1,2,3])

        return TDStreamingClient


#####################################################################################################################3
#sending orders

    def sending_RISK_exit_order(self, risk_reward_dict):
        new_order = Order()

        new_order.order_type(order_type='STOP')
        new_order.order_session(session='NORMAL')
        new_order.stop_price(stop_price=risk_reward_dict['risk'])
        new_order.order_duration(duration='DAY') 
        
        new_order_leg = OrderLeg()
        new_order_leg.order_leg_instruction(instruction='SELL')
        new_order_leg.order_leg_quantity(quantity=risk_reward_dict['shares'])
        new_order_leg.order_leg_asset(asset_type='EQUITY', symbol=risk_reward_dict['ticker'])

        new_order.add_order_leg(order_leg=new_order_leg)

        self.TDSession.place_order(str(account_number), new_order)


    #using this for cold entry strategy
    #need to enter immididately as I get the signal that the previos one is overextended
    def sending_cold_ENTRY_order(self, risk_reward_dict):
        new_order = Order()

        new_order.order_type(order_type='MARKET')
        new_order.order_session(session='NORMAL')
        new_order.order_duration(duration='DAY') 
        
        new_order_leg = OrderLeg()
        new_order_leg.order_leg_instruction(instruction='BUY')
        new_order_leg.order_leg_quantity(quantity=risk_reward_dict['shares'])
        new_order_leg.order_leg_asset(asset_type='EQUITY', symbol=risk_reward_dict['ticker'])

        new_order.add_order_leg(order_leg=new_order_leg)

        self.TDSession.place_order(str(account_number), new_order)

        

    # using this hot exit strategy
    def sending_REWARD_exit_order(self, risk_reward_dict):
        new_order = Order()

        new_order.order_type(order_type='MARKET')
        new_order.order_session(session='NORMAL')
        new_order.order_duration(duration='DAY') 
        
        new_order_leg = OrderLeg()
        new_order_leg.order_leg_instruction(instruction='SELL')
        new_order_leg.order_leg_quantity(quantity=risk_reward_dict['shares'])
        new_order_leg.order_leg_asset(asset_type='EQUITY', symbol=risk_reward_dict['ticker'])

        new_order.add_order_leg(order_leg=new_order_leg)

        self.TDSession.place_order(str(account_number), new_order)


    # exiting an existing position in one stock either in red or in green
    def sending_oco(self, risk_reward_dict):   

        new_order = Order()
        new_order.order_strategy_type(order_strategy_type='OCO')

        # defining reward order
        reward_child = new_order.create_child_order_strategy()
        reward_child.order_type(order_type='LIMIT')
        reward_child.order_session(session='NORMAL')
        reward_child.order_price(price=risk_reward_dict['reward'])
        reward_child.order_duration(duration='DAY')

        # defining risk order
        risk_child= new_order.create_child_order_strategy()
        risk_child.order_type(order_type='STOP')
        risk_child.order_session(session='NORMAL')
        risk_child.order_price(price=risk_reward_dict['risk'])
        risk_child.order_duration(duration='DAY')   

        # same leg compnonets for both child orders
        child_order_leg = OrderLeg()
        child_order_leg.order_leg_instruction(instruction = 'SELL')
        child_order_leg.order_leg_quantity(quantity=risk_reward_dict['shares'])
        child_order_leg.order_leg_asset(asset_type='EQUITY', symbol=risk_reward_dict['ticker'])

        reward_child.add_order_leg(order_leg=child_order_leg)
        risk_child.add_order_leg(order_leg=child_order_leg)

        # adding rewards order to the parent order
        new_order.add_child_order_strategy(child_order_strategy=reward_child)
        # adding risk order to the parent order
        new_order.add_child_order_strategy(child_order_strategy=risk_child)

        self.TDSession.place_order(str(account_number), new_order)


#####################################################################################################################3
# viewing / deleting orders

    def account_info(self):
        #define an endpoint with a stock of yout choice
        accounts_data_single = self.TDSession.get_accounts(
            account=str(account_number),
            fields=['orders']
        )
        return accounts_data_single


    def query_real_orders(self):
        #getting the orders from today's date
        today_date = datetime.date(datetime.now())
        content = self.TDSession.get_orders_query(from_entered_time=today_date)
        return content


    def query_saved_orders(self):
        ##query all saved orders
        today_date = datetime.date(datetime.now())
        content = self.TDSession.get_orders_query(from_entered_time=today_date)
        return content


    def deleting_one_real_order(self, order_id):

        return self.TDSession.cancel_order(str(account_number), str(order_id))


    def deleting_one_saved_order(self, order_id):

        return self.TDSession.cancel_saved_order(str(account_number), str(order_id))

