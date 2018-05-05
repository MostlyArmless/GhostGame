import urllib.request
from pathlib import Path
import re
from string import ascii_letters as alphabet
import random
from randomdict import RandomDict
from enum import Enum

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


class Player():
    """AI player by default."""

    def __init__(self,name=None):
        self.player_type = player_type
        self.player_status = PlayerStatus.alive
        self.__ai_names = ['Alouiciousness','Bobert','Cornelius','Danwise']
        
        if name is None:
            self.name = random.choice(self.__ai_names)
        else:
            self.name = name

    def forfeit(self):
        self.player_status = PlayerStatus.forfeit


    def die(self):
        self.player_status = PlayerStatus.Killed
        self.num_alive_players -= 1


    def revive(self):
        self.player_status = PlayerStatus.Alive


    def get_next_action(self):
        # The AI will always attempt to append a letter
       return ValidActions.AppendLetter


    def get_letter(self):
        # Randomly select a letter from the alphabet
        return random.choice(alphabet)


    def validate_letter(self, l):
        # Letter must be in [a-z]
        if len(l) != 1:
            return False

        match = re.match(r"[a-zA-Z]",l)
        if match is None:
            return False
        else:
            return True


class HumanPlayer(Player):
    """Overrides the necessary methods of Player class to allow for human interaction"""
    def __init__(self):
        super()

    def get_letter(self):
        
        attempts = 0
        while attempts < 3:
            response = input('Enter a letter>>')
            if self.validate_letter(response):
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
            else:
                attempts += 1

        if not is_valid:
            raise ValueError("User is bad and dumb")


class GhostGame():
    """Tracks the game state"""

    def help(self):
        with open(self.help_file) as file_obj:
            print(str(file_obj.read()))

    def __init__(self,num_players=2,num_human_players=1,dict_file='dictionary1.txt'):
        self.s = ''
        self.i_current_player = 0
        self.players = self.init_players(num_players,num_human_players)
        self.num_alive_players = len(players)
        
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


    def init_players(self,num_players,num_human_players):
        players = []
        for i in range(0,num_players+1):
            if i < num_human_players:
                players.append(HumanPlayer)
            else:
                players.append(Player)

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
            urllib.request.urlretrieve(self.dict_url,dict_file_path)


    def get_dict_string(self):
        """Read the dictionary text file in as a single string for regexing"""
        with open(self.dict_file) as file_obj:
            return str(file_obj.read())


    def build_word_set(self):
        """Build a set of all words in the dictionary file"""
        with open(self.dict_file,'r') as file_obj:
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
        # box_size = min(10,len(self.s))
        # horizontal_line = '-' * box_size
        # print(horizontal_line)
        # word_line = '|' + self.s + ' '*(box_size - len(self.s)) + '|'
        # print(horizontal_line)       


def main():
    """Contains the gameplay logic"""

    # Instantiate a GhostGame
    gg = GhostGame()

    # Game loop
    while True:
        # Update the current and previous player
        this_player, last_player = gg.get_current_player(), gg.get_last_player()

        # Print the current working string
        gg.print_string()

        # Prompt the user for what action they want to take this turn
        #TODO - figure out how to call this properly
        this_action = this_player.get_next_action(this_player)
        print(f'this_action = {this_action}')

        # Take the chosen action
        if this_action == ValidActions.AppendLetter:
            # Get the player's next letter
            next_letter = this_player.get_letter()

            # Append that letter to the string
            gg.s += next_letter

        elif this_action == ValidActions.Forfeit:
            # Player forfeits
            this_player.forfeit()
            print(f'{this_player.name} forfeits')

        elif this_action == ValidActions.Challenge:
            # Challenge the previous player
            if gg.check_possible_word(gg.s):
                # It's possible for the previous player to construct a valid word.
                # Ask the previous player to type the word they're thinking of
                last_players_word = last_player.challenge()

                if gg.check_word(last_players_word):
                    # The word last_player provided IS in the dictionary, so they're safe.
                    # this_player made an erroneous challenge, so they die
                    this_player.die()
                else:
                    # last_player didn't provide a valid word, so they fail the challenge.
                    last_player.die()
            else:
                # The current string can't possibly be made into a word, so last_player loses
                last_player.die()

        # Check whether the end-game condition is satisfied
        if self.num_alive_players == 0 or gg.check_word(gg.s):
            gg.game_over()
        
        # Move to the next player's turn
        gg.next_player()

        if gg.check_word(gg.s + next_letter):
            print(f'Player {this_player.name} loses! They made the word "{s_test}"')
            gg.reset()
        else:
            # Append the letter
            gg.s += next_letter



if __name__ == '__main__':
    main()
    # gg = GhostGame()
    # gg.s = 'stuff'
    # gg.print_string()


