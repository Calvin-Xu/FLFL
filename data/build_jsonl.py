from datasets import load_dataset
import json
import string
import random
import numpy as np
import re
from tqdm import tqdm
import json


def condensed(text):
    text = text.strip()
    text = "".join(text.split())
    text = text.translate(
        str.maketrans("", "", string.punctuation + "()・〔〕「」『』：；’”。、")
    )
    return text


def write_jsonl(dataset, output_file, format_json):
    with open(output_file, "w", encoding="utf-8") as f:
        for example in dataset:
            json_line = json.dumps(format_json(example), ensure_ascii=False)
            f.write(json_line + "\n")


def format_basic(example):
    return {
        "input": example["input"],
        "output": example["output"],
        "instruction": "次の文に正確に振り仮名を付けてください",
    }


def format_dpo(example):
    return {
        "system": "あなたは日本語上級専門家です。",
        "question": f"次の文に正確に振り仮名を付けてください\n{example['input']}",
        "chosen": example["output"],
        "rejected": example["mecab_output"],
    }


def sanity_check(input_string, key_kanji):
    for keyword, readings in key_kanji.items():
        pattern = f"<ruby>{keyword}<rt>(.*?)</rt></ruby>"

        match = re.search(pattern, input_string)

        # print(f"Checking {keyword} in {input_string}")

        if match:
            # print(f"Matched {match}")
            value = match.group(1)
            if value not in readings:
                return False
    return True


KEY_KANJI = {
    "人": ["ひと", "にん", "じん"],
    "回": ["かい"],
    "日": ["ひ", "にち", "じつ", "か"],
    "個": ["こ"],
    "手": ["て", "しゅ"],
}


def dataset_to_jsonl_filter(dataset, output_file, text_replacements={}):
    # filepaths = {}
    n_same, n_diff = 0, 0
    with open(output_file, "w", encoding="utf-8") as f:
        random.shuffle(dataset)
        for example in dataset:
            if len(condensed(example["input"])) < 10:
                continue
            # if example["file_path"] in filepaths:
            #     filepaths[example["file_path"]] += 1
            #     if filepaths[example["file_path"]] > 30:
            #         continue
            if not sanity_check(example["output"], KEY_KANJI):
                continue
            if example["output"] == example["mecab_output"]:
                # if random.random() > 0.1:
                #     continue
                n_same += 1
            else:
                n_diff += 1
            for replacement in text_replacements:
                example["output"] = example["output"].replace(
                    replacement, text_replacements[replacement]
                )
            json_line = json.dumps(
                {
                    "input": example["input"],
                    "output": example["output"],
                    "instruction": "次の文に正確に振り仮名を付けてください",
                },
                ensure_ascii=False,
            )
            # filepaths[example["file_path"]] = 1
            f.write(json_line + "\n")
    print(n_same, n_diff)


