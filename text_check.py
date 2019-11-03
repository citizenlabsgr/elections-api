import sys

def check_repeated(text):
    # remove punctuation from the string
    no_punct = ""
    for char in text:
        if char not in '''!()-[]{};:'"\,<>./?@#$%^&*_~''':
            no_punct = no_punct + char

    # display the unpunctuated string
    print(no_punct)

    list_of_words = no_punct.split()
    repeated_list = []

    for index, word in enumerate(list_of_words):
        for other_index in range(index + 1, len(list_of_words)):
            if(word == list_of_words[other_index]):
                repeated_list.append(((index, word), (other_index, list_of_words[other_index])))


    return repeated_list

if __name__ == "__main__":
    print( check_repeated(sys.argv[1]))

"""
    initial_index = None
    consecutive_count = 0

    for index, repeated_tuple in enumerate(repeated_list):
        if(initial_index == None):
            initial_index = (index,repeated_tupe[0][0])
            count += 1
        elif (len(repeated_list) > index + 1 and repeated[0][0] + 1 == repeated_list[index + 1][0][0]):
            #TODO: check if the value of the next index would equals the value of the second pair for the tuple
"""

