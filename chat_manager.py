import socket
import requests
from typing import Optional, Any

def read_next_kv(p:list[str]):
    if(len(p) < 2):
        return None, None
    k = p.pop(0)
    v = p.pop(0)
    return k, v

def verify_packet(p:str) -> Optional[list[str]]:
    if(p == None): return None
    lis = p.split("<#?=~>")
    length = len(lis)
    if(length == 0 or length == 0 or length%2 != 0):
        return None
    return lis

class Chat:
    sock: socket.socket
    ip: str
    port: int
    key: str

    def __init__(self, ip:str, port:int, key:str) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(3)

        self.key = key
        self.ip = ip
        self.port = port

    def recv_data(self) -> Optional[str]:
        try:
            m, a = self.sock.recvfrom(2048)
            return m.decode()
        except:
            return None

    def get_head_url(self, name:str) -> str:
        return f'https://minotar.net/helm/{name}/48'

    def check_server_connection(self) -> bool:
        self.sock.sendto("ping<#?=~>None".encode(), (self.ip, self.port))
        m = self.recv_data()
        if(m == "pong"):
            return True
        return False

    def check_key(self) -> bool:
        self.sock.sendto(f"key<#?=~>{self.key}".encode(), (self.ip, self.port))
        m = self.recv_data()
        if(m == "LOGGED IN"):
            return True
        return False

    def get_new_chats(self) -> list[list[str, str]]:
        self.sock.sendto(f"key<#?=~>{self.key}<#?=~>GET-CHAT<#?=~>None".encode(), (self.ip, self.port))
        m = self.recv_data()
        if(m != "LOGGED IN"): return []
        m = self.recv_data()
        p = verify_packet(m)
        if(p == None): return []
        k, v = read_next_kv(p)
        if(k != "CHAT"):
            return []
        num_chats = int(v)
        chats = []
        for i in range(num_chats):
            k, v = read_next_kv(p)
            if(k == None or v == None):
                return [[]]
            chats.append([k, v])
        return chats
    
    def send_chat(self, sender: str, msg: str) -> bool:
        self.sock.sendto(f"key<#?=~>{self.key}<#?=~>SAY<#?=~>[{sender}]: {msg}".encode(), (self.ip, self.port))
        m = self.recv_data()
        if(m != "LOGGED IN"): return False
        m = self.recv_data()
        if(m != "DONE"): return False
        return True