import socket
import pyaudio
import os
import json
import pickle
import threading
import time

# BUFFER_SIZE = 1024
# CHANNELS = 2
# FORMAT = pyaudio.paInt16
# RATE = 44100
# is_paused = False
# is_finished = False


class Client():

    def __init__(self) -> None:
        self.__BUFFER_SIZE = 1024
        self.__CHANNELS = 2
        self.FORMAT = pyaudio.paInt16
        self.RATE = 44100
        self.is_paused = False
        self.is_finished = False
        self.out_music = False
        self.music_cancel = False

    def __list_devices(self, client_socket):
        msg = {'service-type': 'list_devices'}
        msg_bytes = json.dumps(msg).encode('utf-8')
        client_socket.send(msg_bytes)
        devices = client_socket.recv(self.__BUFFER_SIZE)
        list_devices = pickle.loads(devices)
        k = 0
        print("\n")
        print("---------------------------------------")
        for i in list_devices:
            print(f"{k} - Host: {i[0]}, PORT: {i[1]}")
            k += 1
        print("---------------------------------------")
        print("\n")
        return list_devices

    def __list_songs(self, client_socket):
        msg = {'service-type': 'list_songs'}
        msg_bytes = json.dumps(msg).encode('utf-8')
        client_socket.send(msg_bytes)
        songs_list = client_socket.recv(self.__BUFFER_SIZE).decode()
        print("\n")
        print("Músicas disponíveis:")
        print("-----------------------------------------------")
        print(songs_list)
        print("-----------------------------------------------")
        print("\n")

    def __play_music_with_server(self, client_socket, song_choice, device=None):
        if device:
            msg = {'service-type': 'play_music',
                   'music': f'{song_choice}', 'device': device}
            msg_bytes = json.dumps(msg).encode('utf-8')
        else:
            msg = {'service-type': 'play_music', 'music': f'{song_choice}'}
            msg_bytes = json.dumps(msg).encode('utf-8')
        client_socket.send(msg_bytes)

        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT, channels=self.__CHANNELS, rate=self.RATE,
                        frames_per_buffer=self.__BUFFER_SIZE, output=True)
        data_of_file = b''
        end_message = b'\nnn'
        while True:
            if not self.is_paused:
                data = client_socket.recv(self.__BUFFER_SIZE)
                data_of_file += data
                if data[-3:] == end_message:
                    self.is_finished = True
                    break
                stream.write(data)
            else:
                continue

        if os.path.isdir("cache") == False:
            os.makedirs("cache")

        if len(data_of_file) != 0:
            file = open(f'cache/{song_choice}', 'wb')
            file.write(data_of_file)
            file.close()

        stream.stop_stream()
        stream.close()

    def __play_music_with_cache(self, song_choice):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT, channels=self.__CHANNELS,
                        rate=self.RATE, output=True)
        print("Reproduzindo do cache...")
        with open(f'cache/{song_choice}', 'rb') as file:
            while True:
                if not self.is_paused:
                    data = file.read(self.__BUFFER_SIZE)
                    stream.write(data)
                if not data:
                    self.is_finished = True
                    break

    def __handle_user_input(self):
        self.out_music = False
        while not self.is_finished:
            command = input(
                "Digite 'p' para pausar ou 'r' para retomar a reprodução:")
            if command == 'p':
                self.is_paused = True
                print("Reprodução pausada.")
            elif command == 'r':
                self.is_paused = False
                print("Reprodução retomada.")
            else:
                print("Comando inválido.")

        time.sleep(1)
        self.is_finished = False
        self.is_paused = False
        print("Reprodução finalizada.")
        print("\x1b[2J")

    def __end_connection(self, client_socket):
        msg = {'service-type': 'end_connection'}
        msg_bytes = json.dumps(msg).encode('utf-8')
        client_socket.send(msg_bytes)
        client_socket.close()
        print("Conexão encerrada.")

    def __play_music_code(self, cache=False, song_choice=None, client_socket=None, device=None):
        if cache:
            thread_play_music = threading.Thread(
                target=self.__play_music_with_cache, args=(song_choice,), daemon=True)
            thread_play_music.start()
        else:
            if device:
                thread_play_music = threading.Thread(target=self.__play_music_with_server, args=(
                    client_socket, song_choice, device,), daemon=True)
                thread_play_music.start()
            else:
                thread_play_music = threading.Thread(target=self.__play_music_with_server, args=(
                    client_socket, song_choice,), daemon=True)
                thread_play_music.start()
        self.__handle_user_input()

    def start_client(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("192.168.18.123", 12345))
        sock_address = client_socket.getsockname()

        while True:
            print(
                "--------------------------------------------------------------------------------------------------")
            command = input(
                '1 - Listar dispositivos disponíveis\n2 - Listar músicas disponíveis\n3 - Tocar Música\n4 - Encerrar Conexão\n5 - Encerrar Conexão\n')
            print(
                "--------------------------------------------------------------------------------------------------")
            match (command):
                case '1':
                    self.__list_devices(client_socket)

                case '2':
                    self.__list_songs(client_socket)
                case '3':
                    song_choice = input(
                        "Digite o nome da música que deseja reproduzir: ")
                    devices = self.__list_devices(client_socket)

                    device_choice = input(
                        "Digite o índice do dispositivo que deseja reproduzir. ")

                    if devices[int(device_choice)][0] == sock_address[0] and devices[int(device_choice)][1] == sock_address[1]:
                        if os.path.isdir("cache"):
                            songs_cache = os.listdir('cache')
                            if song_choice in songs_cache:
                                self.__play_music_code(
                                    cache=True, song_choice=song_choice, client_socket=client_socket)
                            else:
                                print(
                                    "Música não encontrada no cache local, transmitindo pelo servidor...")
                                self.__play_music_code(
                                    cache=False, song_choice=song_choice, client_socket=client_socket)
                        else:
                            print(
                                "Música não encontrada no cache local, transmitindo pelo servidor...")
                            self.__play_music_code(
                                cache=False, song_choice=song_choice, client_socket=client_socket)
                    else:
                        print(
                            f"Reproduzindo no dispositivo {device_choice[0]}...")
                        self.__play_music_code(
                            cache=False, song_choice=song_choice, client_socket=client_socket, device=devices[int(device_choice)])
                case '4':
                    music_choice = client_socket.recv(
                        self.__BUFFER_SIZE).decode()
                    print(f"Reproduzindo {music_choice}... ")
                    self.__play_music_with_server(
                        client_socket, music_choice)
                    self.__handle_user_input()
                case '5':
                    self.__end_connection(client_socket)
                    break
        print("\x1b[2J")


client = Client()
client.start_client()
