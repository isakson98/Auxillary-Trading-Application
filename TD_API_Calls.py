from Config import client_id, password, username, secret_city, secret_mascot, secret_restaurant, secret_mother, account_number 
from TdAmeritradeAuth import TDAuthentication 
from datetime import datetime
import requests

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

        # endpoint = r"https://api.tdameritrade.com/v1/orders" #temp
        # payload = { 'toEnteredTime' : '2020-03-20', #temp
        #             'fromEnteredTime' : '2020-03-01',#temp
        #             'maxResults' : '100',#temp
        # }

        #checking if the token is still valid
        try:
            content = requests.get(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint,  headers = header) 
            #content = requests.get(url = endpoint, params = payload, headers = header) # temp
            

        data = content.json()
        #returns a dictionary
        return data

    
    def sending_oco(self, risk_reward_dict):   ##temp saved
        ##creating a double order

        #creating a saved order
        header = {'Authorization' : "Bearer {}".format(self.access_token),
                "Content-Type" : "application/json"}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)   ##temp saved


        payload = {
        #reward
        "orderStrategyType": "OCO",
        "childOrderStrategies": [
            {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": risk_reward_dict['reward'], 
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
            },
        #risk
            {
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
        ]
        }

        #checking if the token is still valid
        try:
            content = requests.post(url = endpoint, params = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, params = payload,  headers = header)
            print(content.raise_for_status())

        if (content.status_code == 200):
            print("The exit orders have been sent")
        else :
            print("Sending the exit orders failed")
        return



    def sending_RISK_exit_order(self, risk_reward_dict):


        header = {'Authorization' : "Bearer {}".format(self.access_token),
                "Content-Type" : "application/json"}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)  ##temp saved

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
            content = requests.post(url = endpoint, params = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, params = payload,  headers = header)
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

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)  ##temp saved

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
            content = requests.post(url = endpoint, params = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, params = payload,  headers = header)
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

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/savedorders".format(account_number)  ##temp saved

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
            content = requests.post(url = endpoint, params = payload, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.post(url = endpoint, params = payload,  headers = header)
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
        except requests.HTTPError as e:
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
        ##query all saved orders
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(account_number)

        try:
            content = requests.get(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
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
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.get(url = endpoint, headers = header)
            print(content.raise_for_status())
            

        data = content.json()

        return data



    def deleting_one_real_order(self, order_id):
        ## deleting the saved order
        header = {'Authorization' : "Bearer {}".format(self.access_token)}

        #adding an order id 
        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders/{}".format(account_number, order_id)

        try:
            content = requests.delete(url = endpoint, headers = header)
            content.raise_for_status()
        except requests.HTTPError as e:
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
        except requests.HTTPError as e:
            print("Token timed out -> obtaining a new one")
            self.TDClient.authenticate()
            self.access_token = self.TDClient.access_token
            header = {'Authorization' : "Bearer {}".format(self.access_token)}
            content = requests.delete(url = endpoint, headers = header)
            print(content.raise_for_status())

        #dispalying data
        print(content.status_code)
        return