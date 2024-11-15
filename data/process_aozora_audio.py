import string
import zipfile
import os
from datasets import Dataset, DatasetDict, Value, Features
import json
from collections import defaultdict

L_REMOVE = r"""!%&)*+,-./:;=>?@\]^_`|}~)・〕"""

# KANJI_DATA = defaultdict(set)
# with open("kanji-kyouiku.json", "r", encoding="utf-8") as file:
#     kanji_data_full = json.load(file)
#     for kanji in kanji_data_full:
#         KANJI_DATA[kanji].update(kanji_data_full[kanji]["readings_on"])
#         KANJI_DATA[kanji].update(kanji_data_full[kanji]["readings_kun"])
#     print(KANJI_DATA)


def condensed(text):
    text = text.strip()
    text = "".join(text.split())
    punctuation = string.punctuation + "()・〔〕"
    text = (text.rstrip(punctuation)).lstrip(punctuation)
    return text


def extract_txt_csv_files(zip_path, extract_to):
    # create dir with name of zip file
    directory_name = os.path.splitext(os.path.basename(zip_path))[0]
    full_extract_path = os.path.join(extract_to, directory_name)
    os.makedirs(full_extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        file_list = zip_ref.namelist()
        for file in file_list:
            if file.endswith(".txt") or file.endswith(".csv"):
                zip_ref.extract(file, full_extract_path)
                print(f"Extracted: {file} to {full_extract_path}")


def find_and_extract_zips(root_dir, target_dir):
    n = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".zip"):
                zip_path = os.path.join(root, file)
                print(f"Extracting: {zip_path}")
                extract_txt_csv_files(zip_path, target_dir)
                n += 1
    print(f"Extracted {n} zip files")


def process_file(file_path, delimiters):
    current_block = {
        "input": "",
        "output": "",
        "inferred_readings": [],
        "mecab_readings": [],
    }
    examples = []

    def process_block(block):
        texts = {
            "inferred_readings": ("", block["input"]),
            "mecab_readings": ("", block["input"]),
        }
        readings_queue = {
            "inferred_readings": block["inferred_readings"].copy(),
            "mecab_readings": block["mecab_readings"].copy(),
        }

        def replace_first(text, lemma, reading):
            index = text.find(lemma)
            if index != -1:
                before = text[:index]
                after = text[index + len(lemma) :]
                ruby_text = f"{delimiters['ruby'][0]}{lemma}{delimiters['rt'][0]}{reading}{delimiters['rt'][1]}{delimiters['ruby'][1]}"
                return before + ruby_text, after
            return text, ""

        for reading_ver in ["inferred_readings", "mecab_readings"]:
            for _ in range(len(readings_queue[reading_ver])):
                if readings_queue[reading_ver]:
                    lemma, reading = readings_queue[reading_ver].pop(0)
                    before, after = replace_first(texts[reading_ver][1], lemma, reading)
                    texts[reading_ver] = (texts[reading_ver][0] + before, after)

        inferred_annotated = "".join(texts["inferred_readings"])
        mecab_annotated = "".join(texts["mecab_readings"])
        return inferred_annotated, mecab_annotated

    with open(file_path, "r", encoding="utf-8") as file:
        readings_section = False
        # kanji_check_failed = False
        for line in file:
            if "行番号" in line:
                if current_block["input"]:
                    if (
                        len(current_block["inferred_readings"]) == 0
                        # or kanji_check_failed
                    ):
                        continue
                    inferred_annotated, mecab_annotated = process_block(current_block)
                    examples.append(
                        {
                            "input": current_block["input"].lstrip(L_REMOVE),
                            "output": inferred_annotated.lstrip(L_REMOVE),
                            "mecab_output": mecab_annotated.lstrip(L_REMOVE),
                        }
                    )
                current_block = {
                    "input": "",
                    "output": "",
                    "inferred_readings": [],
                    "mecab_readings": [],
                }
                # kanji_check_failed = False
            elif "[青空文庫テキスト]" in line:
                current_block["input"] = line.split("\t")[0]
            elif "読み推定結果:" in line:
                readings_section = True
            elif readings_section and line.strip():
                parts = line.strip().split()  # there are mixed spaces here...
                if len(parts) == 4:
                    lemma, inferred_reading, mecab_reading, whisper_text = parts
                    # if inferred_reading not in KANJI_DATA[lemma]:
                    #     kanji_check_failed = True
                    current_block["inferred_readings"].append((lemma, inferred_reading))
                    current_block["mecab_readings"].append((lemma, mecab_reading))
            elif line.strip() == "":
                readings_section = False

    if current_block["input"]:
        if len(current_block["inferred_readings"]) != 0:
            inferred_annotated, mecab_annotated = process_block(current_block)
            examples.append(
                {
                    "input": current_block["input"].lstrip(L_REMOVE),
                    "output": inferred_annotated.lstrip(L_REMOVE),
                    "mecab_output": mecab_annotated.lstrip(L_REMOVE),
                }
            )

    return examples


def process_directory(root_dir, delimiters):
    """
    Walks through the directory, processes all .txt files, and adds the examples to a HuggingFace dataset.

    Args:
        root_dir (str): The root directory to start the walk.
        delimiters (dict): A dictionary containing delimiter configurations.

    Returns:
        DatasetDict: A HuggingFace dataset containing all processed examples.
    """
    examples = []
    n_file_processed = 0
    seen_examples = set()
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in [f for f in filenames if f.endswith(".txt")]:
            filepath = os.path.join(dirpath, filename)
            file_examples = process_file(filepath, delimiters)
            for example in file_examples:
                input_output_pair = (
                    condensed(example["input"]),
                    condensed(example["output"]),
                )
                if input_output_pair not in seen_examples:  # Check for duplication
                    seen_examples.add(input_output_pair)
                    example["file_path"] = os.path.relpath(
                        filepath, start=root_dir
                    )  # Add relative file path to each example
                    examples.append(example)
            n_file_processed += 1
            if n_file_processed % 100 == 0:
                print(f"Processed {n_file_processed} files", flush=True)
    print(f"Processed {n_file_processed} files", flush=True)

    features = Features(
        {
            "input": Value("string"),
            "output": Value("string"),
            "mecab_output": Value("string"),
            "file_path": Value("string"),
        }
    )

    dataset_dict = {k: [d[k] for d in examples] for k in features}
    dataset = Dataset.from_dict(dataset_dict, features=features)
    return DatasetDict({"all_data": dataset})


def main():
    # # unprocessed_dir = "aozora_audio"
    root_dir = "aozora_speech_dataset"
    # # find_and_extract_zips(unprocessed_dir, root_dir)
    delimiters = {"ruby": ("<ruby>", "</ruby>"), "rt": ("<rt>", "</rt>")}

    dataset = process_directory(root_dir, delimiters)
    dataset.save_to_disk("./aozora_speech_examples")
    print(dataset["all_data"])
    print(dataset["all_data"][:10])
    # print(process_file("/Users/calvinxu/Projects/ML/FLFL/test.txt", delimiters))


if __name__ == "__main__":
    main()
