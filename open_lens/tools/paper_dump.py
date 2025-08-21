from paperscraper.get_dumps import biorxiv, medrxiv, chemrxiv, arxiv
import os

os.makedirs("datasets/paperscraper", exist_ok=True)
medrxiv(save_path="datasets/paperscraper/medrxiv.jsonl")  #  Takes ~30min and should result in ~35 MB file
arxiv(save_path="datasets/paperscraper/arxiv.jsonl")