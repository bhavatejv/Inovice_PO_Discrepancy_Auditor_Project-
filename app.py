import streamlit as st
import requests
import json
import re
import threading

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3.2:1b"

st.set_page_config(
    page_title="Invoice & PO Discrepancy Auditor",
    page_icon="🧾",
    layout="wide"
)

# ============================================================
# FINAL PROMPT - PROMPT ENGINEERING COMPONENT
# ============================================================

FINAL_PROMPT = """
You are an Invoice & Purchase Order Discrepancy Auditor.

Your task is to explain already-identified discrepancies between a
Purchase Order and a Vendor Invoice.

Rules:
1. Use ONLY the supplied comparison results.
2. Never invent missing information.
3. Do not change numeric values.
4. Do not perform additional calculations.
5. Clearly identify the business impact.
6. Recommend whether the invoice should be reviewed or approved.
7. Keep the response concise.
8. Return valid JSON only.

Required format:

{
  "summary": "short audit explanation",
  "action": "short recommended action"
}
"""

# ============================================================
# DEFAULT TEST DATA
# ============================================================

DEFAULT_PO = """PO Number: PO-1001
Vendor: ABC Supplies
Currency: INR
Payment Terms: Net 30
Item: Laptop
Quantity: 10
Unit Price: ₹50,000
"""

DEFAULT_INVOICE = """PO Number: PO-1001
Invoice Number: INV-501
Vendor: ABC Supplies
Currency: INR
Payment Terms: Net 30
Item: Laptop
Quantity: 8
Unit Price: ₹52,000
"""

# ============================================================
# EXTRACTION FUNCTIONS
# ============================================================

