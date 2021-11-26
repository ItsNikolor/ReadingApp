import re


def read(filename):
    if not filename:
        return []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [re.sub('[^\w!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]+', ' ', line) for line in f]
    words = [word for line in lines for word in line.split()]
    return words
