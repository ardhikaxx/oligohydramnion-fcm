import json

filepath = r'D:\klasterisasi_oligohydramnion\k4-oligohydramnion.ipynb'
with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_func = '''def predict_action(cluster_number, usia_ibu_asli=None, gravida_asli=None):
    if cluster_number == 1:
        return "Konservatif / Induksi / Partus spontan"
    if cluster_number == 2:
        return "SC / Konservatif / Induksi / Partus spontan"
    if cluster_number == 3:
        return "SC / SCTP"
    return "SC / SCTP"'''

for cell in data['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'def predict_action(' in source:
            # Replace the whole function block
            lines = source.split('\n')
            start_idx = -1
            end_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('def predict_action('):
                    start_idx = i
                elif start_idx != -1 and line.strip() == '' and not line.startswith(' '):
                    end_idx = i
                    break
            
            # Since the function might be at the end of the cell
            if start_idx != -1 and end_idx == -1:
                end_idx = len(lines)
                
            if start_idx != -1:
                lines[start_idx:end_idx] = new_func.split('\n')
                cell['source'] = [line + '\n' for line in lines]
                cell['source'][-1] = cell['source'][-1].rstrip('\n') # remove last newline

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1)
