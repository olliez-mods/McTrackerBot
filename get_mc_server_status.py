# Import necessary modules
import socket
import struct
import json
import requests

# Define a function to unpack a variable-length integer from a stream
def unpack_varint(s):
    # Initialize the value and read up to 5 bytes
    d = 0
    for i in range(5):
        b = ord(s.recv(1)) # Receive a single byte
        d |= (b & 0x7F) << 7*i # Shift and OR the byte into the value
        if not b & 0x80: # Check if the last bit is 0
            break
    return d

def unpack_string(s):
    l = unpack_varint(s) # String length

    d = b""
    while len(d) < l:
        d += s.recv(1) # Receive 1 byte at a time until we have our data
    
    return d.decode('utf8')

# Define a function to pack a variable-length integer into a stream
def pack_varint(d):
    o = b"" # Initialize an empty byte string
    while True:
        b = d & 0x7F # Get the last 7 bits of the value
        d >>= 7 # Shift the value 7 bits to the right
        o += struct.pack("B", b | (0x80 if d > 0 else 0)) # Pack the byte into the stream, setting the last bit if there are more bytes
        if d == 0: # Stop if we have no more bits to pack
            break
    return o

def pack_varstring(s):
    b = s.encode("utf-8") # Encode the string as bytes using UTF-8
    return pack_varint(len(b)) + b # Pack the length of the bytes and the bytes themselves into the stream

# Define a function to pack data into a stream
def pack_data(d):
    h = pack_varint(len(d)) # Pack the length of the data as a variable-length integer
    if type(d) == str: # If the data is a string, encode it as bytes
        d = bytes(d, "utf-8")
    return h + d # Concatenate the length and data bytes

# Define a function to pack a port into a stream
def pack_port(i):
    return struct.pack('>H', i) # Pack the port as a big-endian unsigned short (2 bytes)

# checks whether we have a connection to the interner, will only work if google.com is online
def is_connected():
    try:
        # attempt to connect to googles servers, if yes then yes, otherwise no
        requests.head("http://www.google.com/", timeout=2)
        return True
    except requests.ConnectionError:
        return False
    except:
        pass
    


# Define a function to get the status of a Minecraft server
def get_status(host: str='localhost', port: int=25565) -> dict:

    if(not is_connected()):
        return {'connected':0, 'online':-1, 'count':-1, 'players':[]}

    # Create a TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.settimeout(2)
        s.connect((host, port)) # Attempt to connect to the server
    except:
        return {'connected':1, 'online':0, 'count':-1, 'players':[]} # Return this is we can't connect


    try:
        # Send a handshake and status request packet
        s.send(pack_data(b"\x00\x00" + pack_data(host.encode('utf8')) + pack_port(port) + b"\x01")) # Handshake packet
        s.send(pack_data("\x00")) # Status request packet

        # Read the response packet
        unpack_varint(s)     # Packet length
        unpack_varint(s)     # Packet ID
        data = unpack_string(s) # String

        data_json = json.loads(data)
        # Close the socket
        s.close()

        if("sample" in data_json["players"]):
            for i in range(len(data_json["players"]["sample"])):
                if(data_json["players"]["sample"][i]["name"] == "Anonymous Player"):
                    del data_json["players"]["sample"][i]
                    data_json["players"]["online"] -= 1
                    break

        results = {'connected':1, 'online':1, 'count':0, 'players':[]} # response if no one is online
        results['count'] = int(data_json['players']['online']) # add the number of players

        if("sample" in data_json['players']):
            # add player names to list
            for player in data_json['players']['sample']:
                results['players'].append(player['name'])
        return results
    except:
        return {'connected':1, 'online':1, 'count':0, 'players':[]} # Return an error because something went wrong



if __name__ == "__main__":
    print(str(get_status("localhost", 25565)))