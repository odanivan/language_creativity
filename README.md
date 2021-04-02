# Automated Analysis of Language Creativity
- [Neurodesign Lecture -- Artificial Intelligence and the Neuroscience of Creativity, Winter '21](https://hpi.de/studium/im-studium/lehrveranstaltungen/it-systems-engineering-ma/lehrveranstaltung/wise-20-21-3156-neurodesign-lecture-_-artificial-intelligence-and-the-neuroscience-of-creativity.html)
- [(Neuro-)Design Thinking for Digital Engineering, Summer '20](https://hpi.de/studium/im-studium/lehrveranstaltungen/it-systems-engineering-ma/lehrveranstaltung/sose-20-2951-neuro_design-thinking-for-digital-engineering.html)

## Run Commands

### Measure Language Creativity Scores

```python3 src/language_creativity.py --input_file INPUT_FILE [--output_file OUTPUT_FILE] --creativity_scores CREATIVITY_SCORES --language LANGUAGE```

- `INPUT_FILE` is the path to a CSV file containing the sentences to evaluate for language creativity (e.g., `data/de_sentences.csv`) _[required]_
- `OUTPUT_FILE` is the path to a CSV file that will contain the language creativity scores [0, 20] (e.g., `data/de_scores.csv`) _[optional]_
  - Default: `None` (i.e., print to console)
- `CREATIVITY_SCORES` is a filter list indicating the desired creativity scores and their weighting factors _[optional]_
  - Possible creativity scores: `{WORD_NOVELTY, CONTEXT_NOVELTY, PARTICIPANT_SIMILARITY, SENTENCE_SIMILARITY, RHYTHMIC_SCORE, PHONETIC_SCORE}`
  - Possible weighting factors: `(+)[0, 1]`, where the optional `+` indicates a bonus point score
  - Default: `WORD_NOVELTY:0.4,CONTEXT_NOVELTY:0.4,PARTICIPANT_SIMILARITY:0.1,SENTENCE_SIMILARITY:0.1,RHYTHMIC_SCORE:+0.1,PHONETIC_SCORE:+0.1`
- `LANGUAGE` is the language of the input data _[optional]_
  - Possible languages: `{DE, EN}`
  - Default: `DE`

### Generate Creativity Score Distributions

```python3 src/histogram_generator.py --input_file INPUT_FILE --output_file OUTPUT_FILE --creativity_score CREATIVITY_SCORE```

- `INPUT_FILE` is the path to a CSV file containing the measured language creativity scores (e.g., `data/de_scores.csv`) _[required]_
- `OUTPUT_FILE` is the path to a CSV file that will contain the histogram data for the specified creativity score (e.g., `data/de_distribution.csv`) _[required]_
- `CREATIVITY_SCORE` is the creativity score for which to create the histogram data distribution [0, 20] _[required]_
  - Possible creativity scores: `{WORD_NOVELTY, CONTEXT_NOVELTY, PARTICIPANT_SIMILARITY, SENTENCE_SIMILARITY, RHYTHMIC_SCORE, PHONETIC_SCORE, TOTAL_SCORE}`

## Project Supervisors
- Dr. Shama Rahman (shama.rahman[at]hpi.de)
- Dr. Julia von Thienen (julia.vonthienen[at]hpi.de)

## Project Partners
- Theresa Weinstein (theresa.weinstein[at]hpi.de)
- Simon Ceh (simon.ceh[at]uni-graz.at)

## Contributors:
-  [Tobias Maltenberger](https://github.com/maltenbergert) (tobias.maltenberger[at]student.hpi.de)
-  [Ivan Ilic](https://github.com/odanivan) (ivan.ilic[at]student.hpi.de)
