from enum import Enum
from itertools import tee

import argparse
import csv
import pathlib
import requests
import sys
import cologne_phonetics
import phonetics
import pylcs
import termcolor

# Define WORD_NOVELTY API endpoints
WORD_NOVELTY_API_DE = "http://api.corpora.uni-leipzig.de/ws/words/deu_news_2012_1M/word/"
WORD_NOVELTY_API_EN = "http://api.corpora.uni-leipzig.de/ws/words/eng_news_2013_3M/word/"

# TODO: To use the CONTEXT_NOVELTY score, replace `827FF4DDC28347C1A13FA45DA7289CE9` with a valid API key from `https://www.scaleserp.com/`
SCALESERP_API_KEY = "827FF4DDC28347C1A13FA45DA7289CE9"


# Define CONTEXT_NOVELTY API endpoints
def CONTEXT_NOVELTY_API_DE(q):
    return "https://api.scaleserp.com/search?api_key=%s&q=%s&google_domain=google.de&location=Germany&gl=de&hl=de&page=1&output=json" % (
        SCALESERP_API_KEY, q)


def CONTEXT_NOVELTY_API_EN(q):
    return "https://api.scaleserp.com/search?api_key=%s&q=%s&google_domain=google.com&location=United+States&gl=us&hl=en&page=1&output=json" % (
        SCALESERP_API_KEY, q)


# Define creativity scores
class Scores(Enum):
    WORD_NOVELTY = 1
    CONTEXT_NOVELTY = 2
    PARTICIPANT_SIMILARITY = 3
    SENTENCE_SIMILARITY = 4
    RHYTHMIC_SCORE = 5
    PHONETIC_SCORE = 6
    TOTAL_SCORE = 7


score_color_map = {
    Scores.WORD_NOVELTY: "yellow",
    Scores.CONTEXT_NOVELTY: "yellow",
    Scores.PARTICIPANT_SIMILARITY: "yellow",
    Scores.SENTENCE_SIMILARITY: "yellow",
    Scores.RHYTHMIC_SCORE: "cyan",
    Scores.PHONETIC_SCORE: "cyan",
    Scores.TOTAL_SCORE: "red"
}


def pairwise(iterable):
    f, s = tee(iterable)
    next(s, None)

    return zip(f, s)


