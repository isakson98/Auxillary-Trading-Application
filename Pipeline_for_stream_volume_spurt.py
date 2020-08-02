import asyncio
import pprint
from W_sockets_stream import WebSocket_TD
import datetime

SHARES_TO_FILTER = 500 

# Data Pipeline function
async def Data_pipeline_SPURT(a_ticker, a_cred):
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

    spurt_up_count = 0
    spurt_down_count = 0

    new_tick = 0
    old_tick = 0 # for comparing whether it's uptick or down tick

    # to dispute times when transactions are of the same price
    # in Ameritrade, current same price is green 
    # if the last transaction != to the current price is green and vice versa (red) 
    up_flag = None
    down_flag = None

    WB_TD_client = WebSocket_TD(a_ticker, a_cred)

    # Build the Pipeline.
    await WB_TD_client.build_pipeline()

    # Keep going as long as we can recieve data.
    while True:
        try:
            # Start the Pipeline.
            data = await WB_TD_client.start_pipeline()

            # i can have functions to show what exactly i want to do with streaming data
        
            # Grab the Data, if there was any. Remember not every message will have `data.`
            if 'data' in data:
                #sometimes data comes in a batch, have to do calculations for each transaction
                for tick in data['data'][0]['content']:

                    # parsing the variables out
                    trans_timestamp = tick['1'] 
                    new_tick = tick['2']
                    new_volume = tick['3']

                    # converting to datetime object
                    transaction_time = datetime.datetime.fromtimestamp(trans_timestamp // 1000.0) # // -> int div
                    new_time = transaction_time.minute 

                    # if times are equal, we are in the same minute
                    if new_tick < old_tick :
                        up_flag = False


                    # if new price is higher, its an uptick
                    if (new_tick > old_tick or up_flag) : 
                        #restarting count for spurt down if the tick is green
                        if spurt_down_count >= 10:
                            print("Red spurt {}".format(spurt_down_count))
                            print("Time {}".format(new_time))
                            print("=" * 60)
                        spurt_down_count = 0
                        #if volume is great then what we are filtering, include it 
                        if new_volume >= SHARES_TO_FILTER:
                            spurt_up_count += 1
                        up_flag = True
                        down_flag = False


                    # if new price is lower, it's a downtick 
                    elif (new_tick < old_tick or down_flag) :
                        #restarting count for spurt up if the tick is red
                        if spurt_up_count >= 10:
                            print("Green spurt {}".format(spurt_up_count))
                            print("Time {}".format(new_time))
                            print("=" * 60)
                        spurt_up_count = 0
                        #if volume is great then what we are filtering, include it 
                        if new_volume >= SHARES_TO_FILTER:
                            spurt_down_count += 1
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
            await WB_TD_client.close_stream()
            break
