import re
import api
from collections import Counter

""" Some of the logic in this file is from http://norvig.com/spell-correct.html """

def words(text):
    return re.findall(r'\w+', text.lower())

WORDS = Counter(words(open('data/big.txt').read()))

def known(words):
    return set(word for word in words if word in WORDS)

def edits(word):
    print("In edits(" + word + ")")
    """ All words one edit away from 'word' """
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:index], word[index:])           for index in range(len(word) + 1)]
    deletes    = [left + right[1:]                       for left, right in splits if right]
    transposes = [left + right[1] + right[0] + right[2:] for left, right in splits if len(right)>1]
    replaces   = [left + letter + right[1:]              for left, right in splits if right for letter in letters]
    inserts    = [left + letter + right                  for left, right in splits for letter in letters]
    return set(deletes + transposes + replaces + inserts)

def check_edits(word):
    all_edits = edits(word)
    potential_edits = [word for word in all_edits if word in WORDS]
    if len(potential_edits) > 0:
        return True
    else:
        return False

def sanitize_and_split_words(text):
    #print("About sanitize and split \"" + text + "\"")
    text_sans_tags = re.sub("(<(((@|#)[^ ]+)|((https?):\/\/[^>]+))>)", "", text.lower())
    text_sans_emoji = re.sub(":[^: ]+:|([0-9]{1,2}(:[0-9]{1,2})?(am|pm))", " ", text_sans_tags)
    text_sans_symbols = re.sub("[^a-z'-]+", " ", text_sans_emoji)
    text_sans_combined_words = re.sub("[a-z]*[_\-']+[a-z]*", " ", text_sans_symbols)
    words = re.split("[ ]+" , text_sans_combined_words.strip())
    #print("Sanitized and split words: ", words)
    return words

def find_unknown_words(words):
    #print("Finding unknown words in: ", words)
    known_words = known(words)
    unknown_words = [word for word in words if (len(word) > 3 and word not in known_words)]
    unknown_words = [word for word in unknown_words if not check_edits(word)]
    #print("Unknown words: ", unknown_words)
    return unknown_words

def check_dictionary(word):
    """ Returns true if word found or false if not """
    response = api.call_dictionary(word)
    match_string = '<def>'
    #print(response.text)
    #print("match_string: " + match_string)
    if match_string in response.text:
    #    print("dictionary definition found for \"%s\"" %word)
        return True
    else:
    #    print("No match found for \"%s\"" %word)
        return False