TEXT_REPLACEMENTS = {
    "<ruby>何<rt>なん</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>何匹<rt>なんびき</rt></ruby>",
    "<ruby>一<rt>ひと</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>一匹<rt>いっぴき</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>一匹<rt>いっぴき</rt></ruby>",
    "<ruby>三<rt>さん</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>三匹<rt>さんびき</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>六匹<rt>ろっぴき</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>八匹<rt>はっぴき</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>十匹<rt>じっぴき</rt></ruby>",
    "<ruby>百<rt>ひゃく</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>百匹<rt>ひゃっぴき</rt></ruby>",
    "<ruby>千<rt>まん</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>千<rt>せんびき</rt></ruby>",
    "<ruby>万<rt>まん</rt></ruby><ruby>匹<rt>ひき</rt></ruby>": "<ruby>万匹<rt>まんびき</rt></ruby>",
    "<ruby>何<rt>なん</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>何百<rt>なんびゃく</rt></ruby>",
    "<ruby>何<rt>な</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>何百<rt>なんびゃく</rt></ruby>",
    "<ruby>三<rt>さん</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>三百<rt>さんびゃく</rt></ruby>",
    "<ruby>五<rt>ご</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>五百<rt>ごひゃく</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>六百<rt>ろっぴゃく</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>八百<rt>はっぴゃく</rt></ruby>",
    "<ruby>八<rt>や</rt></ruby><ruby>百<rt>ひゃく</rt></ruby>": "<ruby>八百<rt>はっぴゃく</rt></ruby>",
    "<ruby>三<rt>み</rt></ruby><ruby>千<rt>せん</rt></ruby>": "<ruby>三千<rt>さんぜん</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>千<rt>ち</rt></ruby>": "<ruby>八千<rt>はっせん</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>世紀<rt>せいき</rt></ruby>": "<ruby>十世紀<rt>じっせいき</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>八<rt>はち</rt></ruby><ruby>世紀<rt>せいき</rt></ruby>": "<ruby>十八世紀<rt>じゅうはっせいき</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby>世紀<rt>せいき</rt></ruby>": "<ruby>二十世紀<rt>にじっせいき</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>一<rt>いち</rt></ruby><ruby>世紀<rt>せいき</rt></ruby>": "<ruby>二十一世紀<rt>にじゅういっせいき</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>世紀<rt>せいき</rt></ruby>": "<ruby>一世紀<rt>いっせいき</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>一本<rt>いっぽん</rt></ruby>",
    "<ruby>三<rt>さん</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>三本<rt>さんぼん</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>六本<rt>ろっぽん</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>八本<rt>はっぽん</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>十本<rt>じゅっぽん</rt></ruby>",
    "<ruby>百<rt>ひゃく</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>百本<rt>ひゃっぽん</rt></ruby>",
    "<ruby>千<rt>せん</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>千本<rt>せんぼん</rt></ruby>",
    "<ruby>何<rt>なん</rt></ruby><ruby>本<rt>ほん</rt></ruby>": "<ruby>何本<rt>なんぼん</rt></ruby>",
    "<ruby>千<rt>ち</rt></ruby><ruby>円<rt>えん</rt></ruby>": "<ruby>千円<rt>せんえん</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>二日<rt>ふつか</rt></ruby>",
    "<ruby>三<rt>さん</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>三日<rt>みっか</rt></ruby>",
    "<ruby>四<rt>よん</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>四日<rt>よっか</rt></ruby>",
    "<ruby>四<rt>し</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>四日<rt>よっか</rt></ruby>",
    "<ruby>五<rt>ご</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>五日<rt>いつか</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>六日<rt>むいか</rt></ruby>",
    "<ruby>七<rt>しち</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>七日<rt>なのか</rt></ruby>",
    "<ruby>七<rt>なな</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>七日<rt>なのか</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>八日<rt>ようか</rt></ruby>",
    "<ruby>九<rt>きゅう</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>九日<rt>ここのか</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>十日<rt>とおか</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>四<rt>し</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>十四日<rt>じゅうよっか</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>四<rt>よん</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>十四日<rt>じゅうよっか</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>七<rt>なな</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>十<rt>じゅう</rt></ruby><ruby>七<rt>しち</rt></ruby><ruby>日<rt>にち</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>九<rt>きゅう</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>十九日<rt>じゅうくにち</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>二十日<rt>はつか</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>四<rt>し</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>二十四日<rt>にじゅうよっか</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>四<rt>よん</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>二十四日<rt>にじゅうよっか</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>七<rt>なな</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>七<rt>しち</rt></ruby><ruby>日<rt>にち</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>九<rt>きゅう</rt></ruby><ruby>日<rt>にち</rt></ruby>": "<ruby>二十九日<rt>にじゅうくにち</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>冊<rt>さつ</rt></ruby>": "<ruby>一冊<rt>いっさつ</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>冊<rt>さつ</rt></ruby>": "<ruby>八冊<rt>はっさつ</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>冊<rt>さつ</rt></ruby>": "<ruby>十冊<rt>じゅっさつ</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>歳<rt>さい</rt></ruby>": "<ruby>一歳<rt>いっさい</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>歳<rt>さい</rt></ruby>": "<ruby>八歳<rt>はっさい</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>歳<rt>さい</rt></ruby>": "<ruby>十歳<rt>じゅっさい</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>歳<rt>さい</rt></ruby>": "<ruby>二十歳<rt>はたち</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>才<rt>さい</rt></ruby>": "<ruby>一才<rt>いっさい</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>才<rt>さい</rt></ruby>": "<ruby>八才<rt>はっさい</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>才<rt>さい</rt></ruby>": "<ruby>十才<rt>じゅっさい</rt></ruby>",
    "<ruby>二<rt>に</rt></ruby><ruby>十<rt>じゅう</rt></ruby><ruby>才<rt>さい</rt></ruby>": "<ruby>二十才<rt>はたち</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>個<rt>こ</rt></ruby>": "<ruby>一個<rt>いっこ</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>個<rt>こ</rt></ruby>": "<ruby>六個<rt>ろっこ</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>個<rt>こ</rt></ruby>": "<ruby>八個<rt>はっこ</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>個<rt>こ</rt></ruby>": "<ruby>十個<rt>じゅっこ</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>六回<rt>ろっかい</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>十回<rt>じゅっかい</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>ヶ所<rt>かしょ</rt></ruby>": "<ruby>一ヶ所<rt>いっかしょ</rt></ruby>",
    "<ruby>六<rt>ろく</rt></ruby><ruby>ヶ所<rt>かしょ</rt></ruby>": "<ruby>六ヶ所<rt>ろっかしょ</rt></ruby>",
    "<ruby>八<rt>はち</rt></ruby><ruby>ヶ所<rt>かしょ</rt></ruby>": "<ruby>八ヶ所<rt>はっかしょ</rt></ruby>",
    "<ruby>十<rt>じゅう</rt></ruby><ruby>ヶ所<rt>かしょ</rt></ruby>": "<ruby>十ヶ所<rt>じゅっかしょ</rt></ruby>",
    # wtf examples in data
    "<ruby>一<rt>いち</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>回<rt>わ</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>回<rt>た</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>いち</rt></ruby><ruby>回<rt>かえ</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>ひ</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>ひ</rt></ruby><ruby>回<rt>わ</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>ひ</rt></ruby><ruby>回<rt>かえ</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>ひ</rt></ruby><ruby>回<rt>た</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>はじめ</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>はじめ</rt></ruby><ruby>回<rt>かえ</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>はじめ</rt></ruby><ruby>回<rt>わ</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>はじめ</rt></ruby><ruby>回<rt>た</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>ひと</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>一<rt>わん</rt></ruby><ruby>回<rt>かい</rt></ruby>": "<ruby>一回<rt>いっかい</rt></ruby>",
    "<ruby>二<rt>ふ</rt></ruby><ruby>人<rt>じん</rt></ruby>": "<ruby>二人<rt>ふたり</rt></ruby>",
    "<ruby>二<rt>ふ</rt></ruby><ruby>人<rt>ひと</rt></ruby>": "<ruby>二人<rt>ふたり</rt></ruby>",
    "<ruby>二<rt>ふ</rt></ruby><ruby>人<rt>にん</rt></ruby>": "<ruby>二人<rt>ふたり</rt></ruby>",
    "<ruby>二<rt>ふう</rt></ruby><ruby>人<rt>じん</rt></ruby>": "<ruby>二人<rt>ふたり</rt></ruby>",
}


