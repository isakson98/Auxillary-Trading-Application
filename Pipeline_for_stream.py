import asyncio
import pprint
from W_sockets_stream import WebSocket_TD

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

    data_response_count = 0
    heartbeat_response_count = 0

    WB_TD_client = WebSocket_TD(ticker)

    # Build the Pipeline.
    await WB_TD_client.build_pipeline()

    # Keep going as long as we can recieve data.
    while True:
        try:
            # Start the Pipeline.
            data = await WB_TD_client.start_pipeline()
        
            # Grab the Data, if there was any. Remember not every message will have `data.`
            if 'data' in data:

                print('='*80)
                # format -> {'seq': 310, 'key': 'AAPL', '1': 1587759182311, '2': 282.96, '3': 76.0, '4': 124604}
                data_content = data['data'][0]['content']
                pprint.pprint(data_content, indent=4)

                # Here I can grab data as it comes in and do something with it.
                if 'key' in data_content[0]:
                    print('Here is my key: {}'.format(data_content[0]['key']))

                print('-'*80)
                data_response_count += 1
            
            # If we get a heartbeat notice, let's increment our counter.
            elif 'notify' in data:
                print(data['notify'][0])
                heartbeat_response_count += 1

            # # Once we have 1 data responses, we can unsubscribe from a service.
            # if data_response_count == 1:
            #     unsub = await WB_TD_client.(service='LEVELONE_FUTURES')
            #     data_response_count += 1
            #     print('='*80)
            #     print(unsub)
            #     print('-'*80)

            # Once we have 5 heartbeats, let's close the stream. Make sure to break the while loop.
            # or else you will encounter an exception.
            if heartbeat_response_count == 3:
                await WB_TD_client.close_stream()
                break
        except:
            print("Breaking while loop")
            await WB_TD_client.close_stream()
            break
            

async def close():
    await asyncio.sleep(1)


print("Enter stock ticker to stream: ")
ticker = input()

# Run the pipeline.
try:
    asyncio.run(data_pipeline(ticker))
except:
    print("Exited pipeline")