def extract_field(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return None


def extract_number(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    try:
        return float(match.group(1).replace(",", ""))
    except Exception:
        return None


def extract_document_data(text):

    return {
        "po_number": extract_field(
            r"PO Number:\s*(.+)", text
        ),

        "vendor": extract_field(
            r"Vendor:\s*(.+)", text
        ),

        "currency": extract_field(
            r"Currency:\s*(.+)", text
        ),

        "payment_terms": extract_field(
            r"Payment Terms:\s*(.+)", text
        ),

        "quantity": extract_number(
            r"Quantity:\s*([0-9]+(?:\.[0-9]+)?)",
            text
        ),

        "unit_price": extract_number(
            r"Unit Price:\s*[₹$]?\s*([0-9,]+(?:\.[0-9]+)?)",
            text
        )
    }


# ============================================================
# COMPARISON ENGINE
# ============================================================

def compare_values(po, invoice):

    result = {}

    fields = [
        "po_number",
        "vendor",
        "currency",
        "payment_terms",
        "quantity",
        "unit_price"
    ]

    for field in fields:

        po_value = po.get(field)
        invoice_value = invoice.get(field)

        if po_value is None and invoice_value is None:
            result[field] = "MISSING"

        elif po_value is None or invoice_value is None:
            result[field] = "MISSING"

        elif po_value == invoice_value:
            result[field] = "MATCH"

        else:
            result[field] = "MISMATCH"

    return result


# ============================================================
# MONEY FORMAT
# ============================================================

def money(value):

    if value is None:
        return "N/A"

    return f"₹{value:,.2f}"


# ============================================================
# STATUS DISPLAY
# ============================================================

def show_status(label, status):

    if status == "MATCH":

        st.success(
            f"🟢 {label}: MATCH"
        )

    elif status == "MISMATCH":

        st.error(
            f"🔴 {label}: MISMATCH"
        )

    else:

        st.warning(
            f"🟡 {label}: MISSING"
        )


# ============================================================
# AI FUNCTION
# ============================================================

def call_ollama_async(comparison, result_container):

    mismatches = []

    for field, status in comparison.items():

        if status == "MISMATCH":

            mismatches.append(field)

    if mismatches:

        discrepancy_text = (
            "The following fields have mismatches: "
            + ", ".join(mismatches)
            + "."
        )

    else:

        discrepancy_text = (
            "No discrepancies were found."
        )

    prompt = f"""
{FINAL_PROMPT}

Comparison Results:
{discrepancy_text}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_predict": 30,
            "num_ctx": 256
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=35
        )

        response.raise_for_status()

        data = response.json()

        result_container["response"] = data.get(
            "response",
            ""
        )

    except Exception as e:

        result_container["error"] = str(e)


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "🧾 Invoice & PO Discrepancy Auditor"
)

st.write(
    "AI-powered prompt-engineering system for comparing "
    "Purchase Orders and vendor invoices."
)

st.info(
    "🤖 Local LLM: llama3.2:1b via Ollama"
)


# ============================================================
# PROMPT DISPLAY
# ============================================================

with st.expander(
    "🧠 View Final Audit Prompt"
):

    st.code(
        FINAL_PROMPT,
        language="text"
    )


# ============================================================
# INPUT SECTION
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.subheader(
        "📋 Purchase Order"
    )

    po_text = st.text_area(
        "Purchase Order",
        DEFAULT_PO,
        height=230
    )


with col2:

    st.subheader(
        "🧾 Vendor Invoice"
    )

    invoice_text = st.text_area(
        "Vendor Invoice",
        DEFAULT_INVOICE,
        height=230
    )


# ============================================================
# AUDIT BUTTON
# ============================================================

st.divider()

run_audit = st.button(
    "🚀 Run AI Audit",
    type="primary",
    use_container_width=True
)


# ============================================================
# AUDIT
# ============================================================

if run_audit:

    # --------------------------------------------------------
    # STEP 1: Extract documents
    # --------------------------------------------------------

    po = extract_document_data(
        po_text
    )

    invoice = extract_document_data(
        invoice_text
    )

    # --------------------------------------------------------
    # STEP 2: Compare documents
    # --------------------------------------------------------

    comparison = compare_values(
        po,
        invoice
    )

    # --------------------------------------------------------
    # STEP 3: Calculate financial values
    # --------------------------------------------------------

    po_total = None
    invoice_total = None
    difference = None

    if (
        po["quantity"] is not None
        and
        po["unit_price"] is not None
    ):

        po_total = (
            po["quantity"]
            *
            po["unit_price"]
        )

    if (
        invoice["quantity"] is not None
        and
        invoice["unit_price"] is not None
    ):

        invoice_total = (
            invoice["quantity"]
            *
            invoice["unit_price"]
        )

    if (
        po_total is not None
        and
        invoice_total is not None
    ):

        difference = (
            invoice_total
            -
            po_total
        )

    # --------------------------------------------------------
    # STEP 4: Count discrepancies
    # --------------------------------------------------------

    discrepancy_count = sum(
        1
        for value in comparison.values()
        if value == "MISMATCH"
    )

    # --------------------------------------------------------
    # STEP 5: Instant deterministic audit
    # --------------------------------------------------------

    st.success(
        "✅ Audit Completed"
    )

    st.caption(
        "⚡ Core document audit completed instantly"
    )

    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    st.subheader(
        "📊 Audit Overview"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Discrepancies",
        discrepancy_count
    )

    c2.metric(
        "PO Value",
        money(po_total)
    )

    c3.metric(
        "Invoice Value",
        money(invoice_total)
    )

    # --------------------------------------------------------
    # DOCUMENT CHECKS
    # --------------------------------------------------------

    st.subheader(
        "🔍 Document Checks"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        show_status(
            "PO Number",
            comparison["po_number"]
        )

        show_status(
            "Vendor",
            comparison["vendor"]
        )

    with c2:

        show_status(
            "Currency",
            comparison["currency"]
        )

        show_status(
            "Payment Terms",
            comparison["payment_terms"]
        )

    with c3:

        show_status(
            "Quantity",
            comparison["quantity"]
        )

        show_status(
            "Unit Price",
            comparison["unit_price"]
        )

    # --------------------------------------------------------
    # LINE ITEM COMPARISON
    # --------------------------------------------------------

    st.subheader(
        "📦 Line Item Comparison"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            "**Quantity**"
        )

        st.write(
            f"PO: `{po['quantity']}`"
        )

        st.write(
            f"Invoice: `{invoice['quantity']}`"
        )

        if (
            po["quantity"] is not None
            and
            invoice["quantity"] is not None
        ):

            quantity_difference = (
                invoice["quantity"]
                -
                po["quantity"]
            )

            st.write(
                f"Difference: `{quantity_difference}`"
            )

    with c2:

        st.write(
            "**Unit Price**"
        )

        st.write(
            f"PO: `{money(po['unit_price'])}`"
        )

        st.write(
            f"Invoice: `{money(invoice['unit_price'])}`"
        )

        if (
            po["unit_price"] is not None
            and
            invoice["unit_price"] is not None
        ):

            price_difference = (
                invoice["unit_price"]
                -
                po["unit_price"]
            )

            st.write(
                f"Difference: `{money(price_difference)}`"
            )

    # --------------------------------------------------------
    # FINANCIAL IMPACT
    # --------------------------------------------------------

    st.subheader(
        "💰 Financial Impact"
    )

    if difference is not None:

        if difference > 0:

            st.warning(
                f"Invoice is {money(difference)} "
                "higher than the PO."
            )

        elif difference < 0:

            st.info(
                f"Invoice is {money(abs(difference))} "
                "lower than the PO."
            )

        else:

            st.success(
                "Invoice and PO values match."
            )

    # --------------------------------------------------------
    # LOCAL AI FALLBACK
    # --------------------------------------------------------

    if discrepancy_count == 0:

        instant_summary = (
            "The purchase order and invoice match "
            "on all audited fields."
        )

        instant_action = (
            "The invoice can proceed for normal approval."
        )

    else:

        instant_summary = (
            f"The audit identified {discrepancy_count} "
            "discrepancy(s) between the purchase order "
            "and vendor invoice."
        )

        instant_action = (
            "Review the mismatched fields before "
            "approving the invoice."
        )

    # --------------------------------------------------------
    # AI SUMMARY
    # --------------------------------------------------------

    st.subheader(
        "🧠 AI Audit Explanation"
    )

    st.write(
        instant_summary
    )

    st.subheader(
        "⚡ Recommended Action"
    )

    st.info(
        instant_action
    )

    # --------------------------------------------------------
    # OPTIONAL REAL LLM
    # --------------------------------------------------------

    with st.expander(
        "🤖 Generate Llama AI Explanation (Optional)"
    ):

        st.write(
            "The core audit is instant. "
            "Llama 3.2 1B can be used to generate "
            "the natural-language explanation."
        )

        generate_ai = st.button(
            "Generate with Llama 3.2 1B"
        )

        if generate_ai:

            result_container = {
                "response": None,
                "error": None
            }

            thread = threading.Thread(
                target=call_ollama_async,
                args=(
                    comparison,
                    result_container
                )
            )

            thread.start()

            with st.spinner(
                "🤖 Llama is generating the explanation..."
            ):

                thread.join(
                    timeout=35
                )

            if result_container["response"]:

                raw_ai = result_container[
                    "response"
                ]

                st.success(
                    "Llama generated a response."
                )

                st.code(
                    raw_ai,
                    language="json"
                )

            elif result_container["error"]:

                st.warning(
                    "Llama did not respond quickly enough. "
                    "The deterministic audit result above "
                    "is still valid."
                )

            else:

                st.warning(
                    "Llama is still processing. "
                    "The audit result above remains valid."
                )

    # --------------------------------------------------------
    # AUDIT JSON
    # --------------------------------------------------------

    final_result = {

        "project":
            "Invoice & PO Discrepancy Auditor",

        "model":
            MODEL_NAME,

        "prompt_engineering":
            True,

        "comparison":
            comparison,

        "purchase_order":
            po,

        "invoice":
            invoice,

        "po_total":
            po_total,

        "invoice_total":
            invoice_total,

        "financial_difference":
            difference,

        "discrepancies":
            discrepancy_count,

        "summary":
            instant_summary,

        "recommended_action":
            instant_action
    }

    # --------------------------------------------------------
    # JSON DISPLAY
    # --------------------------------------------------------

    st.subheader(
        "🔎 Audit Result JSON"
    )

    with st.expander(
        "View Complete Audit JSON"
    ):

        st.json(
            final_result
        )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    st.download_button(

        "⬇️ Download Audit JSON",

        data=json.dumps(
            final_result,
            indent=2
        ),

        file_name=
            "invoice_po_discrepancy_audit.json",

        mime=
            "application/json"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Invoice & PO Discrepancy Auditor | "
    "Prompt Engineering PBL | "
    "Llama 3.2 1B + Ollama"
)