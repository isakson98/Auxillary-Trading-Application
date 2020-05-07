import asyncio
import pprint
from W_sockets_stream import WebSocket_TD
import datetime

# Data Pipeline function
async def data_pipeline(ticker):
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
    # streamer count
    data_response_count = 0
    heartbeat_response_count = 0

    #data parsing
    new_minute = True
    new_time = None
    old_time = None
    new_volume = None
    minute_volume = None

    WB_TD_client = WebSocket_TD(ticker)

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
                print(data)
                #getting the current minute
                trans_timestamp = data['data'][0]['content'][0]['1'] 
                
                #converting to datetime object
                transaction_time = datetime.datetime.fromtimestamp(trans_timestamp // 1000.0) # // -> int div

                new_time = transaction_time.minute 

                new_volume = data['data'][0]['content'][0]['3']

                # if times are equal, we are in the same minute
                if new_time == old_time:
                    minute_volume = minute_volume + new_volume

                # renew the volume + update new time
                else:
                    #prev minute results
                    print('='*80)
                    print(minute_volume)
                    minute_volume = new_volume
                    old_time = new_time


                # Here I can grab data as it comes in and do something with it.
                if 'key' in data['data'][0]['content'][0]:
                    print('Here is my key: {}'.format(data['data'][0]['content'][0]['key']))

                print('-'*80)
                data_response_count += 1
            

            # If we get a heartbeat notice, let's increment our counter.
            elif 'notify' in data:
                print(data['notify'][0])
                heartbeat_response_count += 1


        except Exception as e:
            print("Breaking while loop")
            print(e)
            await WB_TD_client.close_stream()
            break
            

async def close():
    await asyncio.sleep(1)


print("Enter stock ticker to stream: ")
# ticker = input()

# Run the pipeline.
try:
    asyncio.run(data_pipeline("TSLA"))
except:
    print("Exited pipeline")