from w_sockets_final import WebSocket_TD

print("Enter stock ticker to stream: ")
ticker = input()


stream_ts = WebSocket_TD()
stream_ts.stream(ticker)


