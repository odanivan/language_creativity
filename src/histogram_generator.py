import argparse
import csv
import requests
import sys
import pathlib
import pandas

# The possible creativity scores to create histogram data for
creativity_scores = [
    "WORD_NOVELTY", "CONTEXT_NOVELTY", "PARTICIPANT_SIMILARITY",
    "SENTENCE_SIMILARITY", "RHYTHMIC_SCORE", "PHONETIC_SCORE", "TOTAL_SCORE"
]

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="create histogram data for language creativity scores",
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(
            prog, max_help_position=120, width=99999))

    parser.add_argument("-i",
                        "--input_file",
                        metavar="INPUT_FILE",
                        help="the input file (e.g., data/de_scores.csv)",
                        action="store",
                        type=str,
                        required=True,
                        dest="input_file")
    parser.add_argument("-o",
                        "--output",
                        metavar="OUTPUT_FILE",
                        help="the output file (e.g., data/de_histogram.csv)",
                        action="store",
                        type=str,
                        required=True,
                        dest="output_file")
    parser.add_argument("-c",
                        "--creativity_score",
                        metavar="CREATIVITY_SCORE",
                        help="the creativity score (e.g., RHYTHMIC_SCORE)",
                        action="store",
                        type=str,
                        required=True,
                        choices=creativity_scores,
                        dest="creativity_score")

    arguments = parser.parse_args()

    # Read the input file into a data frame
    data = pandas.read_csv(pathlib.Path(arguments.input_file).resolve(),
                           header=0)

    # Stores the relevant column (the one containing the ratings of all participants in the specified
    # creativity score category, i.e. WORD_NOVELTY)
    scores_by_category = data[arguments.creativity_score].tolist()

    # Count how often a possible score rating has been given to a participant for all possible
    # score classes (from 0 to 20)
    score_classes = []
    for i in range(0, 21):
        # Initialize score_classes with 0
        score_classes.append(0)

    for c in scores_by_category:
        # For each score c that a participant received, count up the respective score class: aka histogram data
        score_classes[c] += 1

    with open(arguments.output_file, mode='w') as wn_file:
        csv_writer = csv.writer(wn_file, delimiter=',')

        for i in range(0, 21):
            csv_writer.writerow([str(i), str(score_classes[i])])
