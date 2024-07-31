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


def generate_kanji_reading_pairs(lemma, reading):
    # ! it is impossible to determine this from the arguments alone
    # for example, 持ち力 can be (も)ち（ちから）or（もち）ち（から） if you don't know anything
    # this function generates all valid readings (fully-aligned, each kanji mapped to at least one kana)
    # additionally, short readings of kanji are prioritized
    def is_kana(char):
        return is_hiragana(char) or is_katakana(char)

    if not all(is_kana(char) for char in reading):
        raise ValueError("generate_furigana:reading must be in kana")
    # recursive
    # base cases
    if all(is_kanji(char) for char in lemma):
        return [(lemma, reading)]
    if is_kana(lemma[-1]) and lemma[-1] != reading[-1]:
        return None

    class States(Enum):
        START = 1
        KANA = 2
        KANJI = 3
        END = 4

    state = States.START
    current_kanji_block = ""

    results = []

    while True:
        # print(lemma, reading, state)
        match state:
            case States.START:
                if is_kana(lemma[-1]):
                    state = States.KANA
                    lemma = lemma[:-1]
                    reading = reading[:-1]
                else:
                    state = States.KANJI
            case States.KANA:
                if is_kanji(lemma[-1]):
                    state = States.KANJI
                else:
                    lemma = lemma[:-1]
                    reading = reading[:-1]
                    state = States.KANA
            case States.KANJI:
                if all(is_kanji(char) for char in lemma):
                    return [(lemma, reading)]
                current_kanji_block = lemma[-1] + current_kanji_block
                if is_kana(lemma[-2]):
                    splits = []
                    # note that this ordering means short readings are in the front of results
                    # which is a good heuristic
                    for j in range(len(reading)):
                        if reading[j] == lemma[-2]:
                            split = (reading[: j + 1], reading[j + 1 :])
                            splits.append(split)
                    # print(splits)
                    results = [
                        (
                            generate_kanji_reading_pairs(lemma[:-1], split[0]),
                            (current_kanji_block, split[1]),
                        )
                        for split in splits
                    ]
                    state = States.END
                else:
                    state = States.KANJI
            case States.END:
                # print(results)
                for result in results:
                    if result[0] is not None:
                        return result[0] + [result[1]]


def generate_furigana(lemma, reading, delimiters):
    def replace_first(text, lemma, reading):
        index = text.find(lemma)
        if index != -1:
            before = text[:index]
            after = text[index + len(lemma) :]
            ruby_text = f"{delimiters['ruby'][0]}{lemma}{delimiters['rt'][0]}{reading}{delimiters['rt'][1]}{delimiters['ruby'][1]}"
            return before + ruby_text, after
        return text, ""

    text = ("", lemma)
    pairs = generate_kanji_reading_pairs(lemma, reading)
    for pair in pairs:
        left, right = replace_first(text[1], pair[0], pair[1])
        text = (text[0] + left, right)
    return "".join(text)


def main():
    # examples = extract_entries("anki_dataset/Mining-All-1.txt")
    # print(examples)
    lemma = "持ち力と届かない"
    reading = "もちちからととどかない"
    # lemma = "持ち越し"
    # reading = "もちこし"
    # lemma = "子"
    # reading = "こ"
    delimiters = {"ruby": ("<ruby>", "</ruby>"), "rt": ("<rt>", "</rt>")}
    print(generate_furigana(lemma, reading, delimiters))


if __name__ == "__main__":
    main()
