from fuzzywuzzy import process


def get_best_match(master_list, query_item):
    best_match, score = process.extractOne(query_item, master_list)
    return best_match, score
