import sys

def check_repeated(text):
    # remove punctuation from the string
    no_punct = ""
    for char in text:
        if char not in '''!()-[]{};:'"\,<>./?@#$%^&*_~''':
            no_punct = no_punct + char


    list_of_words = no_punct.split()
    repeated_list = []

    # Finds all repeated words
    for index, word in enumerate(list_of_words):
        for other_index in range(index + 1, len(list_of_words)):
            if(word == list_of_words[other_index]):
                repeated_list.append(((index, word), (other_index, list_of_words[other_index])))
                break


    initial_tuple = None
    consecutive_count = 0

    #checks if its trully repeated
    for index, repeated_tuple in enumerate(repeated_list):
        if(initial_tuple == None):
            initial_tuple = repeated_tuple 
            consecutive_count += 1
        elif (len(repeated_list) > index + 1 and repeated_tuple[0][0] + 1 == repeated_list[index + 1][0][0]):
            consecutive_count += 1
        elif(consecutive_count> 0 and repeated_tuple[0][0] - 1 == repeated_list[index - 1][0][0]): 
            consecutive_count += 1
        elif(initial_tuple[0][0] + consecutive_count == initial_tuple[1][0]):
            print("repeated sentece")
            for index in range(initial_tuple[0][0], initial_tuple[0][0] + consecutive_count + 1):
                print(list_of_words[index])
        else:
            print(repeated_tuple, "nothing here")
            consecutive_count = 0
            initial_tuple = None

    return repeated_list
if __name__ == "__main__":
    print( check_repeated(sys.argv[1]))

