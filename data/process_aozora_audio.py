import string
import zipfile
import os
from datasets import Dataset, DatasetDict, Value, Features

L_REMOVE = r"""!%&)*+,-./:;=>?@\]^_`|}~)・〕"""


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
    current_block = {"input": "", "output": "", "readings": []}
    examples = []

    def process_block(block):
        text = block["input"]
        for lemma, reading in sorted(
            block["readings"], key=lambda x: len(x[0]), reverse=True
        ):
            ruby_text = f"{delimiters['ruby'][0]}{lemma}{delimiters['rt'][0]}{reading}{delimiters['rt'][1]}{delimiters['ruby'][1]}"
            text = text.replace(lemma, ruby_text)
        return text

    with open(file_path, "r", encoding="utf-8") as file:
        readings_section = False
        for line in file:
            if "行番号" in line:
                if current_block["input"]:
                    if len(current_block["readings"]) == 0:
                        continue
                    annotated_text = process_block(current_block)
                    examples.append(
                        {
                            "input": current_block["input"].lstrip(L_REMOVE),
                            "output": annotated_text.lstrip(L_REMOVE),
                        }
                    )
                current_block = {"input": "", "output": "", "readings": []}
            elif "[青空文庫テキスト]" in line:
                current_block["input"] = line.split("\t")[0]
            elif "読み推定結果:" in line:
                readings_section = True
            elif readings_section and line.strip():
                parts = line.strip().split("\t")
                if len(parts) == 4:
                    lemma, inferred_reading, mecab_reading, whisper_text = parts
                    current_block["readings"].append((lemma, inferred_reading))
            elif line.strip() == "":
                readings_section = False

    if current_block["input"]:
        annotated_text = process_block(current_block)
        examples.append({"input": current_block["input"], "output": annotated_text})

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
            "file_path": Value("string"),
        }
    )

    dataset_dict = {k: [d[k] for d in examples] for k in features}
    dataset = Dataset.from_dict(dataset_dict, features=features)
    return DatasetDict({"all_data": dataset})


def main():
    # unprocessed_dir = "aozora_audio"
    root_dir = "aozora_speech_dataset"
    # find_and_extract_zips(unprocessed_dir, root_dir)
    delimiters = {"ruby": ("<ruby>", "</ruby>"), "rt": ("<rt>", "</rt>")}
    dataset = process_directory(root_dir, delimiters)
    dataset.save_to_disk("./aozora_speech_examples")


if __name__ == "__main__":
    main()
