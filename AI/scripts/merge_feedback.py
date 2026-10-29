"""Merge learners' approved error reports (Admin → Nhận diện YOLO → Báo lỗi → Xuất dữ liệu train) into a dataset.

The zip holds images/fb_<id>.jpg, labels/fb_<id>.txt and names.txt (labels written by name), so class ids are
remapped to the dataset's data.yaml here. Goes to the train split only; idempotent (files are overwritten).

    python AI/scripts/merge_feedback.py --zip lingoprism_feedback.zip --data /content/lingoprism_ds_v3/data.yaml

A box whose name is not a class of the dataset (an object learners named in Vietnamese that the detector has no
class for) would leave its object unboxed – learnt as background – so its photo is skipped, unless --add-classes
appends the new names to data.yaml (then train with the larger head). missed/ + missed.csv in the zip are photos of
objects the detector did not find at all: box them by hand first; they are not merged here.
"""
import argparse
import zipfile
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--repeat", type=int, default=3, help="chép mỗi ảnh báo lỗi N lần: ít ảnh nhưng là ca khó, cần trọng số")
    ap.add_argument("--add-classes", action="store_true", help="thêm lớp mới (tên người dùng gõ) vào data.yaml")
    args = ap.parse_args()

    data = yaml.safe_load(Path(args.data).read_text(encoding="utf-8"))
    root = Path(data.get("path") or Path(args.data).parent)
    names = data["names"]
    index = {n: int(i) for i, n in (names.items() if isinstance(names, dict) else enumerate(names))}
    images, labels = root / "images" / "train", root / "labels" / "train"

    with zipfile.ZipFile(args.zip) as z:
        zip_names = z.read("names.txt").decode("utf-8").split("\n")
        zip_names = [n for n in zip_names if n]
        merged = skipped = 0
        added = []
        for entry in z.namelist():
            if not (entry.startswith("images/") and entry.endswith(".jpg")):
                continue
            stem = Path(entry).stem
            boxes = [line.split() for line in z.read(f"labels/{stem}.txt").decode("utf-8").splitlines()]
            boxes = [(zip_names[int(b[0])], b[1:]) for b in boxes if len(b) == 5]
            unknown = {name for name, _ in boxes if name not in index}
            if unknown and not args.add_classes:
                skipped += 1
                continue
            for name in sorted(unknown):
                index[name] = len(index)
                added.append(name)
            lines = [" ".join([str(index[name])] + rest) for name, rest in boxes]
            for r in range(args.repeat):
                (images / f"{stem}_{r}.jpg").write_bytes(z.read(entry))
                (labels / f"{stem}_{r}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            merged += 1
    if added:
        names = list(names.values()) if isinstance(names, dict) else list(names)
        data["names"] = names + added
        data["nc"] = len(data["names"])
        Path(args.data).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"Thêm {len(added)} lớp mới vào {args.data}: {', '.join(added)}")
    for cache in (root / "labels").glob("*.cache"):
        cache.unlink()
    print(f"Đã gộp {merged} ảnh báo lỗi (x{args.repeat}) vào {images}"
          + (f", bỏ {skipped} ảnh có lớp chưa có trong data.yaml (thêm bằng --add-classes)" if skipped else ""))


if __name__ == "__main__":
    main()
