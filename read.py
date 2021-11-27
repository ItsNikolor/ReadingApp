import re
import fitz


def read(filename):
    if not filename:
        return []

    if filename.split('.')[-1] == 'pdf':
        with fitz.open(filename) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
    else:
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
    text = re.sub('[^\w!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]+', ' ', text)
    return text.split()
