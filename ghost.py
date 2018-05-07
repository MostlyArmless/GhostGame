import urllib.request
from pathlib import Path
import re
from string import ascii_letters as alphabet
import random
from randomdict import RandomDict
from enum import Enum
from pydispatch import dispatcher


class PlayerStatus(Enum):
    """Enum for player status tracking"""
    Alive = 1
    Forfeit = 2
    Killed = 3

    @classmethod
    def has_value(self, value):
        return any(value == item.value for item in self)


class ValidActions(Enum):
    """Enum to indicate the actions a player can take on their turn"""
    AppendLetter = 1
    Forfeit = 2
    Challenge = 3

    @classmethod
    def has_value(self, value):
        return any(value == item.value for item in self)


class Player:
    """AI player"""
    player_status = PlayerStatus.Alive

    def __init__(self):
        pass

    def forfeit(self):
        self.player_status = PlayerStatus.Forfeit
        dispatcher.send(signal=PlayerStatus.Forfeit, sender=self)

    def die(self):
        self.player_status = PlayerStatus.Killed
        dispatcher.send(signal=PlayerStatus.Killed, sender=self)

    def revive(self):
        self.player_status = PlayerStatus.Alive
        dispatcher.send(signal=PlayerStatus.Alive, sender=self)

    def get_next_action(self):
        # The AI will always attempt to append a letter
        return ValidActions.AppendLetter

    def get_letter(self):
        # Randomly select a letter from the alphabet
        return random.choice(alphabet[0:26])

    def validate_letter(self, l):
        # Letter must be in [a-z]
        if len(l) != 1:
            return False

        match = re.match(r'[a-zA-Z]', l)
        if match is None:
            return False
        else:
            return True


class HumanPlayer(Player):
    """Overrides the necessary methods of Player class to allow for human interaction"""

    def __init__(self):
        super().__init__(self)

    def get_letter(self):

        attempts = 0
        while attempts < 3:
            response = input('Enter a letter>>')
            if super().validate_letter(self, response):
                return response
            else:
                attempts += 1

        raise ValueError('Too many attempts made, user is bad and dumb')

    def get_next_action(self):
        attempts = 0
        is_valid = False
        while not is_valid and attempts < 3:
            # TODO: try-catch logic for user inputs that are non-numeric
            print("Choose an action for this turn:")
            for a in list(ValidActions):
                print(f'{a.value}: {a.name}')
            response = int(input('Enter a number>>'))

            if ValidActions.has_value(response):
                is_valid = True
                # Convert the int to an instance of the enum.
                response = ValidActions(response)
            else:
                attempts += 1

        if not is_valid:
            raise ValueError("User is bad and dumb")

        return response


