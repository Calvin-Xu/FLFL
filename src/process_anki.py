from enum import Enum
from furigana import generate_furigana
from utils import is_hiragana, is_kanji, is_katakana, is_kana
import json


def extract_entries(file_path):
    examples = []
    with open(file_path, "r") as file:
        for line in file:
            fields = line.strip().split("\t")
            lemma = fields[0]
            reading = fields[1]
            sentence = fields[2]
            if reading == lemma:
                continue
            if all(is_kana(char) for char in lemma):
                continue
            if len(lemma) == 0 or len(reading) == 0:
                continue
            example = {
                "lemma": lemma.split("・")[0],
                "reading": reading,
                "sentence": sentence,
            }
            examples.append(example)
    return examples


def main():
    examples = extract_entries("data/anki_dataset/Mining-All-1.txt")
    output_file = "data/anki_dataset/Mining-All-1.jsonl"
    delimiters = {"ruby": ("<ruby>", "</ruby>"), "rt": ("<rt>", "</rt>")}
    for example in examples:
        if not generate_furigana(example["lemma"], example["reading"], delimiters):
            (example["lemma"], example["reading"])

    with open(output_file, "w", encoding="utf-8") as f:
        for example in examples:
            json_line = json.dumps(
                {
                    # "input": example["lemma"],
                    "output": generate_furigana(
                        example["lemma"], example["reading"], delimiters
                    ),
                    # "context": example["sentence"],
                    "instruction": "",
                    "input": (
                        example["sentence"] + "\n\n" if example["sentence"] else ""
                    )
                    + "[INST]\n"
                    + "次の文に正確に振り仮名を付けてください\n"
                    + example["lemma"]
                    + "\n[/INST]",
                },
                ensure_ascii=False,
            )
            f.write(json_line + "\n")


if __name__ == "__main__":
    main()
