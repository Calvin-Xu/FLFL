import re
import os
from datasets import Dataset, DatasetDict, Value, Features


def process_reading(reading):
    """
    Processes a kanji reading by replacing elongation characters with 'う' in certain cases.

    Args:
        reading (str): The reading to be processed.

    Returns:
        str: The processed reading.
    """
    # hiragana that can be followed by 'う' for elongation
    elongation_pattern = r"(お|こ|そ|と|の|ほ|も|よ|ろ|を|ご|ぞ|ど|ぼ|ぽ|く|ぐ|す|ず|つ|づ|ぬ|ふ|ぶ|ぷ|む|ゆ|る|しょ|ちょ|じょ|にょ|ひょ|みょ|りょ|きょ|ぎょ|びょ|ぴょ|しゅ|ちゅ|じゅ|にゅ|ひゅ|みゅ|りゅ|きゅ|ぎゅ|びゅ|ぴゅ)ー"
    # replace 'ー' with 'う'
    processed_reading = re.sub(elongation_pattern, r"\1う", reading)
    return processed_reading


def process_line(line, delimiters, furiganafy=True, postprocess=True):
    """
    Processes a single line from the file.

    Args:
        line (str): The line to be processed.
        delimiters (dict): A dictionary containing delimiter configurations.
        postprocess (bool): Whether to postprocess the reading.

    Returns:
        str: The processed line.
    """
    parts = line.split("\t")
    if len(parts) == 3:
        text, reading, pos = parts
        if pos.strip() == "漢字":
            if postprocess:
                reading = process_reading(reading)
            return f"{delimiters['ruby'][0]}{text}{delimiters['rt'][0]}{reading}{delimiters['rt'][1]}{delimiters['ruby'][1]}"
        elif pos.strip() == "分かち書き":
            return ""
        else:
            return text
    if len(parts) == 4:  # katakana entries are like this, what do I know
        text, reading, pos, _ = parts
        # if pos.strip() == "カタカナ":
        return text
    return ""


def condensed(text):
    text = "".join(text.split())
    text = text.replace("※", "")
    return text


def process_file(
    filepath, delimiter_config, validate_sentence=False, validate_reading=False
):
    """
    Processes a single file and returns a list of examples.

    Args:
        filepath (str): The path to the file to be processed.
        delimiter_config (dict): A dictionary containing delimiter configurations.

    Returns:
        list: A list of examples, where each example is a dictionary containing the input sentence, output sentence, and reference reading.
    """
    examples = []
    with open(filepath, "r", encoding="utf-8") as file:
        sentence, reading, segments = "", "", []
        sentence_validation, reading_validation = "", ""
        for line in file:
            if "行番号" in line:
                if segments:  # reached new example; process the previous one
                    formatted_output = "".join(segments)
                    sentence_validation = condensed(sentence_validation)
                    reading_validation = condensed(reading_validation)
                    _sentence = condensed(sentence)
                    _reading = condensed(reading)
                    if (
                        "<ruby>" not in formatted_output
                        or (_sentence != sentence_validation and validate_sentence)
                        or (_reading != reading_validation and validate_reading)
                    ):
                        if _sentence != sentence_validation:
                            print(
                                f"Error: {_sentence} != {sentence_validation}, file: {filepath}"
                            )
                        if _reading != reading_validation:
                            print(
                                f"Error: {_reading} != {reading_validation}, file: {filepath}"
                            )
                    else:
                        examples.append(
                            {
                                "input": sentence.replace("※", ""),
                                "output": formatted_output,
                                "ref_reading": reading_validation,
                            }
                        )
                sentence = next(file).split("\t")[0]
                reading = next(file).split("\t")[1]
                segments, sentence_validation, reading_validation = (
                    [],
                    "",
                    "",
                )  # reset for new example
            else:
                segment_output = process_line(line, delimiter_config, postprocess=False)
                segments.append(segment_output)
                sentence_validation += line.split("\t")[0]
                reading_validation += line.split("\t")[1]

        # Process the last example in the file
        formatted_output = "".join(segments).strip()
        if (
            "<ruby>" not in formatted_output
            or (condensed(sentence) != sentence_validation and validate_sentence)
            or (condensed(reading) != reading_validation and validate_reading)
        ):
            examples.append(
                {"input": sentence, "output": formatted_output, "ref_reading": reading}
            )

    return examples


def process_directory(
    root_dir, delimiters, validate_sentence=False, validate_reading=False
):
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
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in [f for f in filenames if f.endswith(".txt")]:
            filepath = os.path.join(dirpath, filename)
            file_examples = process_file(filepath, delimiters)
            for example in file_examples:
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
            "ref_reading": Value("string"),
            "file_path": Value("string"),
        }
    )

    dataset_dict = {k: [d[k] for d in examples] for k in features}
    dataset = Dataset.from_dict(dataset_dict, features=features)
    return DatasetDict({"all_data": dataset})


def main():
    root_directory = "aozora_dataset"
    delimiters = {"ruby": ("<ruby>", "</ruby>"), "rt": ("<rt>", "</rt>")}
    dataset = process_directory(
        root_directory, delimiters, validate_sentence=True, validate_reading=True
    )
    dataset.save_to_disk("./aozora_examples")


if __name__ == "__main__":
    main()