class GhostGame():
    """Primary game object"""

    def help(self):
        with open(self.help_file) as file_obj:
            print(str(file_obj.read()))

    def __init__(self, num_players=2, num_human_players=1, dict_file='dictionary1.txt'):
        # User Options
        self.min_word_length = 3

        # Primary Variables
        self.s = ''
        self.i_current_player = 0
        self.players = self.init_players(num_players, num_human_players)
        self.num_alive_players = len(self.players)

        # Resources
        self.dict_file = dict_file
        self.dict_url = "https://github.com/dwyl/english-words/raw/master/words_alpha.txt"
        self.help_file = 'README.md'

        # Download the dictionary text file, if it doesn't already exist on disk
        self.download_dictionary_file()

        self.dict_string = self.get_dict_string()
        self.word_list = self.dict_string.splitlines()
        self.word_set = self.build_word_set()

    def get_current_player(self):
        return self.players[self.i_current_player]

    def get_last_player(self):
        if self.i_current_player == 0:
            return self.players[-1]
        else:
            return self.players[self.i_current_player - 1]

    def init_players(self, num_players, num_human_players):
        players = []
        for i in range(0, num_players):
            if i < num_human_players:
                players.append(HumanPlayer)
            else:
                players.append(Player)
            # Connect event handler
            dispatcher.connect(signal=dispatcher.Any, receiver=self.handle_player_state_change, sender=players[i])
        return players

    def next_player(self):
        if self.i_current_player == len(self.players) - 1:
            self.i_current_player = 0
        else:
            self.i_current_player += 1

    def download_dictionary_file(self):
        dict_file_path = Path(self.dict_file)
        word_set = set()
        if not dict_file_path.is_file():
            print('Downloading file...')
            # TODO: Add error handling for failed URL requests
            urllib.request.urlretrieve(self.dict_url, dict_file_path)

    def get_dict_string(self):
        """Read the dictionary text file in as a single string for regexing"""
        with open(self.dict_file) as file_obj:
            return str(file_obj.read())

    def build_word_set(self):
        """Build a set of all words in the dictionary file"""
        with open(self.dict_file, 'r') as file_obj:
            word_set = set()
            for line in file_obj:
                word_set.add(line.rstrip())
            return word_set

    def check_word(self, test_word):
        """Check if a given test_word is an exact match for an existing dictionary word"""
        return test_word.lower() in self.word_set

    def check_possible_word(self, test_word):
        """Check if a test word is on it's way to becoming a possible word"""
        num_letters = len(test_word)
        if num_letters < 3:
            raise ValueError('test_word must be at least 3 characters')

        # Look for a line where this test_word is a substring
        r = re.escape(test_word)
        match = re.search(r, self.dict_string)

        if match is None:
            return False
        else:
            return True

    def print_string(self):
        print(f'Current string = "{self.s}"')
        print('')
        # box_size = min(10,len(self.s))
        # horizontal_line = '-' * box_size
        # print(horizontal_line)
        # word_line = '|' + self.s + ' '*(box_size - len(self.s)) + '|'
        # print(horizontal_line)

    def handle_player_state_change(self, sender):
        """Simple event handler"""
        if sender.player_status == PlayerStatus.Alive:
            self.num_alive_players += 1
        elif sender.player_status == PlayerStatus.Killed:
            self.num_alive_players -= 1
        elif sender.player_status == PlayerStatus.Forfeit:
            self.num_alive_players -= 1
        else:
            raise ValueError(f"Invalid PlayerStatus '{sender.player_status}'")

    def game_over(self):
        # Find the alive player to give them credit
        for p in self.players:
            if p.player_status == PlayerStatus.Alive:
                alive_player = p
                break

        print(f'GAME OVER. PLAYER {alive_player} WINS')
        exit(0)


def main():
    """Contains the gameplay logic"""

    # Instantiate a GhostGame
    gg = GhostGame()

    # Register the event handlers
    # for player in gg.players:
    #     dispatcher.connect(signal=dispatcher.Any, receiver=gg.handle_player_state_change, sender=player)

    # Game loop
    while True:
        # Update the current and previous player
        this_player, last_player = gg.get_current_player(), gg.get_last_player()

        # Print the current working string
        gg.print_string()

        # Prompt the user for what action they want to take this turn
        # TODO - figure out how to call this properly
        print(f'{this_player}\'s turn')
        this_action = this_player.get_next_action(this_player)

        # Take the chosen action
        if this_action == ValidActions.AppendLetter:
            # Get the player's next letter
            next_letter = this_player.get_letter(this_player)

            # Append that letter to the string
            gg.s += next_letter

        elif this_action is ValidActions.Forfeit:
            # Player forfeits
            this_player.forfeit(this_player)
            print(f'Player {gg.i_current_player} forfeits')

        elif this_action == ValidActions.Challenge:
            # Challenge the previous player
            if gg.check_possible_word(gg.s):
                # It's possible for the previous player to construct a valid word.
                # Ask the previous player to type the word they're thinking of
                last_players_word = last_player.challenge(last_player)

                if gg.check_word(last_players_word):
                    # The word last_player provided IS in the dictionary, so they're safe.
                    # this_player made an erroneous challenge, so they die
                    this_player.die(this_player)
                else:
                    # last_player didn't provide a valid word, so they fail the challenge.
                    last_player.die(last_player)
            else:
                # The current string can't possibly be made into a word, so last_player loses
                last_player.die(last_player)

        # Check whether the end-game condition is satisfied
        if gg.num_alive_players < 2 or (len(gg.s) > gg.min_word_length and gg.check_word(gg.s)):
            gg.game_over()

        # Move to the next player's turn
        gg.next_player()


if __name__ == '__main__':
    main()