def hito_template(readings):
    output = {}
    for reading in readings:
        output = output | {
            f"<ruby>二<rt>に</rt></ruby><ruby>人<rt>{reading}</rt></ruby>": "<ruby>二人<rt>ふたり</rt></ruby>",
            f"<ruby>四<rt>し</rt></ruby><ruby>人<rt>{reading}</rt></ruby>": "<ruby>四人<rt>よにん</rt></ruby>",
            f"<ruby>四<rt>よん</rt></ruby><ruby>人<rt>{reading}</rt></ruby>": "<ruby>四人<rt>よにん</rt></ruby>",
            f"<ruby>七<rt>なな</rt></ruby><ruby>人<rt>{reading}</rt></ruby>": "<ruby>七人<rt>しちにん</rt></ruby>",
        }
    return output


if __name__ == "__main__":
    dataset = load_dataset("aozora_speech_examples", split="train")
    input_lengths = [len(example["input"]) for example in dataset]
    min_length = int(np.percentile(input_lengths, 5))
    max_length = int(np.percentile(input_lengths, 95))
    print(max(input_lengths), min_length, max_length)

    filtered_dataset = [
        example
        for example in dataset
        if len(example["input"]) >= min_length and len(example["input"]) <= max_length
    ]

    output_jsonl_path = "aozora_speech_new.jsonl"
    TEXT_REPLACEMENTS = TEXT_REPLACEMENTS | hito_template(
        ["ひと", "にん", "じん", "ぴと", "びと"]
    )
    dataset_to_jsonl_filter(filtered_dataset, output_jsonl_path, TEXT_REPLACEMENTS)
