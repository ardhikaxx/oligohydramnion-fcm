import json
from pathlib import Path

root = Path(r"D:\klasterisasi_oligohydramnion")
notebooks = ["evaluasi.ipynb", "k2-oligohydramnion.ipynb", "k3-oligohydramnion.ipynb", "k4-oligohydramnion.ipynb", "k5-oligohydramnion.ipynb"]

target_old = """    if "sc" in text or "sctp" in text:
        return "sc (termasuk cito sc, sctp, pro sc, & kombinasi)"
    if "konservatif" in text or "perawatan" in text:
        return "perawatan konservatif\""""

target_new = """    if "sc" in text or "sctp" in text:
        return "sc (termasuk cito sc, sctp, pro sc, & kombinasi)"
    if "partus" in text or "spontan" in text:
        return "partus spontan (termasuk od, partus spontan)"
    if "konservatif" in text or "perawatan" in text:
        return "perawatan konservatif\""""

for nb_name in notebooks:
    nb_path = root / nb_name
    with open(nb_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    changed = False
    for cell in data.get("cells", []):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            if "def clean_action_text(value):" in source and target_old in source:
                new_source = source.replace(target_old, target_new)
                if new_source != source:
                    # convert back to list of lines if cell["source"] was list
                    if isinstance(cell["source"], list):
                        lines = new_source.splitlines(keepends=True)
                        cell["source"] = lines
                    else:
                        cell["source"] = new_source
                    changed = True
    
    if changed:
        with open(nb_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print(f"Updated {nb_name}")
    else:
        print(f"No change or already updated in {nb_name}")
