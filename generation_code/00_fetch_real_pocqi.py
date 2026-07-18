#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

FILES = {
    "questions.parquet": "https://huggingface.co/datasets/jjfenglab/Real-POCQi/resolve/main/questions.parquet?download=true",
    "answers.parquet": "https://huggingface.co/datasets/jjfenglab/Real-POCQi/resolve/main/answers.parquet?download=true",
    "ratings.parquet": "https://huggingface.co/datasets/jjfenglab/Real-POCQi/resolve/main/ratings.parquet?download=true",
    "README.md": "https://huggingface.co/datasets/jjfenglab/Real-POCQi/raw/main/README.md",
}


def main() -> None:
    for name, url in FILES.items():
        target = RAW / name
        if target.exists() and target.stat().st_size > 0:
            print(f"exists: {target}")
            continue
        print(f"downloading: {name}")
        urlretrieve(url, target)
    print("done")


if __name__ == "__main__":
    main()

