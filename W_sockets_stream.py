from TD_API_Calls import TD_API_Calls
import json
import websockets
import asyncio
import nest_asyncio
import datetime

# figure out how to split into minutes
# how to figure out which tick was last to compare it with current
# how do i want to deal with data and how/where to implement indicators based on incoming data

class WebSocket_TD:

    def __init__(self, a_ticker):
        #getting login, data info, and url from main TD class
        TD_client = TD_API_Calls()
        self.log_data_url = TD_client.get_cred(a_ticker)
        self.connection: websockets.WebSocketClientProtocol = None

        #either get an event loop (which stores coroutines to switch beteween) or create a new one
        try:
            self.loop = asyncio.get_event_loop()
        except websockets.WebSocketException:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)       

    #pipeline functions
    async def start_pipeline(self) -> dict:     
        """Recieves the data as it streams in.
        Returns:
        ----
        dict -- The data coming from the websocket.
        """

        return await self._receive_message(return_value=True)


    #pipeline functions
    async def build_pipeline(self) -> websockets.WebSocketClientProtocol:
        """Builds a data pipeine for processing data.
        Often we want to take the data we are streaming and
        use it in other functions or store it in other platforms.
        This method makes the process of building a pipeline easy
        by handling all the connection setup and request setup.
        Returns:
        ----
        websockets.WebSocketClientProtocol -- The websocket connection.
        """

        # Connect to Websocket.
        await self._connect()

        # Build the Data Request.
        await self._send_message(self.log_data_url['data'])

        return self.connection

    def stream(self):
        """Starts the stream and prints the output to the console.
        Initalizes the stream by building a login request, starting 
        an event loop, creating a connection, passing through the 
        requests, and keeping the loop running."""


        try:
            # Connect to the Websocket.
            self.loop.run_until_complete(self._connect(pipeline_start=False))

            # Send the Request.
            asyncio.ensure_future(self._send_message(self.log_data_url['data']))

            # Start Recieving Messages.
            asyncio.ensure_future(self._receive_message(return_value=False))

            # Keep the Loop going, until an exception is reached.
            self.loop.run_forever()

        # interrupting the stream
        except:
            # adding function in the loop that will close all other tasks
            asyncio.ensure_future(self.close_stream())
            self.loop.run_forever()

            self.loop.close()
            print(self.loop.is_closed())


    async def _connect(self, pipeline_start: bool = True) -> websockets.WebSocketClientProtocol:
        """Connects the Client to the TD Websocket.
        Connecting to webSocket server websockets.client.connect 
        returns a WebSocketClientProtocol, which is used to send 
        and receive messages
        Keyword Arguments:
        ----
        pipeline_start {bool} -- This is also used to start the data
            pipeline so, in that case we can handle more tasks here.
            (default: {True})
        Returns:
        ---
        websockets.WebSocketClientProtocol -- The websocket connection.
        """        

        # Grab the login info.
        login_request = self.log_data_url['login']

        # Create a connection.
        self.connection = await websockets.client.connect(self.log_data_url['uri'])

        # check it before sending it back.
        if await self._check_connection() and pipeline_start == True:

            # Login to the stream.
            await self._send_message(login_request)
            await self._receive_message(return_value=True)
            return self.connection
        
        else:
            # Login to the stream.
            await self._send_message(login_request)
            return self.connection


    async def close_stream(self) -> None:
        """Closes the connection to the streaming service."""        

        # close the connection.
        await self.connection.close()

        # Stop the loop.
        self.loop.call_soon_threadsafe(self.loop.stop())

        # cancel all the task.
        for index, task in enumerate(asyncio.Task.all_tasks()):
            
            # let the user know which task is cancelled.
            print("Cancelling Task: {}".format(index))

            # cancel it.
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                print("main(): cancel_me is cancelled now")

        # stopping the loop after this function
        self.loop.stop()
        
    # async def unsubscribe(self, service: str) -> dict:
    #     """Unsubscribe from a service.
    #     Arguments:
    #     ----
    #     service {str} -- The name of the service, to unsubscribe from. For example,
    #         "LEVELONE_FUTURES" or "QUOTES".
    #     Returns:
    #     ----
    #     dict -- A message from the websocket specifiying whether the unsubscribe command
    #         was successful.
    #     """

    #     # self.unsubscribe_count += 1

    #     # service_count = len(self.data_requests['requests']) + self.unsubscribe_count
        
    #     # request = {
    #     #     "requests":[
    #     #         {
    #     #             "service": service.upper(), 
    #     #             "requestid": service_count, 
    #     #             "command": 'UNSUBS',
    #     #             "account": self.user_principal_data['accounts'][0]['accountId'],
    #     #             "source": self.user_principal_data['streamerInfo']['appId']
    #     #         }
    #     #     ]
    #     # }

    #     # await self._send_message(json.dumps(request))

    #     # return await self._receive_message(return_value=True)
    
    async def _send_message(self, message: str):
        """Sends a message to webSocket server
        Arguments:
        ----
        message {str} -- The JSON string with the
            data streaming service subscription.
        """        

        await self.connection.send(message)

    async def _receive_message(self, return_value: bool = False) -> dict:
        """Recieves and processes the messages as needed.
        Keyword Arguments:
        ----
        return_value {bool} -- Specifies whether the messages should be returned
            back to the calling function or not. (default: {False})
        Returns:
        ----
        {dict} -- A python dictionary
        """

        # Keep going until cancelled.
        while True:

            try:
                # Grab the Message
                message = await self.connection.recv()
                # Parse Message
                message_decoded = await self._parse_json_message(message=message)
               
                
                # if "data" in message_decoded:
                #     for single in message_decoded["data"][0]['content']:
                #         if single['3'] > 1000:
                #             print(single['3'])

                #returning when it's true, usually if its a pipeline
                if return_value:
                        return message_decoded

            except websockets.exceptions.ConnectionClosed:

                # stop the connection if there is an error.
                print('Connection with server closed')
                break

    async def _parse_json_message(self, message: str) -> dict:
        """Parses incoming messages from the stream
        Arguments:
        ----
        message {str} -- The JSON string needing to be parsed.
        Returns:
        ----
        dict -- A python dictionary containing the original values.
        """        

        try:
            message_decoded = json.loads(message)
        except:
            message = message.encode('utf-8').replace(b'\xef\xbf\xbd', bytes('"None"','utf-8')).decode('utf-8')
            message_decoded = json.loads(message)
        
        return message_decoded

    async def _check_connection(self) -> bool:
        """Determines if we have an active connection
        There are multiple times we will need to check the connection 
        of the websocket, this function will help do that.
        Raises:
        ----
        ConnectionError: An error is raised if we can't connect to the
            websocket.
        Returns:
        ----
        bool -- True if the connection healthy, False otherwise.
        """        

        # if it's open we can stream.
        if self.connection.open:
            print('Connection established. Streaming will begin shortly.')
            return True
        elif self.connection.close:
            print('Connection was never opened and was closed.')
            return False
        else:
            raise ConnectionError


    async def heartbeat(self, connection):
        '''
            Sending heartbeat to server every 5 seconds
            Ping - pong messages to verify connection is alive
        '''
        while True:
            try:
                await connection.send('ping')
                await asyncio.sleep(3)
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break


