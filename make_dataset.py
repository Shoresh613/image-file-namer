import os
import json
import argparse

DEFAULT_PROMPT = (
    "Output keywords for this image in one line for the purpose of giving the image file a "
    "name for easy search. Just a single space between keywords. No emojis."
)

def build_dataset(image_dir, human_prompt, data_out, info_out):
    entries = []
    for fn in sorted(os.listdir(image_dir)):
        name, ext = os.path.splitext(fn)
        if ext.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}:
            continue

        rel_path = os.path.join("./", fn)
        entry = {
            "conversations": [
                {
                    "from": "human",
                    "value": f"<image>{human_prompt}"
                },
                {
                    "from": "gpt",
                    "value": name
                }
            ],
            "images": [rel_path]
        }
        entries.append(entry)

    # write data.json
    with open(data_out, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(entries)} records to {data_out}")

    # write dataset_info.json
    dataset_info = {
        "dataset_name": {
            "file_name": os.path.basename(data_out),
            "formatting": "sharegpt",
            "columns": {
                "messages": "conversations",
                "images": "images"
            }
        }
    }
    with open(info_out, "w", encoding="utf-8") as f:
        json.dump(dataset_info, f, indent=2, ensure_ascii=False)
    print(f"Wrote dataset description to {info_out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Build multimodal fine-tuning dataset from a folder of images"
    )
    p.add_argument(
        "image_dir",
        help="Path to folder containing your images"
    )
    p.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Human instruction text suffix (prepended by <image>)"
    )
    p.add_argument(
        "--data-out",
        default="data.json",
        help="Output JSON file for the dataset"
    )
    p.add_argument(
        "--info-out",
        default="dataset_info.json",
        help="Output dataset_info.json"
    )
    args = p.parse_args()

    build_dataset(
        image_dir=args.image_dir,
        human_prompt=args.prompt,
        data_out=args.data_out,
        info_out=args.info_out
    )
