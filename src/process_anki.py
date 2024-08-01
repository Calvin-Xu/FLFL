from enum import Enum
from utils import is_hiragana, is_kanji, is_katakana


def extract_entries(file_path):
    examples = []
    with open(file_path, "r") as file:
        for line in file:
            print(line)
            fields = line.strip().split("\t")
            print(fields)
            lemma = fields[0]
            reading = fields[1]
            sentence = fields[2]
            if reading == lemma:
                continue
            example = {"lemma": lemma, "reading": reading, "sentence": sentence}
            examples.append(example)
    return examples


def main():
    # examples = extract_entries("anki_dataset/Mining-All-1.txt")
    # print(examples)
    pass


if __name__ == "__main__":
    main()
