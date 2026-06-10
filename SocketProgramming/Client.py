# import socket
# import sys

# # An example script to connect to Google using socket
# # programming in Python
# import socket # for socket
# import sys

# try:
# 	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
# #AF_INET refers to the address-family ipv4
# #SOCK_STREAM means connection-oriented TCP protocol
# 	print ("Socket successfully created")
# except socket.error as err:
# 	print ("socket creation failed with error %s" %(err))

# # default port for socket
# port = 80

# try:
# 	host_ip = socket.gethostbyname('www.google.com')
# except socket.gaierror:

# 	# this means could not resolve the host
# 	print ("there was an error resolving the host")
# 	sys.exit()

# # connecting to the server
# s.connect((host_ip, port))

# print ("the socket has successfully connected to google")

# print(port)
# ip = socket.gethostbyname('www.google.com')
# print(ip)

# # for the telnet you have to do these things
# # Open the Control Panel
# # Go to Programs & Features
# # In left bar select "Turn Windows features on or off"
# # Find "Telnet Client" and tick it
# # Click "OK"

# # Create a socket object
# s = socket.socket()        
 
# # Define the port on which you want to connect
# port = 12345               
 
# # connect to the server on local computer
# s.connect(('127.0.0.1', port))
 
# # receive data from the server and decoding to get the string.
# print (s.recv(1024).decode())
# # close the connection
# s.close()    
     

import socket


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    message = input(" -> ")  # take input

    while message.lower().strip() != 'bye':
        client_socket.send(message.encode())  # send message
        data = client_socket.recv(1024).decode()  # receive response

        print('Received from server: ' + data)  # show in terminal

        message = input(" -> ")  # again take input

    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()