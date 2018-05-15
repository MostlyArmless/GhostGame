import urllib.request
from pathlib import Path
import re
from string import ascii_letters as alphabet
import random
from randomdict import RandomDict
from enum import Enum
from pydispatch import dispatcher
from math import ceil

valid_chars = alphabet + '?!'


def fileread(filename):
    """Read a text file and return all contents as a string"""
    with open(filename) as file_obj:
        return str(file_obj.read())


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
    player_name = None

    def __init__(self, name=None):
        __ai_player_names = ['Alice', 'Bob', 'Chuck', 'Dick', 'Ester', 'Francine']
        if name is None:
            self.player_name = random.choice(__ai_player_names)
        else:
            self.player_name = name
        self.target_word = ''

    def challenge(self, gg):
        """Respond to challenge issued by another player by returning the word this player is thinking of"""
        candidates = gg.get_target_word()

        if candidates is not None:
            return random.choice(candidates)
        else:
            return None

    def forfeit(self):
        self.player_status = PlayerStatus.Forfeit
        dispatcher.send(signal=PlayerStatus.Forfeit, sender=self)

    def die(self):
        self.player_status = PlayerStatus.Killed
        dispatcher.send(signal=PlayerStatus.Killed, sender=self)

    def revive(self):
        self.player_status = PlayerStatus.Alive
        dispatcher.send(signal=PlayerStatus.Alive, sender=self)

    def get_next_action(self, gg):
        """Choose the AI player's next move"""
        # Check whether the last player added a letter that can't possibly be turned into a word, and challenge them
        if not gg.check_possible_word(gg.s):
            # Challenge the previous player
            return '?'

        # Check whether the previous target word is still possible after the last round of added letters
        if gg.s != self.target_word[0:len(gg.s)-1]:
            self.target_word = gg.get_target_word()
            if self.target_word is None:
                # There are no more words we can work towards. Admit defeat.
                return '!'

        print(f'Player "{self.player_name}" target_word = "{self.target_word}"')
        next_letter = self.target_word[len(gg.s)]
        return next_letter


class HumanPlayer(Player):
    """Overrides the necessary methods of Player class to allow for human interaction"""

    def __init__(self, name=None):

        __human_player_names = ['Mike', 'Jane']

        if name is None:
            self.player_name = random.choice(__human_player_names)
        else:
            self.player_name = name

    def challenge(self, gg):
        # Challenge the human player to provide any possible word that could start with the current string
        print(f'{self.player_name}: you\'ve been challenged.')
        is_valid = False
        while not is_valid:
            response = input(f'Enter a word that starts with "{gg.s}">>')
            is_valid = response.isalpha()

    def get_next_action(self, gg):
        attempts = 0
        is_valid = False
        while not is_valid and attempts < 3:
            response = input(f"{self.player_name}: \"{gg.s}\">>")

            if response in valid_chars:
                return response.lower()
            else:
                attempts += 1

        if not is_valid:
            raise ValueError("User failed to select a valid option.")


