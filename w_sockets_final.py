from TD_API_Calls import TD_API_Calls
import json
import websockets
import asyncio
import nest_asyncio
import datetime



class WebSocket_TD:

    def __init__(self):
        #getting login, data info, and url from main TD class
        TD_client = TD_API_Calls()
        self.log_data_url = TD_client.get_cred()
        self.connection: websockets.WebSocketClientProtocol = None

        #either get an event loop (which stores coroutines to switch beteween) or create a new one
        try:
            self.loop = asyncio.get_event_loop()
        except websockets.WebSocketException:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def stream(self):
        """Starts the stream and prints the output to the console.
        Initalizes the stream by building a login request, starting 
        an event loop, creating a connection, passing through the 
        requests, and keeping the loop running."""
        try:
            # Connect to the Websocket.
            self.loop.run_until_complete(self._connect(pipeline_start=False))

            # Send the Request.
            asyncio.ensure_future(self._send_message(self.log_data_url[1]))

            # Start Recieving Messages.
            asyncio.ensure_future(self._receive_message(return_value=False))

            # Keep the Loop going, until an exception is reached.
            self.loop.run_forever()
        except:
            self.close_stream()


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
        login_request = self.log_data_url[0]

        # Create a connection.
        self.connection = await websockets.client.connect(self.log_data_url[2])

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
    
    def shut_down(self):
        self.close_stream()

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
               
                
                if "data" in message_decoded:
                    # format -> {'seq': 310, 'key': 'AAPL', '1': 1587759182311, '2': 282.96, '3': 76.0, '4': 124604}
                    for single in message_decoded["data"][0]['content']:
                        if single['3'] > 100:
                            print(single)

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


timesale_socket = WebSocket_TD()

timesale_socket.stream()

