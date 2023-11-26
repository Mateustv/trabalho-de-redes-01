
import socket
import os
import wave
from _thread import *
import json
import pickle


class Server():
    def __init__(self) -> None:
        self.__devices = []
        self.__BUFFER_SIZE = 1024
        self.__sockets = {}

    def __list_devices(self, client_socket):
        print('Aparelhos conectados:')
        print(self.__sockets)
        client_socket.send(pickle.dumps(self.__devices))

    def __list_songs(self, client_socket):
        print('Musicas disponiveis:')
        songs = os.listdir('resource')
        songs = [song for song in songs if song.endswith(".wav")]
        songs_str = "\n".join(songs)
        client_socket.send(songs_str.encode())

    def __play_music_server(self, client_socket, song_choice):
        if os.path.exists(f"resource/{song_choice}"):
            with wave.open(f"resource/{song_choice}", "rb") as song_file:
                data = song_file.readframes(self.__BUFFER_SIZE)
                while data != b'':
                    client_socket.send(data)
                    data = song_file.readframes(self.__BUFFER_SIZE)
                song_file.close()
                end_message = "\nnn".encode()
                client_socket.send(end_message)

    def __handle_client(self, client_socket, client_address):
        print(f"Conexão estabelecida com o cliente {client_address} \n")

        while True:
            command = client_socket.recv(1024).decode()
            request = json.loads(command)
            print(request)
            if request['service-type'] == 'list_devices':
                self.__list_devices(client_socket)
            elif request['service-type'] == 'list_songs':
                self.__list_songs(client_socket)
            elif request['service-type'] == 'play_music':
                music = request['music']
                if 'device' in request:
                    ip_device_target = request['device'][0]
                    song_choice = music.encode()
                    socket_target = self.__sockets[ip_device_target]
                    socket_target.send(song_choice)
                else:
                    self.__play_music_server(client_socket, music)
            elif request['service-type'] == 'end_connection':
                self.__devices.remove([client_address[0], client_address[1]])
                client_socket.close()
                print(f"Conexão encerrada com o cliente {client_address}")
                break

    def __obter_ip(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except socket.error:
            return "Não foi possível obter o endereço IP"

    def start_server(self):
        # self.__obter_ip()
        # "192.168.18.123"

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(server_socket)
        server_socket.bind((self.__obter_ip(), 12345))
        server_socket.listen(5)
        print("Servidor iniciado. Aguardando conexões...")

        while True:
            client_socket, client_address = server_socket.accept()
            print(client_socket)
            self.__sockets[client_address[0]] = client_socket
            self.__devices.append([client_address[0], client_address[1]])
            start_new_thread(
                self.__handle_client, (self.__sockets[client_address[0]], client_address))


server = Server()
server.start_server()
