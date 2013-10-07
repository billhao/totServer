import string
import random

def rnd_str_generator(size=8, chars=string.ascii_uppercase+string.digits):
    return ''.join( random.choice(chars) for x in range(size) )
