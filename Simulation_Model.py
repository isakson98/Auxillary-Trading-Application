from Finn_Hub_API_Calls import Finn_Hub_API_Calls
from Risk_Reward import Risk_Reward
from datetime import datetime
import pandas as pd

## could not figure out how to efficiently deal with data retrieval if using two files.
## so far it seems more efficient to run the simulation in the file where all the calculations are made
## however, I would like to track and plot the results 

class Simulation_Model:

    def __init__(self):
        self.open_order_info = {'time': 0, 'ticker' : 0, 'shares' : 0, 'price' : 0}
        self.risk_reward_setup ={'risk': 0, 'reward' : 0, 'shares' : 0, 'ticker' : 0}
        self.five_min_data = None
        self.one_min_data = None
        self.data_pd = None
        self.FH_connect = Finn_Hub_API_Calls()
        self.TA_object = Risk_Reward()


    #not safe against DAY TIME SAVINGS and HALTS
    #this function iterates through every minute of a specified stock between 9:30 (+some pre market) and 13:00
    #and records cold_entry, stop loss, target and first overbought indicator in a dataframe, which is then graphed out
    #this is a powerful function because it should accomodate every strategy I map out for any stock
    #this would allow me to see results of my strategy in the past (past 30 day limit which TradingView imposes)
    def run_through_model(self):
        #specifying the start time (seconds, which backtracks a hundred candles and a whole day) 
        # beware of the GMT TIME DIFFERENCE SAVINGS LIGHT
        dates = pd.to_datetime(['2020-03-31'])
        second = (dates - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s') 
        
        self.open_order_info['time'] = second[0] + 48600
        self.open_order_info['ticker'] = "NCLH"
        
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
            self.TA_object.cold_entry(self.open_order_info['ticker'], 1, start_time)
            start_time +=1
            
                    
        iterations = 0
        for yes in self.data_pd['Cold Entry']:
            #print(yes)
            if yes == 1:
                print(self.data_pd['Timestamp'].iloc[iterations])
            iterations+=1




#plotting
# fig = go.Figure(data=[go.Candlestick(x= self.data_pd['Timestamp'][Pd:],
#         open= self.data_pd['Open'][Pd:],
#         high= self.data_pd['High'][Pd:],
#         low= self.data_pd['Low'][Pd:],
#         close= self.data_pd['Close'][Pd:]),
# go.Scatter(x=self.data_pd['Timestamp'][Pd:], y=self.data_pd['Up'][Pd:], line=dict(color='orange', width=1))])
#fig.show()