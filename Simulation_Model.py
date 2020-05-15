from Risk_Reward import Risk_Reward
from Sentiment_Screener import Sentiment_Screener
import pandas as pd
import numpy as np

#this file taekes all the stocks in recent_runners, runs them throught the run_model function
#and 
#preinitiliaze num_days to default which will iterate through entire file
#otherwise
# if -1 goes through entire file
# otherwise goes through specified number of rows
def simulation_model(num_days):

    fox = Risk_Reward()

    df_list_stocks = pd.read_csv("recent_runners.csv")

    if num_days == -1:
        num_days = len(df_list_stocks.index)

    if num_days > len(df_list_stocks.index):
        print("Number of days specified is too big : ", len(df_list_stocks.index), " is maximum possible")

    #checking a row of them
    for index, row in df_list_stocks.iterrows():

        ticker = 0

        for name in row:
            
            if name != row[0] and (name != 'None'or name != 'NONE'):
                name_of_row = 'ticker_' + str(ticker)
                print(row['date'], row[name_of_row])
                fox.run_through_model(row[name_of_row], row['date'])

            ticker+=1

        #decrement until 0
        if index == num_days - 1:
            break
