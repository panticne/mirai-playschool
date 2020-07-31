""" This file is the client which monitor Raspberry Pi Zero W of the game Mirai-playschool"""

__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "nemanja.pantic@heig-vd.ch"

import socket
import os
import signal
import threading
import subprocess
import time
import pickle
import ipaddress
from queue import Queue
from player import Player

NUMBER_OF_THREADS = 4
JOB_NUMBER = [1, 2, 3, 4]
queue = Queue()
s = socket.socket()
host = '192.168.1.7'
port = 9999
game_start = False
s.connect((host, port))
lock = threading.Lock()
delay = 15
delayset = False
first_infection = False
list_player = []
temp_ip = set()
timer = 3

def is_valid_ipv4_address(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError as errorCode:
        # uncomment below if you want to display the exception message.
        # print(errorCode)
        # comment below if above is uncommented.
        pass
        return False


def clean_list():
    """
    This method is used to clear a set every timer seconds.
    :return: None
    """
    global temp_ip, timer
    init_timer = timer
    while True:
        while not game_start:
            pass
        while game_start:
            while init_timer:
                time.sleep(1)
                init_timer -= 1
            with lock:
                temp_ip.clear()
                print(temp_ip)
            init_timer = timer


def send_score_server():
    """
    This method is used to send a score periodically to the server game (delay seconds). It starts when the game starts
    and end when the game end.
    :return: None
    """
    while True:
        global game_start, delay, delayset
        while not delayset:
            pass
        init_delay = delay
        while not game_start:
            pass

        while game_start:
            if init_delay == 0:
                init_delay = delay
                m = pickle.dumps([score])
                s.send(m)
            time.sleep(1)
            init_delay -= 1
        with lock:
            delayset = False


def monitoring_attack_easy():
    """
    This method is used to attribute point to a player who infected at least two cards and start an attack with
    all his cards.
    :return: None
    """
    get_ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    get_ip.connect(("8.8.8.8", 80))
    ip_address = get_ip.getsockname()[0]
    while True:
        global game_start, temp_ip
        currentPi = set()
        while not game_start:
            pass
        while game_start:
            p = subprocess.Popen(('tcpdump', '-l', 'dst', ip_address), stdout=subprocess.PIPE)
            for row in iter(p.stdout.readline, b''):

                temp = row.split()
                ip = temp[2].decode("utf-8").split('.')
                final_ip = '.'.join(ip[:4])
                print(final_ip)
                if is_valid_ipv4_address(final_ip):
                    with lock:
                        temp_ip.add(final_ip)
                        print(temp_ip)
                    for player in list_player:
                        if len(player.cards) >= 2:
                            result = all(elem in temp_ip for elem in player.cards)
                            if result and player.ip not in currentPi:
                                currentPi.add(player.ip)
                                score[player.ip] += 2
                                print(player.ip + " got a point in attack easy")
                if not game_start:
                    p.terminate()
                    break


def work():
    """When thread are created we will check the value present in the Queue and launch the wanted method.

    :return: no value
    :rtype: None
    """
    while True:
        x = queue.get()

        if x == 1:
            monitoring_attack_easy()
        if x == 2:
            send_score_server()
        if x == 3:
            clean_list()
        if x == 4:
            listening()

        queue.task_done()


def create_jobs():
    """We setup the future action that we gonna do and put them in a Queue.

    :return: no value
    :rtype: None
    """
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()


def create_workers():
    """We create thread here and we target the method "work" to start the wanted method.

    :return: no value
    :rtype: None
    """
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()


def start_game():
    """
    This method is used to start a game, it locks the game_start variable and set it up to True
    :return: None
    """
    with lock:
        global game_start
        game_start = True


def end_game():
    """
    This method is used to end a game, it locks the game_start variable and set it up to False
    :return:
    """
    with lock:
        global game_start, first_infection
        game_start = False
        first_infection = False


def listening():
    """
    This method is used to check request from server and execute the wanted task
    :return: None
    """
    while True:

        try:

            data = s.recv(1024)

            temp = pickle.loads(data)
        except:
            os.kill(os.getpid(), signal.SIGTERM)

        # We want to start the game, start env monitoring and attribute points
        if temp[0] == 'go':
            global score, delay, delayset
            with lock:
                score = temp[1]
                delay = temp[2]
                delayset = True
            start_game()

        if temp[0] == 'stop':
            end_game()

        if temp[0] == 'infected':
            print("A player infected a card, I need to attribute this IP score to the player")
            global list_player
            with lock:
                list_player.append(temp[1])

        if temp[0] == 'shutdown':
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            os.kill(os.getpid(), signal.SIGTERM)

        if temp[0] == 'reboot':
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            subprocess.Popen(('sudo', 'reboot'), stdout=subprocess.PIPE)

        if temp[0] == 'reverse':
            cmd = temp[1].split()
            if cmd[0] == 'cd':
                try:
                    os.chdir(cmd[1])
                except Exception as e:
                    currentWD = os.getcwd() + "> "
                    m = pickle.dumps([e , currentWD])
                    s.send(m)
                    continue

            if len(cmd[0]) > 0:
                try:
                    cmd = subprocess.Popen(temp[1], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                    output_byte = cmd.stdout.read() + cmd.stderr.read()
                    output_str = str(output_byte, "utf-8")
                    currentWD = os.getcwd() + "> "
                    m = pickle.dumps([output_str, currentWD])
                    s.send(m)

                    print(output_str)

                except Exception as e:
                    currentWD = os.getcwd() + "> "
                    m = pickle.dumps([e , currentWD])
                    s.send(m)
                    continue

create_workers()
create_jobs()