class GhostGame:
    """Primary game object"""

    def help(self):
        with open(self.help_file) as file_obj:
            print(str(file_obj.read()))

    def __init__(self, num_players=2, num_human_players=1, dict_file='20k_word_freq_dict.txt'):
        # User Options
        self.min_word_length = 3

        # Primary Variables
        self.s = ''
        self.i_current_player = 0
        self.players = self.init_players(num_players, num_human_players)
        self.num_alive_players = len(self.players)

        # Resources
        self.dict_file = dict_file
        self.dictionaries = {'test_dictionary.txt': 'test_dictionary.txt',
                             'simple_dict.txt': 'https://github.com/dwyl/english-words/raw/master/words_alpha.txt',
                             '20k_word_freq_dict.txt': 'https://raw.githubusercontent.com/first20hours/google-10000-english/master/20k.txt'}
        self.help_file = 'README.md'
        self.custom_dict = 'custom_dictionary.txt'

        # Download the dictionary text file, if it doesn't already exist on disk
        self.download_dictionary_file()

        # Concatenate the custom and standard dictionaries
        self.dict_string = fileread(self.custom_dict) + fileread(self.dict_file)
        self.word_set = self.build_word_set()

        self.print_game_start_message()

    def remove_word(self, word):
        """Removes a given word from both the dict_string and word_set. Presumes that the word has already been
        confirmed to exist in both."""

        # Remove word from set
        self.word_set.discard(word)

        # Remove the word from dict_string
        result = re.search(word, self.dict_string)
        self.dict_string = self.dict_string[0:result.start() - 1] + self.dict_string[result.end():-1]

    def get_target_word(self):
        """Return a possible word that the AI player could work towards, which both contains the current string and
        won't result in this player losing"""

        # Find all possible words that contain the current string
        words_found = []
        i = 0
        # TODO: introduce the notion of game difficulty levels by restricting the number of candidate words
        for match in re.finditer(r'^' + self.s + r'.*', self.dict_string, flags=re.MULTILINE):
            if len(match.group()) >= self.min_word_length:
                words_found.append(match.group())
            # i += 1
            # if i >= num_candidates:
            #     break

        if not words_found:
            return None

        # Filter the list of words by those that will result in this player winning
        safe_length_words = []
        for word in words_found:
            # Isolate the part of the word AFTER the current working string to determine if it'll cause us to lose
            if self.is_safe_length(word):
                # This word WON'T cause the current player to lose. add it to the list of winning words
                safe_length_words.append(word)

        if not safe_length_words:
            # There are possible words, but none of them are a safe length.
            # The best strategy now is to target the longest possible word and hope another player makes a mistake
            return max(words_found, key=len)

        # Now we need to eliminate any words that are of a safe length but which start with another word that exists
        # e.g. "apples" might be a safe word in terms of length, but it starts with "app" which may not be a safe length
        winning_words = []
        for word in safe_length_words:
            # Make each possible sub-word, check if it exists, and then check if it's a safe length
            is_safe = True
            # Initialize it as the shortest legal subword
            sub_word = word[0:self.min_word_length-1]
            if len(word) > self.min_word_length:
                # Word is long enough that it might have unsafe subwords
                for c in word[self.min_word_length-1:]:
                    sub_word = sub_word + c
                    if self.check_word(sub_word) and not self.is_safe_length(sub_word):
                        # This safe word contains a sub_word which is not safe. Reject it
                        is_safe = False
                        break
            if is_safe:
                winning_words.append(word)

        if not winning_words:
            # No remaining possible words will let us win, but we can try and hope someone else makes a mistake
            return random.choice(safe_length_words)

        # Choose a random word from the top of the list
        threshold = ceil(len(winning_words)/20)
        return random.choice(winning_words[0:threshold])

    def is_safe_length(self, word):
        """Returns true if a given word will not kill the current player,
        based on their position in the turn order and the word's length"""
        rest_of_word = word[len(self.s):]
        return len(rest_of_word) % self.num_alive_players != self.i_current_player

    def print_game_start_message(self):
        print(f'Starting game with {self.num_alive_players} players:')
        i = 1
        for p in self.players:
            if isinstance(p, HumanPlayer):
                player_type = 'Human'
            else:
                player_type = 'AI'
            print(f'Player {i}: {p.player_name} ({player_type})')
            i += 1

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
                players.append(HumanPlayer())
            else:
                players.append(Player())
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
        if not dict_file_path.is_file():
            print(f'Downloading file from {self.dictionaries[self.dict_file]}...')
            # TODO: Add error handling for failed URL requests
            urllib.request.urlretrieve(self.dictionaries[self.dict_file], dict_file_path)

    def build_word_set(self):
        """Build a set of all words in the dict_string"""
        return set(self.dict_string.split('\n'))

    def check_word(self, test_word):
        """Check if a given test_word is an exact match for an existing dictionary word"""
        if test_word is None:
            return False
        return test_word.lower() in self.word_set

    def check_possible_word(self, test_word):
        """Check if a test word is on it's way to becoming a possible word"""
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
        if isinstance(alive_player, HumanPlayer):
            player_type = 'Human'
        else:
            player_type = 'AI'

        print(f'GAME OVER. PLAYER {alive_player.player_name} ({player_type}) WINS')
        exit(0)


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
        print(f'{this_player.player_name}\'s turn')
        this_action = this_player.get_next_action(gg)

        # Take the chosen action
        if this_action in alphabet:
            # Append the letter to the string
            gg.s += this_action

        elif this_action == "!":
            # Player forfeits
            this_player.forfeit()
            print(f'Player {gg.i_current_player} forfeits')

        elif this_action == "?":
            # Ask the previous player to reveal the word they're thinking of
            last_players_word = last_player.challenge(gg)
            if gg.check_word(last_players_word):
                # The word last_player provided IS in the dictionary, so they're safe.
                # this_player made an erroneous challenge, so they die
                if not isinstance(last_player,HumanPlayer):
                    # Tell the human players what word the AI was thinking of
                    print(f'{last_player.player_name} has passed the challenge!')
                    print(f'The word they were thinking of was "{last_players_word}"')
                    print(f'{this_player.player_name} dies!')

                this_player.die()
            else:
                # last_player didn't provide a valid word, so they fail the challenge.
                last_player.die()

        # Check whether the end-game condition is satisfied
        this_player_formed_a_word = (len(gg.s) >= gg.min_word_length and gg.check_word(gg.s))
        if this_player_formed_a_word:
            this_player.die()
            print(f'{this_player.player_name} spelled a word: "{gg.s}".')

        if gg.num_alive_players < 2:
            gg.game_over()
        elif this_player_formed_a_word:
            # Remove this word from the dictionary so the remaining players can continue playing
            gg.remove_word(gg.s)

        # Move to the next player's turn
        gg.next_player()


if __name__ == '__main__':
    main()
