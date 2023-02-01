# # first of all import the socket library
# import socket			

# # next create a socket object
# s = socket.socket()		
# print ("Socket successfully created")

# # reserve a port on your computer in our
# # case it is 12345 but it can be anything
# port = 12345			

# # Next bind to the port
# # we have not typed any ip in the ip field
# # instead we have inputted an empty string
# # this makes the server listen to requests
# # coming from other computers on the network
# s.bind(('', port))		
# print ("socket binded to %s" %(port))

# # put the socket into listening mode
# s.listen(5)	
# print ("socket is listening")		

# # a forever loop until we interrupt it or
# # an error occurs
# while True:

#     # Establish connection with client.
#     c , addr = s.accept()	
#     print ('Expected indented blockPylanceGot connection from', addr )

#     # send a thank you message to the client. encoding to send byte type.
#     c.send('Thank you for connecting'.encode())

#     # Close the connection with the client
#     c.close()

#     # Breaking once connection closed
#     break


import socket


def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            break
        print("from connected user: " + str(data))
        data = input(' -> ')
        conn.send(data.encode())  # send data to the client

    conn.close()  # close the connection


if __name__ == '__main__':
    server_program()