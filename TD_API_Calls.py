from Config import client_id, password, username, secret_city, secret_mascot, secret_restaurant, secret_mother, account_number 
from TdAmeritradeAuth import TDAuthentication 
from datetime import datetime
import pandas as pd
import requests
import json
import urllib
import dateutil

#THIS class requests unfiltered TD API calls 

class TD_API_Calls:

    def __init__(self):
        self.TDClient  = TDAuthentication(client_id, password, username, secret_city, secret_mascot, secret_restaurant, secret_mother)
        self.access_token = None

    def retrieve_orders(self):

        #getting the orders from today's date
        header = {'Authorization' : "Bearer {}".format(self.access_token)} #uncomment
        today_date = datetime.date(datetime.now())
        endpoint = r"https://api.tdameritrade.com/v1/orders?fromEnteredTime={}".format(today_date) #uncomment

        #checking if the token is still valid
        try:
            content = requests.get(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError : #as e before this
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint,  headers = header) 
            #content = requests.get(url = endpoint, params = payload, headers = header) # temp
            

        data = content.json()
        #returns a dictionary
        return data

    
    def sending_oco(self, risk_reward_dict):   
        ##creating a double order

        #creating an order
        header = {'Authorization' : "Bearer {}".format(self.access_token),
                "Content-Type" : "application/json"}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)   

        payload = {
    
            "orderStrategyType": "OCO",
            "childOrderStrategies": [
                {
                    "orderType": "LIMIT",
                    "session": "NORMAL",
                    "price": 45.97,
                    "duration": "DAY",
                    "orderStrategyType": "SINGLE",
                    "orderLegCollection": [
                        {
                            "instruction": "SELL",
                            "quantity": 2,
                            "instrument": {
                                "symbol": "MSFT",
                                "assetType": "EQUITY"
                            }
                        }
                    ]
                },
                {
                    
                    "orderType": "STOP_LIMIT",
                    "session": "NORMAL",
                    "price": 37.00,
                    "stopPrice": 35.00,
                    "duration": "DAY",
                    "orderStrategyType": "SINGLE",
                    "orderLegCollection": [
                        {
                            "instruction": "SELL",
                            "quantity": 2,
                            "instrument": {
                                "symbol": "MSFT",
                                "assetType": "EQUITY"
                            }
                        }
                    ]
                }
            ]
        }

        # #reward
        # "orderStrategyType": "OCO",
        # "childOrderStrategies": [
        #     {
        #     "orderType": "LIMIT",
        #     "session": "NORMAL",
        #     "price": risk_reward_dict['reward'], 
        #     "duration": "DAY",
        #     "orderStrategyType": "SINGLE",
        #     "orderLegCollection": [
        #         {
        #         "instruction": "SELL",
        #         "quantity": risk_reward_dict['shares'] ,
        #         "instrument": {
        #             "symbol": risk_reward_dict['ticker'],
        #             "assetType": "EQUITY"
        #         }
        #         }
        #     ]
        #     },
        # #risk
        #     {
        #     "orderType": "STOP",
        #     "session": "NORMAL",
        #     "stopPrice": risk_reward_dict['risk'],
        #     "duration": "DAY",
        #     "orderStrategyType": "SINGLE",
        #     "orderLegCollection": [
        #         {
        #         "instruction": "SELL",
        #         "quantity": risk_reward_dict['shares'] ,
        #         "instrument": {
        #             "symbol": risk_reward_dict['ticker'],
        #             "assetType": "EQUITY"
        #         }
        #         }
        #     ]
        #     }
        # ]
        # }

        #checking if the token is still valid
        try:
            content = requests.post(url = endpoint, json = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, json = payload,  headers = header)
            print(content.raise_for_status())

        if (content.status_code == 200):
            print("The exit orders have been sent")
        else :
            print("Sending the exit orders failed")
        return



    def sending_RISK_exit_order(self, risk_reward_dict):


        header = {'Authorization' : "Bearer {}".format(self.access_token),
                "Content-Type" : "application/json"}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)  

        payload = {
            "orderType": "STOP",
            "session": "NORMAL",
            "stopPrice": risk_reward_dict['risk'],
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                "instruction": "SELL",
                "quantity": risk_reward_dict['shares'] ,
                "instrument": {
                    "symbol": risk_reward_dict['ticker'],
                    "assetType": "EQUITY"
                }
                }
            ]
        }


        #checking if the token is still valid
        try:
            content = requests.post(url = endpoint, json = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, json = payload,  headers = header)
            print(content.raise_for_status())

        if (content.status_code == 200):
            print("The exit orders have been sent")
            self.query_saved_orders()
        else :
            print("Sending the exit orders failed")
        return

    #using this for cold entry strategy
    #need to enter immididately as I get the signal that the previos one is overextended
    def sending_cold_ENTRY_order(self, risk_reward_dict):


        header = {'Authorization' : "Bearer {}".format(self.access_token),
                "Content-Type" : "application/json"}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(account_number) 

        payload = {
            "orderType": "MARKET",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                "instruction": "BUY",
                "quantity": risk_reward_dict['shares'] ,
                "instrument": {
                    "symbol": risk_reward_dict['ticker'],
                    "assetType": "EQUITY"
                }
                }
            ]
            }


        #checking if the token is still valid
        try:
            content = requests.post(url = endpoint, json = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError :
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, json = payload,  headers = header)
            print(content.raise_for_status())

        if (content.status_code == 200):
            print("The exit orders have been sent")
        else :
            print("Sending the exit orders failed")
        return

    # using this hot exit strategy
    def sending_REWARD_exit_order(self, risk_reward_dict):

        header = {'Authorization' : "Bearer {}".format(self.access_token),
                "Content-Type" : "application/json"}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(account_number)  

        payload = {
            "orderType": "MARKET",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                "instruction": "SELL",
                "quantity": risk_reward_dict['shares'] ,
                "instrument": {
                    "symbol": risk_reward_dict['ticker'],
                    "assetType": "EQUITY"
                }
                }
            ]
            }

        #checking if the token is still valid
        try:
            content = requests.post(url = endpoint, json = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, json = payload,  headers = header)
            print(content.raise_for_status())

        if (content.status_code == 200):
            print("The exit orders have been sent")
        else :
            print("Sending the exit orders failed")
        return



    def account_info(self):
        #define an endpoint with a stock of yout choice
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        endpoint = r"https://api.tdameritrade.com/v1/accounts"

        try:
            content = requests.get(url=endpoint, headers=header)
            content.raise_for_status()
        except requests.HTTPError:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint, headers = header)
            print(content.raise_for_status())


        data = content.json()

        return data


    #looks like this is the same funcion as the first one aka retrieve_orders()
    def query_real_orders(self):
        ##query all orders
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(account_number)

        try:
            content = requests.get(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint, headers = header)
            print(content.raise_for_status())

        data = content.json()

        return data


    def query_saved_orders(self):
        ##query all saved orders
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)

        try:
            content = requests.get(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError :
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint, headers = header)
            print(content.raise_for_status())
            

        data = content.json()

        return data



    def deleting_one_real_order(self, order_id):
        ## deleting the  order
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        #adding an order id 
        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders/{}".format(account_number, order_id)

        try:
            content = requests.delete(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError :
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.delete(url = endpoint, headers = header)
            print(content.raise_for_status())

        #dispalying data
        print(content.status_code)
        return


## ^ consider having one delete function which will have as parameter 'saved' or just 'orderId', and choose endpoint accordingly
    def deleting_one_saved_order(self, order_id):
        ## deleting the saved order
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        #adding an order id 
        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders/{}".format(account_number, order_id)

        try:
            content = requests.delete(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.delete(url = endpoint, headers = header)
            print(content.raise_for_status())

        #dispalying data
        print(content.status_code)
        return


####### FOR DATA STREAMING
    def unix_time_millis(self, dt):
        epoch = datetime.utcfromtimestamp(0)
        return(dt - epoch).total_seconds() * 1000.0

    ##getting the info to access the websocket for data
    def get_cred(self, a_ticker):

        #defining the end point = user principles
        endpoint = 'https://api.tdameritrade.com/v1/userprincipals'

        # get our access token
        header = {'Authorization' : 'Bearer {}'.format(self.access_token)}

        #defining the parameters for the endpoint
        payload = {'fields' : 'streamerSubscriptionKeys,streamerConnectionInfo'}


        try:
            content = requests.get(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError : #as e before this
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint, params = payload, headers = header) # temp

        #we are converting to a dictionary, to it will be easier for us parse the string
        userPrincipalsResponse = content.json()

        #grab the time sstamp and convert to milliseconds
        tokenTimeStamp = userPrincipalsResponse['streamerInfo']['tokenTimestamp']
        #parsing the date ignore the time zone
        date = dateutil.parser.parse(tokenTimeStamp, ignoretz=True)
        #converting into milliseconds
        tokenTimeStampAsMs = self.unix_time_millis(date)

        #define the items to make a request to login
       # we need to define our credentials that we will need to make our stream
        credentials = {"userid": userPrincipalsResponse['accounts'][0]['accountId'],
                    "token": userPrincipalsResponse['streamerInfo']['token'],
                    "company": userPrincipalsResponse['accounts'][0]['company'],
                    "segment": userPrincipalsResponse['accounts'][0]['segment'],
                    "cddomain": userPrincipalsResponse['accounts'][0]['accountCdDomainId'],
                    "usergroup": userPrincipalsResponse['streamerInfo']['userGroup'],
                    "accesslevel":userPrincipalsResponse['streamerInfo']['accessLevel'],
                    "authorized": "Y",
                    "timestamp": int(tokenTimeStampAsMs),
                    "appid": userPrincipalsResponse['streamerInfo']['appId'],
                    "acl": userPrincipalsResponse['streamerInfo']['acl'] }

        #print(credentials)

        #defining a login request
        ##we have to login it first (send the login request), and then define data request

        login_request = {"requests": [{"service": "ADMIN",
                              "requestid": "0",  
                              "command": "LOGIN",
                              "account": userPrincipalsResponse['accounts'][0]['accountId'],
                              "source": userPrincipalsResponse['streamerInfo']['appId'],
                              "parameters": {"credential": urllib.parse.urlencode(credentials),
                                             "token": userPrincipalsResponse['streamerInfo']['token'],
                                             "version": "1.0"}}]}
        #defining a request to stream
        data_request= {"requests":[{"service": "TIMESALE_EQUITY",
                                    "requestid": "2",
                                    "command": "SUBS",
                                    "account": userPrincipalsResponse['accounts'][0]['accountId'],
                                    "source": userPrincipalsResponse['streamerInfo']['appId'],
                                    "parameters": {
                                        "keys": a_ticker,
                                        "fields": "0,1,2,3"
                                    }}]}



        #turn the request into a json string
        login_encoded = json.dumps(login_request)
        data_encoded = json.dumps(data_request)

        socket_url = userPrincipalsResponse['streamerInfo']['streamerSocketUrl']
        socket_uri = "wss://" + socket_url + "/ws"

        login_and_data = {'login' : login_encoded, 'data' : data_encoded, 'uri': socket_uri}

        return login_and_data

#not part of class because i do not need to get authentication
### get data for a stock, for a simulation
### the delay in this case becomes irrelevant because i'm talking about the past
# formatting below to fit the current code and structure for the TA library in Risk_Reward.py
def TD_price_history(symbol, date, frequency):
    # date is supposed to be 9:30 am of that day
    
    date = date * 1000
    ##query all orders

    endpoint = r"https://api.tdameritrade.com/v1/marketdata/{}/pricehistory".format(symbol)

    payload = {'apikey' : client_id,
                'periodType' : 'day',
                'frequency' : frequency,
                'frequencyType' : 'minute',
                'endDate' : date,
                'startDate': date + 10,
                'needExtendedHoursData' : 'true'
    }

    content = requests.get(url = endpoint, params = payload)

    data = content.text

    data_pd = pd.read_json(data)

    if symbol != "SPY":
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

