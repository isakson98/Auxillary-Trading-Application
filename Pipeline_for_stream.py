import asyncio
import datetime
from td.client import TDClient
SHARES_TO_FILTER = 1500 

# Data Pipeline function
async def Data_pipeline(a_ticker, TD_session):
    """
    Generally speaking, you will need to wrap the operations that process
    and handle the data inside an async function. The reason being is so
    that you can await the return of data.

    However, operations like creating the client, and subscribing to services
    can be performed outside the async function. In the example below, we demonstrate
    building the pipline, which is connecting to the websocket and logging in.
    We then start the pipeline, which is where the services are subscribed to and data
    begins streaming. The `start_pipeline()` will return the data as it comes in. From
    there, we process the data however we choose.

    Additionally, we can also see how to unsubscribe from a stream using logic and how
    to close the socket mid-stream.
    """

    #data parsing
    new_time = None
    old_time = None

    new_volume = 0
    up_volume = 1 #to avoid div by zero in the first rotation
    down_volume = 1

    new_tick = 0
    old_tick = 0 # for comparing whether it's uptick or down tick

    # to dispute times when transactions are of the same price
    # in Ameritrade, current same price is green 
    # if the last transaction != to the current price is green and vice versa (red) 
    up_flag = None
    down_flag = None

    TDStreamingClient = TD_session.get_cred(a_ticker)

    # Build the Pipeline.
    await TDStreamingClient.build_pipeline()

    # Keep going as long as we can recieve data.
    while True:
        try:
            # Start the Pipeline.
            data = await TDStreamingClient.start_pipeline()

            # i can have functions to show what exactly i want to do with streaming data
        
            # Grab the Data, if there was any. Remember not every message will have `data.`
            if 'data' in data:
                # print(data['data'][0]['content'])
                #sometimes data comes in a batch, have to do calculations for each transaction
                for tick in data['data'][0]['content']:

                    # parsing the variables out
                    trans_timestamp = tick['1'] 
                    new_tick = tick['2']
                    new_volume = tick['3']

                    # converting to datetime object
                    transaction_time = datetime.datetime.fromtimestamp(trans_timestamp // 1000.0) # // -> int div
                    new_time = transaction_time.minute 

                    # renew the volume + update new time
                    if new_time != old_time :
                        #prev minute results
                        print('='*60)
                        
                        print(old_time)
                        # subtract to see whether more volume down on negative or positive candle
                        difference = up_volume - down_volume
                        print("Difference in volume   :", difference)
                        
                        percentage = round(difference / (up_volume + down_volume) * 100)
                        print("Percentage of strength :",  percentage)

                        # renew stats for a new minute
                        up_volume = 1
                        down_volume = 1
                        old_time = new_time

                    # if times are equal, we are in the same minute
                    if new_tick < old_tick :
                        up_flag = False

                    # if new price is higher, its an uptick
                    if (new_tick > old_tick or up_flag) : 

                        if new_volume >= SHARES_TO_FILTER:
                            up_volume += new_volume
                            # print('='*60)
                            # print(new_tick, " " , new_volume)
                        
                        up_flag = True
                        down_flag = False

                    # if new price is lower, it's a downtick 
                    elif (new_tick < old_tick or down_flag) :

                        if new_volume >= SHARES_TO_FILTER:
                            down_volume += new_volume
                            # print('='*60)
                            # print(new_tick ," ", -new_volume)
                        
                        up_flag = False
                        down_flag = True
                    
                    # assign the price at which a new transaction went through as the old one
                    # only if the two prices are different
                    old_tick = new_tick

            else:
                print(data)


        except Exception as e:
            print("Breaking while loop")
            print(e)
            await TDStreamingClient.close_stream()
            break
