from enum import Enum
from utils import is_hiragana, is_kanji, is_katakana


def generate_possible_kanji_reading_pairs(text, reading):
    # ! it is impossible to determine an unique reading from the arguments alone
    # for example, 持ち力 can be (も)ち（ちから）or（もち）ち（から） if you don't know anything
    # this function generates all valid readings (fully-aligned, each kanji mapped to at least one kana)
    # and greedily short readings of kanji are at the front of the list (and can be used)

    # this is a good heuristic for short text (like a MeCab token)
    # but fails for for example
    # 鹿乃子のこのこ虎視眈々, しかのこのこのここしたんたん
    # the valid furigana pairs returned are
    # 鹿乃子(しか)のこのこ虎視眈々(のここしたんたん)
    # 鹿乃子(しかのこ)のこのこ虎視眈々(こしたんたん) * correct
    # 鹿乃子(しかのこの)こ虎視眈々(したんたん)

    def is_kana(char):
        return is_hiragana(char) or is_katakana(char)

    if not all(is_kana(char) for char in reading):
        raise ValueError("generate_furigana:reading must be in kana")
    # recursive
    # base cases
    if all(is_kanji(char) for char in text) or all(is_kana(char) for char in text):
        return [[(text, reading)]]
    if is_kana(text[-1]) and text[-1] != reading[-1]:
        return None

    class States(Enum):
        START = 1
        KANA = 2
        KANJI = 3
        END = 4

    state = States.START
    current_kanji_block = ""

    results = []

    while text and reading:
        print(text, reading, state)
        match state:
            case States.START:
                if is_kana(text[-1]):
                    state = States.KANA
                    text = text[:-1]
                    reading = reading[:-1]
                else:
                    state = States.KANJI
            case States.KANA:
                if is_kanji(text[-1]):
                    state = States.KANJI
                else:
                    text = text[:-1]
                    reading = reading[:-1]
                    state = States.KANA
            case States.KANJI:
                if all(is_kanji(char) for char in text):
                    results = [[(text, reading)]]
                    state = States.END
                else:
                    current_kanji_block = text[-1] + current_kanji_block
                    if is_kana(text[-2]):
                        splits = []
                        # shortest readings are in the front of results
                        for j, char in enumerate(reading):
                            if char == text[-2]:
                                split = (reading[: j + 1], reading[j + 1 :])
                                splits.append(split)
                        print(splits)
                        results = [
                            result + [(current_kanji_block, split[1])]
                            for split in splits
                            for result in generate_possible_kanji_reading_pairs(
                                text[:-1], split[0]
                            )
                            if result is not None
                        ]
                        print(results)
                        state = States.END
                    else:
                        state = States.KANJI
                        text = text[:-1]
            case States.END:
                break
    return results


def generate_furigana(text, reading, delimiters):
    def replace_first(text, lemma, reading):
        index = text.find(lemma)
        if index != -1:
            before = text[:index]
            after = text[index + len(lemma) :]
            ruby_text = f"{delimiters['ruby'][0]}{lemma}{delimiters['rt'][0]}{reading}{delimiters['rt'][1]}{delimiters['ruby'][1]}"
            return before + ruby_text, after
        return text, ""

    _text = ("", text)
    pairs = generate_possible_kanji_reading_pairs(text, reading)[0]
    for pair in pairs:
        lemma, reading = pair
        left, right = replace_first(_text[1], lemma, reading)
        _text = (_text[0] + left, right)
    return "".join(_text)


def test_furigana():
    tests = [
        ("持ち力と届かない", "もちちからととどかない"),
        ("持ち越し", "もちこし"),
        ("子", "こ"),
        ("朽ちる", "くちる"),
        ("房々", "ふさふさ"),
        ("蛮殻", "バンカラ"),
        ("がぶ飲み", "がぶのみ"),
        ("已んぬる哉", "やんぬるかな"),
        ("付きっ切り", "つきっきり"),
        ("歯が痛いので歯科医に診てもらった", "はがいたいのでしかいにみてもらった"),
        ("鹿乃子のこのこ虎視眈々", "しかのこのこのここしたんたん"),
    ]
    delimiters = {"ruby": ("<ruby>", "</ruby>"), "rt": ("<rt>", "</rt>")}
    for test in tests:
        print(generate_furigana(test[0], test[1], delimiters))


def main():
    test_furigana()


if __name__ == "__main__":
    main()
