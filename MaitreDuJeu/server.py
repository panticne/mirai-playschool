""" This file is the server of the game Mirai-playschool"""

__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "nemanja.pantic@heig-vd.ch"
__status__ = "Prototype"

import argparse
import pickle
import socket
import threading
import time
from art import *
from queue import Queue


class Player:
    """
    A class to represent a player.
    """

    def __init__(self, ip, cards, score):
        """
        The constructor of player class.
        :param ip: IP of the player.
        :param cards: List of cards that the player infected.
        :param score: Score that the player obtained during the party.
        """
        self.ip = ip
        self.cards = cards
        self.score = score

    def __str__(self):
        """
        Method used to get a well formed print(player)
        :return: The string which represent a player
        """
        return "I'm the player {}, my last score was {} and I infected {}\n".format(self.ip, self.score, self.cards)

    def clear_variable(self):
        """
        Set score to 0 and remove infected cards. It's used to start a new game.
        :return: Nothing
        """
        self.cards = []
        self.score = 0


class Server:
    """
    a class to represent a Server.
    The server take the current IP address of the host and listen on port "port_player" for cards and on port "port_card" for players.

    """

    def __init__(self, minimal_player, minimal_card, timer, delay, port_player, port_card):
        """
        The constructor of Server class.
        :param minimal_player: Represent the minimal player to start a game.
        :param minimal_card: Represent the minimal card to start a game.
        :param timer: Represent the duration of a game.
        :param delay: Represent the synchronization time between server and cards.
        :param port_player: Listening port for player.
        :param port_card: Listening port for card.
        """
        self.minimal_player = minimal_player
        self.minimal_card = minimal_card
        self.timer = timer
        self.delay = delay
        self.port_player = port_player
        self.port_card = port_card

        # Number of thread to create
        self.NUMBER_OF_THREADS = 5
        # Job that we need to create
        self.JOB_NUMBER = [1, 2, 3, 4, 5]
        self.queue = Queue()
        # Contain cards and players information
        self.all_connections_rasp = []
        self.all_connections_player = []
        self.all_rasp = []
        self.all_player = []
        self.thread = []
        # Used to synchronize thread when game start and end.
        self.game_start = False
        # Score of players
        self.newdict = dict()
        #
        self.historic_games = []
        # Used to lock access on variables while writing and reading
        self.lock = threading.Lock()

        self.game_crash = False

    def run_server(self):
        """
        Method used to start the different server threads.
        :return:
        """
        Server.create_workers(self)
        Server.create_jobs(self)

    def historic(self, score):
        print("Inside historic")
        """
        Used to add the final score game to a historic file stored in ./historic.txt
        :param score: The final score of the game
        :return: None
        """
        with self.lock:
            with open("historic.txt", "a") as f:
                f.write(str(score) + "\n")

    def show_historic(self):
        """
        Used to print on prompt the historic file
        :return: None
        """
        with self.lock:
            with open("historic.txt", 'r') as f:
                line = f.read().splitlines()
        count = 1
        # Strips the newline character
        for line in line:
            print("Game {}: had the score : {}".format(count, line.strip()))
            count += 1

    def delete_historic(self):
        """
        Used to delete erase the file ./historic.txt
        :return: None
        """
        with self.lock:
            with open("historic.txt", "w") as f:
                f.close()

    def check_game_is_ok(self):
        """This method check if a game can start (minimal 2 players)

        :return: True / False
        :rtype: Boolean
        """
        with self.lock:
            if len(self.all_player) < self.minimal_player and len(self.all_rasp) < self.minimal_card:
                print("You need to add cards and player.\n The minimal cards number are {} and minimal player are {}".format(self.minimal_card, self.minimal_player))
                return False
            if len(self.all_player) < self.minimal_player:
                print("You should play with someone, it's funnier!\n The minimal player are {}.".format(self.minimal_player))
                return False
            if len(self.all_rasp) < self.minimal_card:
                print("More cards for more fun!\n The minimal card are {}.".format(self.minimal_card))
                return False
            if len(self.all_player) == 0 and len(self.all_rasp) == 0:
                print("You can't start a game without card and player.")
                return False


        return True

    def create_socket(self):
        """
        Setup the socket for Raspberry Pi Zero W.

        :return: no value
        :rtype: None
        """
        try:
            global s
            s = socket.socket()

        except socket.error as msg:
            print("Socket creation error: " + str(msg))

    def create_socket_player(self):
        """
        Setup the socket for player.

        :return: no value
        :rtype: None
        """
        try:
            global t
            t = socket.socket()

        except socket.error as msg:
            print("Socket creation error: " + str(msg))

    def bind_socket(self):
        """
        Binding the socket and listening for connections from cards.

        :return: no value
        :rtype: None
        """
        try:
            global s
            host = ""
            port = self.port_card
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen(40)

        except socket.error as msg:
            print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
            Server.bind_socket(self)

    def bind_socket_player(self):
        """
        Binding the socket and listening for connections from players.

        :return: no value
        :rtype: None
        """
        try:

            host = ""
            port = self.port_player
            global t
            t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            t.bind((host, port))
            t.listen(40)

        except socket.error as msg:
            print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
            Server.bind_socket_player(self)

    def accepting_connections(self):
        """
        This method is used to accept every connection send by different cards and store them in a list.

        :return: no value
        :rtype: None
        """
        for c in self.all_connections_rasp:
            c.shutdown(socket.SHUT_RDWR)
            c.close()

        del self.all_connections_rasp[:]
        del self.all_rasp[:]

        while True:
            try:
                conn, address = s.accept()
                s.setblocking(1)  # prevents timeout
                self.all_connections_rasp.append(conn)
                self.all_rasp.append(address)
                print("\n" + address[0] + " Raspberry Card joined the party")
            except:
                print("Error accepting connections")

    def accepting_connections_player(self):
        """
        This method is used to accept every connection send by different player and store them in a list.

        :return: no value
        :rtype: None
        """
        for c in self.all_connections_player:
            c.shutdown(socket.SHUT_RDWR)
            c.close()

        del self.all_connections_player[:]
        del self.all_rasp[:]

        while True:
            try:
                conn, address = t.accept()
                t.setblocking(1)  # prevents timeout

                self.all_connections_player.append(conn)
                self.all_player.append(Player(address[0], [], 0))
                print("\n" + address[0] + " player joined the party")

            except:
                print("Error accepting connections")

    def mirai_playschool(self):
        """
        This method is used to check the command that the administrator put on the prompt and execute the wanted action.

        You are allowed to do some action if you type a number or "select <target>"
        Action:
        ------
        1:  You will be redirected in the "Start game" prompt
            Start game prompt :
                1:  You can set the timer for a game, enter the number of minutes. The timer represent the duration of a game.
                2:  You can set the delay for a game, enter the number of seconds. The delay represent the Synchronization time between server and cards. It synchronizes the score and the infected cards.
                3:  You can start a game with this command.
                4:  You can set the minimal required player to start a game.
                5:  You can set the minimal required card to start a game.
                6:  You can go back to the main prompt.
        select <id>:    This command is used to connect the server to a card. The ID is the index number of the card in the list all_rasp.
        3:  You will list all the connected card to this server.
        4:  You will list all the connected player to this server.
        5:  You will close all current connection in all_player and all_rasp.
        6:  You will reboot all the card.
        7:  You will print the list of previous game.
        8:  You will erase the list of previous game.
        9:  You will get help.
        :return: no value
        :rtype: None
        """
        Art = text2art('Mirai-playschool')
        print(Art)
        while True:
            cmd = input(
                '\n\n1) Create game\nselect <id>) Access to a Raspberry Pi card\n3) List connected Raspberry Pi '
                'Card\n4) '
                'List player\n5) Disconnect all connected host\n6) Reboot env\n7) Show historic\n8) Delete '
                'historic\n9) help\nmirai-playschool> Enter the action of your '
                'choice :')
            if cmd == '1':
                while True:
                    cmd = input(
                        '\n\n1) Set timer\n2) Set delay\n3) Start game\n4) Set minimal '
                        'player\n5) Set minimal card\n6) Return main menu\nmirai-playschool> Enter '
                        'the action of your choice :')
                    if cmd == '1':
                        number = input('Enter the number of minute : ')
                        if number.isdigit():
                            with self.lock:
                                self.timer = int(number) * 60
                                print("The timer is now {} seconds".format(self.timer))

                        else:
                            print('Please enter a valid number')
                    if cmd == '2':
                        number = input('Enter the number of seconds : ')
                        if number.isdigit():
                            with self.lock:
                                self.delay = int(number)
                            print("The delay is now {} seconds".format(self.delay))
                        else:
                            print('Please enter a valid number')
                    if cmd == '3':
                        Server.start_game(self)
                    if cmd == '4':
                        number = input('Enter the minimal number of player : ')
                        if number.isdigit():
                            with self.lock:
                                self.minimal_player = int(number)
                            print("The minimal player is now {}".format(self.minimal_player))

                        else:
                            print('Please enter a valid number')
                    if cmd == '5':
                        number = input('Enter the minimal number of card : ')
                        if number.isdigit():
                            with self.lock:
                                self.minimal_card = int(number)
                            print("The minimal card is now {}".format(self.minimal_card))
                        else:
                            print('Please enter a valid number')
                    if cmd == '6':
                        break
            elif 'select' in cmd:
                conn = Server.get_target(self, cmd)
                if conn is not None:
                    Server.send_target_commands(self, conn)
            elif cmd == '3':
                for x in range(len(self.all_rasp)):
                    print("ID : {} Card: {}".format(x, self.all_rasp[x][0]))
            elif cmd == '4':
                for player in self.all_player:
                    print(player)
            elif cmd == '5':
                m = pickle.dumps(['shutdown'])
                Server.send_request_all(self, m)
            elif cmd == '6':
                m = pickle.dumps(['reboot'])
                Server.send_request_card(self, m)
            elif cmd == '7':
                Server.show_historic(self)
            elif cmd == '8':
                Server.delete_historic(self)
            elif cmd == '9':
                help(Server.mirai_playschool)
            else:
                print("Command not recognized")

    def start_game(self):
        """This method is used to start a game.
        :return: no value
        :rtype: None
        """
        # If the starting game condition isn't respected, we return on main while.
        if not (Server.check_game_is_ok(self)):
            return
        # take only IP
        only_ip = set()
        # We remove the old score and infected cards of all players.
        for player in self.all_player:
            player.clear_variable()
        # We create the keys for the dict containing the score
        for i in range(len(self.all_player)):
            only_ip.add(self.all_player[i].ip)
        score = dict({i: 0 for i in only_ip})
        # We send the signal to start a game to all the cards.
        m = pickle.dumps(['go', score, self.delay])
        print("Sending game start!")
        Server.send_request_card(self, m)
        # We start all thread working
        with self.lock:
            self.game_start = True
        # We create thread to monitor the timer and to get score from cards.
        thread_timer = threading.Thread(target=Server.count_timer, args=[self, self.timer])
        thread_timer.daemon = True
        thread_timer.start()

        thread_score = threading.Thread(target=Server.get_score, args=[self])
        thread_score.daemon = True
        thread_score.start()
        # To don't leave the method, we wait 1 second while the game didn't end and check if game crashed.
        while self.game_start:
            if self.game_crash:
                self.game_start = False
                self.game_crash = False
                return
            time.sleep(1)
        Server.historic(self, self.newdict)
        # We notify all cards that the game just finished.
        m = pickle.dumps(['stop'])
        Server.send_request_card(self, m)
        # We attribute the final score to all different player
        for player in self.all_player:
            player.score = self.newdict[player.ip]
            print(player)
        # And we finally print the winner
        Server.get_winner(self)

    def maximum_keys(self, dic):
        """
        This method is used to get the maximum score from a dict.
        :param dic: Contain the winner of the game.
        :return: the keys from winner and the maximum score.
        """
        maximum = max(dic.values())
        keys = filter(lambda x: dic[x] == maximum, dic.keys())
        return keys, maximum

    def get_winner(self):
        """
        Used to print the winner/winners in prompt.
        :return: None
        """
        winner = Server.maximum_keys(self, self.newdict)
        # In case we have more than one winner
        winner_list = []
        for player in winner[0]:
            winner_list.append(player)

        if len(winner_list) > 1:

            print("The winner are : {} who get a score of {}".format(winner_list, winner[1]))
        else:

            print("The winner is : {} who get a score of {}".format(winner_list, winner[1]))


    def add_infected_card(self, value):
        """
        This method is used to add to a player the card that he infected and notify all rasp that this card is infected
        :param value: list containing "infected" + ip_player + infected_ip_card + score.
        :return:
        """
        for player in self.all_player:
            if player.ip == value[1]:
                print(
                    "A new infection has been detected, the player {}, infected the card {}".format(value[1], value[2]))
                player.cards.append(value[2])
                m = pickle.dumps(["infected", player])
                Server.send_request_card(self, m)

    def get_score(self):
        """
        This method is used to periodically get the score sent by cards and to print them on the prompt.

        :return: no value
        :rtype: None
        """

        while self.game_start:

            interm_score = []
            for x in range(len(self.all_connections_rasp)):
                try:

                    conn = self.all_connections_rasp[x]
                    data = conn.recv(1024)
                    temp = pickle.loads(data)

                except:
                    print("The card {} leaved the game.".format(self.all_rasp[x]))
                    del self.all_connections_rasp[x]
                    del self.all_rasp[x]
                    if len(self.all_connections_rasp):
                        print("They still have cards, the game continue and player who get point on this level lost "
                              "them")
                        continue
                    else:
                        with self.lock:
                            self.game_crash = True
                        print("We don't have cards anymore.. game will end as soon as possible")
                        return
                if temp[0] == "infected":
                    Server.add_infected_card(self, temp)
                    print("end of add_infected_card")
                    interm_score.append(temp[3])
                else:
                    interm_score.append(temp[0])

            try:
                list_key = dict.keys(interm_score[0])
                self.newdict = dict({i: 0 for i in list_key})
            except:
                with self.lock:
                    self.game_start = False

            # All dict are similar then pick one of them
            for x in range(len(interm_score)):
                A = interm_score[x]
                for i in A.keys():
                    try:
                        self.newdict[i] += A[i]
                    except KeyError:
                        continue

            print("this is the current score {}".format(self.newdict))

        print("Stop listening score")

    def send_request_card(self, cmd):
        """This method is used send a command to all our network

        :param cmd: Represent the command that we want to send to different targets
        :return: no value
        :rtype: None
        """

        for x in range(len(self.all_connections_rasp)):
            conn = self.all_connections_rasp[x]
            conn.send(cmd)

    def send_request_all(self, cmd):
        """This method is used send a command to all our network

        :param cmd: Represent the command that we want to send to different targets
        :return: no value
        :rtype: None
        """

        for x in range(len(self.all_connections_rasp)):
            conn = self.all_connections_rasp[x]
            conn.send(cmd)

        for x in range(len(self.all_connections_player)):
            conn = self.all_connections_player[x]
            conn.send(cmd)

    def list_connections(self):
        """This method is used to periodically check the status of different Raspberry Pi Card.

        :return: no value
        :rtype: None
        """
        while True:
            while not self.game_start:
                results = ''

                for i, conn in enumerate(self.all_connections_rasp):
                    try:
                        m = pickle.dumps([' '])
                        conn.send(m)
                    except:
                        print("The raspberry pi: %s disconnected" % (self.all_rasp[i][0],))
                        del self.all_connections_rasp[i]
                        del self.all_rasp[i]
                        continue
                    results += str(i) + "   " + str(self.all_rasp[i][0]) + "   " + str(self.all_rasp[i][1]) + "\n"

                # print("----Clients----" + "\n" + results)
                time.sleep(1)

    def list_player(self):
        """This method is used to periodically check the status of different players.

        :return: no value
        :rtype: None
        """
        while True:

            results = ''

            for i, conn in enumerate(self.all_connections_player):
                try:
                    m = pickle.dumps([' '])
                    conn.send(m)
                except:
                    print("The player : {} left the game".format(self.all_player[i].ip))
                    del self.all_connections_player[i]
                    del self.all_player[i]
                    continue
                results += str(i) + "   " + str(self.all_player[i].ip) + "   " + "\n"

            # print("----Players----" + "\n" + results)
            time.sleep(1)

    def get_target(self, cmd):
        """This method is used to get the reverse shell from a specific target in the list of current Raspberry Pi

        :param cmd: Represent the command that we want to send to client
        :return: no value
        :rtype: None
        """
        try:
            target = cmd.replace('select ', '')  # target = id
            target = int(target)
            conn = self.all_connections_rasp[target]
            print("You are now connected to :" + str(self.all_rasp[target][0]))
            print(str(self.all_rasp[target][0]) + ">", end="")
            return conn
            # 192.168.0.4> dir

        except:
            print("Selection not valid")
            return None

    def send_target_commands(self, conn):
        """This method is used to communicate command when we get the reverse shell from our target.

        :param conn: Represent the connection that we gonna use to get a reverse shell
        :return: no value
        :rtype: None
        """
        while True:
            try:
                cmd = input()
                if cmd == 'quit':
                    break
                if cmd == '':
                    continue
                if len(str.encode(cmd)) > 0:
                    m = pickle.dumps(['reverse', cmd])
                    conn.send(m)
                    data = conn.recv(20480)
                    temp = pickle.loads(data)
                    print("{} {}".format(temp[0], temp[1]), end="")
            except:
                print("Card is down")
                break

    def create_workers(self):
        """We create thread here and we target the method "work" to start the wanted method.

        :return: no value
        :rtype: None
        """
        for i in range(self.NUMBER_OF_THREADS):
            self.thread.append(threading.Thread(target=Server.work, args=[self]))
            self.thread[i].daemon = True
            self.thread[i].start()

    def count_timer(self, timer):
        """We setup the future action that we gonna do and put them in a Queue.

        :param timer: Represent the number of seconds to wait
        :return: no value
        :rtype: None
        """
        print("\n")
        while timer:
            if self.game_crash:
                return
            mins, secs = divmod(timer, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            print(timeformat, end='\r')
            time.sleep(1)
            timer -= 1
        self.game_start = False

    def work(self):
        """When thread are created we will check the value present in the Queue and launch the wanted method.

        :return: no value
        :rtype: None
        """
        while True:

            x = self.queue.get()

            if x == 1:
                Server.create_socket(self)
                Server.bind_socket(self)
                Server.accepting_connections(self)

            if x == 2:
                Server.mirai_playschool(self)

            if x == 3:
                Server.create_socket_player(self)
                Server.bind_socket_player(self)
                Server.accepting_connections_player(self)

            if x == 4:
                Server.list_player(self)

            if x == 5:
                Server.list_connections(self)

    def create_jobs(self):
        """We setup the future action that we gonna do and put them in a Queue.

        :return: no value
        :rtype: None
        """
        for x in self.JOB_NUMBER:
            self.queue.put(x)

        self.queue.join()


def main():
    """Starting point of application, we get parameters in argv, assign them to the program and start different threads.

    :return: no value
    :rtype: None
    """
    parser = argparse.ArgumentParser(description="Mirai Playschool.")
    parser.add_argument("--timer", required=True, help="Time that you want to play")
    parser.add_argument("--delay", required=True, help="Time for periodic request from client")
    args = parser.parse_args()

    timer = int(args.timer) * 60

    delay = int(args.delay)

    server = Server(1, 1, timer, delay, 10000, 9999)
    server.run_server()


try:
    main()
except KeyboardInterrupt:
    print("\nGood bye, see you soon !")
    exit()
# except:
#    print("\n Some troubles here, watch Traceback")
