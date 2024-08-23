from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, AutoPeftModelForCausalLM
import torch

# model_name = "stockmark/gpt-neox-japanese-1.4b"
# adapter = "../Finetunes/checkpoint-8000"

model_name = "../Finetunes/FLFL"

flfl = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# ft_model = PeftModel.from_pretrained(base_model, adapter)

# ft_model = AutoPeftModelForCausalLM.from_pretrained(adapter)

# tokenizer = AutoTokenizer.from_pretrained(adapter)

prompt_template = """[INST] {instruction}\n{input}\n[/INST]\n"""

test_sentences = [
    "国境の長いトンネルを抜けると雪国であった",
    "鰤の照り焼き、八宝菜、ハンバーグ。",
    "主菜関連は、見事なまでの和洋中折衷。",
    # "＜平塚先生が結婚できない理由の一端を垣間見た気がした＞",
    "別の者の目を通じて歴史を垣間見られるとは、想像を超える体験に違いない！",
    "止めるなら、その大本を根絶やしにしないと効果がないわ",
    "不人気銘柄でこれ以上価値が下がりようないから、ほとんど底値だ",
    "時間の澱の中に沈殿していたようだ。",
]

prompts = [
    prompt_template.format(
        instruction="次の文に正確に振り仮名を付けてください", input=sentence
    )
    for sentence in test_sentences
]

# merged = ft_model.merge_and_unload()
# merged.save_pretrained("FLFL")

# tokenizer.save_pretrained("FLFL")

for model in [flfl]:
    for prompt in prompts:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            tokens = model.generate(**inputs, max_new_tokens=512, do_sample=False)

        output = tokenizer.decode(tokens[0], skip_special_tokens=False)
        print(output)
