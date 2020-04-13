from Risk_Reward import Risk_Reward
from Sentiment_Screener import Sentiment_Screener
from time import sleep
import pandas as pd

#this file taekes all the stocks in recent_runners, runs them throught the run_model function
#and 
fox = Risk_Reward()

df_list_stocks = pd.read_csv("recent_runners.csv")

same_date = {}

#checking a row of them
for index, row in df_list_stocks.iterrows():
    print(row['date'], row['ticker_1'])
    fox.run_through_model(row['ticker_1'], row['date'])
    print("----------------------------------------------------------------------------------------------------------")

    if row['ticker_2'] != 'None':
        print(row['date'], row['ticker_2'])
        fox.run_through_model(row['ticker_2'], row['date'])
        print("----------------------------------------------------------------------------------------------------------")

        if row['ticker_3'] != 'None':
            print(row['date'], row['ticker_3'])
            fox.run_through_model(row['ticker_3'], row['date'])
            print("----------------------------------------------------------------------------------------------------------")

    