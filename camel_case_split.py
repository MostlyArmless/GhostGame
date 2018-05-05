import string

def camel_case_split(s, split_char=' '):
	"""Given a string s written in camelCase, this function
	splits the string either into separate words or
	with_underscores_and_lowercased"""

	out = ''
	for c, i in s:
		print(i)
		if c.isupper():
			# Start of new word
			out += split_char
		
		out += c.lower()
	print(out)
	return out

assert camel_case_split('camelCase') == 'camel case'
assert camel_case_split('StartsWithCapital') == 'starts with capital'
print(camel_case_split('badCAmel'))
assert camel_case_split('two words') == 'camel case'