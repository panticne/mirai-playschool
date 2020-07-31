""" This file is the client which monitor Raspberry Pi Zero W of the game Mirai-playschool"""
# Source : https://www.youtube.com/watch?v=Iu8_IpztiOU
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
from queue import Queue
import ipaddress
from player import Player

NUMBER_OF_THREADS = 5
JOB_NUMBER = [1, 2, 3, 4, 5]
queue = Queue()
s = socket.socket()
host = '192.168.1.7'
port = 9999
game_start = False
try:
    s.connect((host, port))
except:
    print("The server is down")
lock = threading.Lock()
delay = 15
delayset = False
first_infection = False
list_player = []

# Source https://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
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


def monitoring_scan_easy():
    """
    This method is used to give point to a PLAYER which have emit a request to the current IP address
    Give 1 point
    :return: None
    """
    # Method to get IP of current Raspberry Pi Card
    # source :  https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    get_ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    get_ip.connect(("8.8.8.8", 80))
    ip_address = get_ip.getsockname()[0]
    while True:
        global game_start
        currentPi = set()
        while not game_start:
            pass
        while game_start:
            p = subprocess.Popen(('sudo','tcpdump', '-l', 'dst', ip_address), stdout=subprocess.PIPE)
            for row in iter(p.stdout.readline, b''):

                temp = row.split()
                ip = temp[2].decode("utf-8").split('.')
                final_ip = '.'.join(ip[:4])
                if is_valid_ipv4_address(final_ip):
                    if final_ip in score and final_ip not in currentPi:
                        with lock:
                            currentPi.add(final_ip)
                            score[final_ip] += 1
                            print(final_ip + " got a point in scan easy")

                    for player in list_player:
                        if final_ip in player.cards and final_ip not in currentPi:
                            with lock:
                                currentPi.add(final_ip)
                                score[player.ip] += 1
                            print("The player {} got a point in scan easy with the infected card {}".format(player.ip,
                                                                                                            final_ip))
                if not game_start:
                    p.terminate()
                    break


def monitoring_login_easy():
    """
    This method is used to give a point to a PLAYER which have etablished a valid connection to the current IP address
    Give 1 point
    :return: None
    """
    while True:
        currentPi = set()
        global game_start, list_player
        while not game_start:
            pass
        while game_start:
            p = subprocess.Popen(('who'), stdout=subprocess.PIPE)
            for row in iter(p.stdout.readline, b''):
                temp = row.split()
                if len(temp) == 5:
                    ip = temp[4]
                    ip = ip[1:len(ip) - 1].decode("utf-8")
                    if (ip in score and ip not in currentPi):
                        with lock:
                            currentPi.add(ip)
                            score[ip] += 1
                            print(ip + " got a point in login easy")
                    for player in list_player:
                        if ip in player.cards and ip not in currentPi:
                            with lock:
                                currentPi.add(ip)
                                score[player.ip] += 1
                                print("The player {} got a point in login easy with the infected card {}".format(
                                    player.ip, ip))
        p.terminate()


def monitoring_infection_easy():
    get_ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    get_ip.connect(("8.8.8.8", 80))
    current_ip = get_ip.getsockname()[0]

    while True:
        currentPi = set()
        global game_start
        while not game_start:
            pass
        while game_start:
            p = subprocess.Popen(('lsof', '-i', '-P', '-n'), stdout=subprocess.PIPE)
            for row in iter(p.stdout.readline, b''):
                row = row.decode("utf-8")
                temp = row.split()
                if temp[0] == "python3":
                    if len(temp) >= 9:
                        ip_temp = temp[8].split('->')
                        if len(ip_temp) >= 2:
                            if "*" in ip_temp[0]:
                                continue
                            ip1 = ip_temp[0]
                            ip2 = ip_temp[1]

                            ip1_temp_without = ip1.split(':')
                            ip2_temp_without = ip2.split(':')
                            ip1_without_port = ip1_temp_without[0]
                            ip2_without_port = ip2_temp_without[0]

                            if current_ip == ip1_without_port and ip2_without_port in score and ip2_without_port not in currentPi:
                                with lock:
                                    currentPi.add(ip2_without_port)
                                    score[ip2_without_port] += 2
                                    print(ip2_without_port + " got a point in INFECTION easy")
                                global first_infection
                                if not first_infection:
                                    with lock:
                                        first_infection = True
                                    # If it's the first time the card is infected, we send "infected" + ip CNC + ip Card +
                                    # current score
                                    m = pickle.dumps(["infected", ip2_without_port, current_ip, score])
                                    s.send(m)
                        else:
                            continue
                    else:
                        continue
                else:
                    continue
        p.terminate()


def work():
    """When thread are created we will check the value present in the Queue and launch the wanted method.

    :return: no value
    :rtype: None
    """
    while True:
        x = queue.get()

        if x == 1:
            monitoring_scan_easy()
        if x == 2:
            monitoring_login_easy()
        if x == 3:
            monitoring_infection_easy()
        if x == 4:
            send_score_server()
        if x == 5:
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
                    m = pickle.dumps([e, currentWD])
                    s.send(m)
                    continue
            if cmd[0] == 'wget':
                try:
                    p = subprocess.Popen(('wget', cmd[1]), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
                    output_byte = p.stdout.read() + p.stderr.read()
                    output_str = str(output_byte, "utf-8")
                    currentWD = os.getcwd() + "> "
                    m = pickle.dumps([output_str, currentWD])
                    s.send(m)

                    print(output_str)
                except:
                    currentWD = os.getcwd() + "> "
                    m = pickle.dumps([e, currentWD])
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
                    m = pickle.dumps([e, currentWD])
                    s.send(m)
                    continue


create_workers()
create_jobs()
