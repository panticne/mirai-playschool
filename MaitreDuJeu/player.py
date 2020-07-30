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

