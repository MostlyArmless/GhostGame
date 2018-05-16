import unittest
from ghost import GhostGame, Player

class FakeGhostGame(GhostGame):
	def __init__(self,*args, **kwargs):
		pass

class TestGhost(unittest.TestCase):
	def setUp(self):
		# Overwrite the normal dictionary file with a shorter one
		self.gg = GhostGame(dict_file='test_dictionary.txt')
		self.p = Player()

	def test_get_dict_string(self):
		actual = self.gg.get_dict_string()
		with open(self.gg.dict_file, 'r') as file_obj:
			expected = file_obj.read()

		self.assertEqual(actual,expected,'file contents not read properly')
	
	def test_check_word(self):
		self.assertTrue(self.gg.is_complete_word('apple'), 'whole word, lowercase')
		self.assertTrue(self.gg.is_complete_word('Apple'), 'whole word, mixed case')
		self.assertFalse(self.gg.is_complete_word('!'), 'non-word')
		self.assertFalse(self.gg.is_complete_word('multi word'), 'multi word')
		self.assertFalse(self.gg.is_complete_word('badWord'), 'word not in dictionary')

	def test_check_possible_word(self):
		self.assertTrue(self.gg.is_possible_word('apple'), 'whole word')
		self.assertTrue(self.gg.is_possible_word('zed'), 'whole word')
		self.assertTrue(self.gg.is_possible_word('perat'), 'middle of word')
		self.assertTrue(self.gg.is_possible_word('xyl'), 'start of word')
		self.assertTrue(self.gg.is_possible_word('cut'), 'end of word')

		with self.assertRaises(ValueError):
			self.gg.is_possible_word('xy')

		# End of one word concatenated with beginning of next word
		self.assertFalse(self.gg.is_possible_word('leban'))


	def test_validate_letter(self):
		self.assertTrue(self.p.validate_letter('a'), 'lowercase letter')
		self.assertTrue(self.p.validate_letter('Z'), 'uppercase letter')
		self.assertFalse(self.p.validate_letter('!'), 'non-letter character')
		self.assertFalse(self.p.validate_letter('aa'), 'two letters')
		self.assertFalse(self.p.validate_letter('0'), 'number')
		self.assertFalse(self.p.validate_letter(''), 'blank')

	

if __name__ == '__main__':
	unittest.main()