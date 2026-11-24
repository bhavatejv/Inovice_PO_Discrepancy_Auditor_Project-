import json, re, csv

FIELDS = ["po_number","vendor","currency","payment_terms","quantity","unit_price"]

def extract_field(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None

def extract_number(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m: return None
    try: return float(m.group(1).replace(",", ""))
    except: return None

def extract_document_data(text):
    return {
        "po_number": extract_field(r"PO Number:\s*(.+)", text),
        "vendor": extract_field(r"Vendor:\s*(.+)", text),
        "currency": extract_field(r"Currency:\s*(.+)", text),
        "payment_terms": extract_field(r"Payment Terms:\s*(.+)", text),
        "quantity": extract_number(r"Quantity:\s*([0-9]+(?:\.[0-9]+)?)", text),
        "unit_price": extract_number(r"Unit Price:\s*[₹$]?\s*([0-9,]+(?:\.[0-9]+)?)", text)
    }

def compare(po, inv):
    out = {}
    for f in FIELDS:
        a,b=po.get(f),inv.get(f)
        if a is None and b is None: out[f]="MISSING"
        elif a is None or b is None: out[f]="MISSING"
        elif a == b: out[f]="MATCH"
        else: out[f]="MISMATCH"
    return out

with open("evaluation_30_cases.json", encoding="utf-8") as f:
    cases=json.load(f)

rows=[]
correct=0
total=0
for c in cases:
    actual=compare(extract_document_data(c["purchase_order"]),extract_document_data(c["invoice"]))
    expected=dict(zip(FIELDS,c["expected"]))
    case_correct=sum(actual[k]==expected[k] for k in FIELDS)
    correct += case_correct
    total += len(FIELDS)
    rows.append({
        "case_id":c["case_id"],
        "category":c["category"],
        "correct_fields":case_correct,
        "total_fields":len(FIELDS),
        "field_accuracy":round(case_correct/len(FIELDS)*100,2),
        "expected_mismatches":sum(v=="MISMATCH" for v in expected.values()),
        "detected_mismatches":sum(v=="MISMATCH" for v in actual.values())
    })

with open("evaluation_results.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

print(f"Overall field accuracy: {correct/total*100:.2f}%")
print("Saved evaluation_results.csv")