def novelty_class(num_results: int, num_classes: int, upper_bound: int):
    while (num_results > upper_bound and num_classes > 1):
        upper_bound *= 2
        num_classes -= 1

    return num_classes


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="measure language creativity with phonetic analysis",
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(
            prog, max_help_position=120, width=99999))

    parser.add_argument("-i",
                        "--input_file",
                        metavar="INPUT_FILE",
                        help="the input file (e.gw., data/de_sentences.csv)",
                        action="store",
                        type=str,
                        required=True,
                        dest="input_file")
    parser.add_argument("-o",
                        "--output_file",
                        metavar="OUTPUT_FILE",
                        help="the output file (e.g., data/de_scores.csv)",
                        action="store",
                        type=str,
                        default=None,
                        dest="output_file")
    parser.add_argument(
        "-s",
        "--creativity_scores",
        metavar="CREATIVITY_SCORES",
        help=
        "the creativity scores with weightings (e.g., WORD_NOVELTY:0.6,CONTEXT_NOVELTY:0.4)",
        action="store",
        type=str,
        default=None,
        dest="creativity_scores")
    parser.add_argument("-l",
                        "--language",
                        metavar="LANGUAGE",
                        help="the language (e.g., DE)",
                        action="store",
                        type=str,
                        default="DE",
                        dest="language")

    arguments = parser.parse_args()

    # Create default creativity score weightings
    # first := weighting factor of individual to total score [0, 1]
    # second := is handled as bonus point {True, False}
    score_weight_map = {
        Scores.WORD_NOVELTY: (0.4, False),
        Scores.CONTEXT_NOVELTY: (0.4, False),
        Scores.PARTICIPANT_SIMILARITY: (0.1, False),
        Scores.SENTENCE_SIMILARITY: (0.1, False),
        Scores.RHYTHMIC_SCORE: (0.1, True),
        Scores.PHONETIC_SCORE: (0.1, True)
    }

    # Set adjusted creativity score weightings if the user specified custom score weightings via command line interface
    if arguments.creativity_scores:
        scores_and_weights = set(
            filter(None, arguments.creativity_scores.split(",")))

        score_weight_map = {}

        for scores_and_weight in scores_and_weights:
            score, weight = scores_and_weight.split(":")

            is_bonus = weight.startswith("+")
            if is_bonus:
                weight = weight[1:]

            score_weight_map[Scores[score]] = (float(weight), is_bonus)

    # Read input file containing subjects (anonymous participant id), variables (given four letter word),
    # and sentences (participants "creative" solution)
    lines = csv.reader(open(arguments.input_file, "r"), delimiter=";")
    next(lines)

    samples = {}
    scores = {}

    # Pre-processing step: Check if the participants' sentences are valid solutions
    for line in lines:
        stripped_sentence = line[2].strip(" ,;.:!?").upper().split()

        # 1. Discard sentences that are not of length 4 (meaning sentences that do not contain exactly 4 words)
        if len(stripped_sentence) != 4:
            continue

        # 2. Discard sentences that contain words which do not start with correct letter
        # according to given variable (i.e. EKEL)
        for word in stripped_sentence:
            if word[0] not in line[1]:
                continue

        if line[0] not in samples:
            samples[line[0]] = {}
            scores[line[0]] = {}

        samples[line[0]][line[1]] = line[2]
        scores[line[0]][line[1]] = {}

    subject_vocabulary = {}
    variable_vocabulary = {}

    for subject, pairs in samples.items():
        if subject not in subject_vocabulary:
            subject_vocabulary[subject] = {}

        for variable, sentence in pairs.items():

            if variable not in variable_vocabulary:
                variable_vocabulary[variable] = {}

            for word in sentence.strip(" ,;.:!?").lower().split():
                if word not in subject_vocabulary[subject]:
                    subject_vocabulary[subject][word] = 1
                else:
                    subject_vocabulary[subject][word] += 1

                if word not in variable_vocabulary[variable]:
                    variable_vocabulary[variable][word] = 1
                else:
                    variable_vocabulary[variable][word] += 1

    # Calculate relative occurrences of words per variable or subject
    for subject, pairs in subject_vocabulary.items():
        for word, count in pairs.items():
            subject_vocabulary[subject][word] /= len(
                subject_vocabulary[subject])

    for variable, pairs in variable_vocabulary.items():
        for word, count in pairs.items():
            variable_vocabulary[variable][word] /= len(
                variable_vocabulary[variable])

    max_subject_occurence = 0.0
    min_subject_occurence = 1.0
    for subject in subject_vocabulary.values():

        if max(subject.values()) > max_subject_occurence:
            max_subject_occurence = max(subject.values())

        if min(subject.values()) < min_subject_occurence:
            min_subject_occurence = min(subject.values())

    max_variable_occurence = 0.0
    min_variable_occurence = 1.0
    for variable in variable_vocabulary.values():

        if max(variable.values()) > max_variable_occurence:
            max_variable_occurence = max(variable.values())

        if min(variable.values()) < min_variable_occurence:
            min_variable_occurence = min(variable.values())

    # Determine creativity scores for all subjects and their variables
    for subject_index, (subject, pairs) in enumerate(samples.items()):

        for variable_index, (variable, sentence) in enumerate(pairs.items()):

            # Eliminate special characters in the beginning or end
            stripped_sentence = sentence.strip(" ,;.:!?").lower().split()

            # Determine the WORD_NOVELTY score
            if Scores.WORD_NOVELTY in score_weight_map:
                score = 0

                # Set desired WORD_NOVELTY API (default is DE)
                word_novelty_api = WORD_NOVELTY_API_DE
                if arguments.language == "EN":
                    word_novelty_api = WORD_NOVELTY_API_EN

                # Determine the novelty of each word
                for word in stripped_sentence:
                    lower_word = word.lower()
                    lower_score = sys.maxsize
                    lower_resp = requests.get(word_novelty_api + lower_word)

                    # Process only successful request responses
                    if lower_resp.status_code == 200:
                        # The response from api.corpora.uni-leipzig.de contains the key `frequencyClass`
                        # which classifies words based on how frequently they are used in the corpus
                        lower_score = min(
                            20,
                            lower_resp.json()["frequencyClass"] + 1)

                    upper_word = lower_word.capitalize()
                    upper_score = sys.maxsize
                    upper_resp = requests.get(word_novelty_api + upper_word)

                    if upper_resp.status_code == 200:
                        upper_score = min(
                            20,
                            upper_resp.json()["frequencyClass"] + 1)

                    # Use the minimum score of both lowered and capitalized word
                    word_score = min(lower_score, upper_score)

                    if word_score != sys.maxsize:
                        score += word_score

                # Calculate the arithmetic mean over all individual word frequency scores
                scores[subject][variable][Scores.WORD_NOVELTY] = int(
                    round(score / 4))

            # Determine the CONTEXT_NOVELTY score
            if Scores.CONTEXT_NOVELTY in score_weight_map:
                score = 0

                # Set desired CONTEXT_NOVELTY API (default is DE)
                context_novelty_api = CONTEXT_NOVELTY_API_DE
                if arguments.language == "EN":
                    context_novelty_api = CONTEXT_NOVELTY_API_EN

                # Iterate over all possible pairs of words in the sentence
                for first, second in pairwise(stripped_sentence):
                    try:
                        # Obtain the CONTEXT_NOVELTY from the scaleserp.com endpoint
                        resp = requests.get(
                            context_novelty_api("\"%s + %s\"" %
                                                (first, second)))

                        # Process only successful request responses
                        if resp.status_code == 200:
                            response_json = resp.json()

                            # Determine the novelty score in the nested JSON response
                            # There are two preconditions for successful respones:
                            # 1) response_json["request_info"]["success"] == True
                            # 2) response_json["search_information"]["total_results"] != None
                            if response_json["request_info"][
                                    "success"] == True:
                                if "total_results" in response_json[
                                        "search_information"]:
                                    # Map the number of google search results N to a score in [0, 20]
                                    # < 512 search results implies the best score of 20
                                    score += novelty_class(
                                        int(response_json["search_information"]
                                            ["total_results"]), 20, 512)
                                else:
                                    # If there are 0 search results, the word is highly novel
                                    score += 20
                    except Exception:
                        continue

                # Perform the same CONTEXT_NOVELTY calculation for word pairs that do not appear consecutively
                for indices in [[0, 2], [0, 3], [1, 3]]:
                    try:
                        resp = requests.get(
                            context_novelty_api(
                                "\"%s * %s\"" %
                                (stripped_sentence[indices[0]],
                                 stripped_sentence[indices[1]])))

                        if resp.status_code == 200:
                            response_json = resp.json()

                            if response_json["request_info"][
                                    "success"] == True:
                                if "total_results" in response_json[
                                        "search_information"]:
                                    score += novelty_class(
                                        int(response_json["search_information"]
                                            ["total_results"]), 20, 512)
                                else:
                                    score += 20
                    except Exception:
                        continue

                # Calculate the arithmetic mean over all individual word frequency scores
                scores[subject][variable][Scores.CONTEXT_NOVELTY] = int(
                    round(score / 6))

            # Determine the PARTICIPANT_SIMILARITY score
            if Scores.PARTICIPANT_SIMILARITY in score_weight_map:
                score = 0
                # Score is calculated based on how often the participant (subject) has used the same word
                # These relative occurences of words per participant are given in the subject_vocabulary dictionary
                for word in stripped_sentence:
                    score += subject_vocabulary[subject][word]

                # Calculate average score over all 4 words of a sentence, taking the minimum and maximum occurence
                # across all participants into account
                score = 1 - ((score/4) - min_subject_occurence) / \
                    max(1, (max_subject_occurence - min_subject_occurence))
                scores[subject][variable][Scores.PARTICIPANT_SIMILARITY] = int(
                    round(score * 20))

            # Determine the SENTENCE_SIMILARITY score
            if Scores.SENTENCE_SIMILARITY in score_weight_map:
                score = 0
                # Score is calculated based on how often other participants have used the same word as a solution
                # to this specific four-letter word puzzle (variable)
                # These relative occurences of words per variable are given in the variable_vocabulary dictionary
                for word in stripped_sentence:
                    score += variable_vocabulary[variable][word]

                # Calculate average score over all 4 words of a sentence, taking the minimum and maximum occurence
                # across all sentences of a variable into account
                score = 1 - ((score / 4) - min_variable_occurence) / \
                    max(1, (max_variable_occurence - min_variable_occurence))
                scores[subject][variable][Scores.SENTENCE_SIMILARITY] = int(
                    round(score * 20))

            # Determine RHYTHMIC_SCORE
            if Scores.RHYTHMIC_SCORE in score_weight_map:
                score = 0

                phonetic_result = []
                # Eliminate all special characters on the left and right sides
                stripped_sentence = sentence.strip(" ,;.:!?").lower()

                # Compute the phonetic word representations
                if arguments.language == "DE":
                    # In German based on `cologne_phonetics`
                    # `encode` allows for passing the entire sentence
                    phonetic_result = cologne_phonetics.encode(
                        stripped_sentence)
                elif arguments.language == "EN":
                    # In German based on `phonetics`
                    # `soundex` accepts only one word per call
                    for word in stripped_sentence.split(" "):
                        phonetic_result.append((word, phonetics.soundex(word)))

                sounds_to_word_groups = {}

                # Iterate over all phonetic word representations in pairs
                for i in range(len(phonetic_result)):
                    for j in range(i + 1, len(phonetic_result)):
                        (word1, sound1) = phonetic_result[i]
                        (word2, sound2) = phonetic_result[j]

                        # Iterate over all characters in the shorter phonetic word representation
                        for x in range(1, 1 + min(len(sound1), len(sound2))):

                            # Consider identical sounds as rhymes but ignore identical words
                            if ((sound1[-x:] == sound2[-x:])
                                    and not (word1 == word2)):

                                adj_word1 = word1
                                adj_word2 = word2

                                # For German, use d/t and s/z interchangeably
                                if x > 1 and arguments.language == "DE":
                                    if (adj_word1[-1:] == 'd'):
                                        adj_word1 = adj_word1[:-1] + 't'
                                    if (adj_word1[-1:] == 's'):
                                        adj_word1 = adj_word1[:-1] + 'z'

                                    if (adj_word2[-1:] == 'd'):
                                        adj_word2 = adj_word2[:-1] + 't'
                                    if (adj_word2[-1:] == 's'):
                                        adj_word2 = adj_word2[:-1] + 'z'

                                # Go to the next word representation if the next considered sound differs
                                if not adj_word1[-(x + 1):] == adj_word2[-(
                                        x + 1):]:
                                    continue

                                # Initialize word group if the sound is encountered for the first time
                                if sound1[-x:] not in sounds_to_word_groups:
                                    sounds_to_word_groups[sound1[-x:]] = set()

                                # Update the sound-to-word-group mapping
                                # sounds_to_word_groups maps a repeating sound to all the words that contain the sound
                                sounds_to_word_groups[sound1[-x:]].add(word1)
                                sounds_to_word_groups[sound1[-x:]].add(word2)
                            else:
                                break

                word_groups_to_sounds = {}

                # Freeze the word groups to make them hash-able and therefore usable as keys in the
                # inverted map from word group --> sound
                for sound, word_group in sounds_to_word_groups.items():
                    sounds_to_word_groups[sound] = frozenset(word_group)

                # Build inverted map from word group --> sound
                # For every word group, choose the longest common sound
                for sound, word_group in sounds_to_word_groups.items():
                    if (not word_group
                            in word_groups_to_sounds) or len(sound) > len(
                                word_groups_to_sounds[word_group]):
                        word_groups_to_sounds[word_group] = sound

                # Map the word groups' sounds to a discrete scale from 0 to 20
                # For each found rhyme, the score consists of two parts:
                # 1) the length of the rhyme (similar to the number of syllables of a rhyme),
                # and 2) the number of words that rhyme
                for word_group, sound in word_groups_to_sounds.items():
                    rhyme_length = len(sound)
                    score += min(20, (rhyme_length * 5) - 5)
                    num_words_in_rhyme = len(word_group)
                    score += min(20, (num_words_in_rhyme - 1) * 5)

                score = min(20, score)

                scores[subject][variable][Scores.RHYTHMIC_SCORE] = int(
                    round(score))

            # Determine PHONETIC_SCORE
            if Scores.PHONETIC_SCORE in score_weight_map:
                score = 0

                total_combinations = 0
                levenstein_score = 0
                substring_score = 0

                # Iterate over the phonetic word representations in pairs
                for i in range(len(phonetic_result)):
                    for j in range(i + 1, len(phonetic_result)):
                        total_combinations += 1

                        (word1, sound1) = phonetic_result[i]
                        (word2, sound2) = phonetic_result[j]

                        # Compute the Levenshtein distance between the two representations
                        levenstein_distance = pylcs.levenshtein_distance(
                            sound1, sound2)
                        # Compute the longest substring between the two representations
                        longest_substr_len = pylcs.lcs2(sound1, sound2)

                        # Normalize the Levenshtein distance score using the lenght of the longer representation
                        levenstein_score += levenstein_distance / max(
                            len(sound1), len(sound2))

                        # Normalize the longest substring score using the lenght of the shorter representation
                        substring_score += longest_substr_len / min(
                            len(sound1), len(sound2))

                # Map both partial phonetic scores to a scale from 0 to 20
                score += 0.5 * ((1 -
                                 (levenstein_score / total_combinations)) * 20)
                score += 0.5 * ((substring_score / total_combinations) * 20)

                scores[subject][variable][Scores.PHONETIC_SCORE] = int(
                    round(score))

            # Determine TOTAL_SCORE
            regular_total_score = 0.0
            bonus_total_score = 0.0

            # Consider all scores and whether they are provide bonus points
            for score, weight_and_bonus in score_weight_map.items():
                weight, is_bonus = weight_and_bonus

                # Accumulate the partial total scores
                if is_bonus:
                    bonus_total_score += weight * scores[subject][variable][
                        score]
                else:
                    regular_total_score += weight * scores[subject][variable][
                        score]

            # Calculate the total score with a maximum of 20
            scores[subject][variable][Scores.TOTAL_SCORE] = min(
                20,
                int(round(regular_total_score)) +
                int(round(bonus_total_score)))

            # Construct the CSV header rows
            plain_header = ""
            colored_header = ""

            # Print the header line in the first iteration, displays the title of each column for the following lines
            if subject_index == 0 and variable_index == 0:
                plain_header = "\"subject\",\"variable\",\"sentence\""
                colored_header = plain_header

                for score in Scores:
                    if score in score_weight_map or score == Scores.TOTAL_SCORE:
                        plain_header += ",\"%s\"" % (score.name)
                        colored_header += ",%s" % (termcolor.colored(
                            "\"%s\"" % (score.name), score_color_map[score]))

                plain_header += "\n"
                colored_header += "\n"

            # Print the score line (in color for the console output)
            plain_output = plain_header + "\"%s\",\"%s\",\"%s\"" % (
                subject, variable, sentence)
            colored_output = colored_header + "\"%s\",\"%s\",\"%s\"" % (
                subject, variable, sentence)

            for score in Scores:
                if score in score_weight_map or score == Scores.TOTAL_SCORE:
                    plain_output += ",%s" % (scores[subject][variable][score])
                    colored_output += ",%s" % (termcolor.colored(
                        scores[subject][variable][score],
                        score_color_map[score]))

            print(colored_output)

            # Optionally, write the results to the output file
            if arguments.output_file:
                output_file = pathlib.Path(arguments.output_file).resolve()

                with output_file.open("a") as f:
                    f.write(plain_output + "\n")
