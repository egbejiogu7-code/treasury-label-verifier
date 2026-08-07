import re
from difflib import SequenceMatcher

import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import numpy as np


STANDARD_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not "
    "drink alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)


def normalize_text(value: str) -> str:
    """Normalize text for comparisons that should ignore capitalization and spacing."""
    value = value or ""
    value = value.upper()
    value = re.sub(r"[^A-Z0-9%.'/-]+", " ", value)
    return " ".join(value.split())


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(
        None,
        normalize_text(left),
        normalize_text(right),
    ).ratio()


def extract_abv(text: str) -> str | None:
    """Extract ABV percentage, with proof as a fallback."""
    text = text or ""

    # First look for an explicit ABV percentage such as
    # 45%, 45.0%, 45 % ALC./VOL.
    match = re.search(
        r"(\d{1,3}(?:\.\d+)?)\s*(?:%|PERCENT)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    # Fallback: US proof is approximately 2 x ABV.
    # Example: 90 PROOF = 45% ABV.
    proof_match = re.search(
        r"(\d{1,3}(?:\.\d+)?)\s*PROOF",
        text,
        re.IGNORECASE,
    )

    if proof_match:
        proof = float(proof_match.group(1))
        return str(proof / 2)

    return None


def status_icon(passed: bool) -> str:
    return "✅" if passed else "❌"


st.set_page_config(
    page_title="TTB Label Verification",
    page_icon="🔎",
    layout="wide",
)

st.title("AI-Powered Alcohol Label Verification")
st.caption(
    "Prototype for comparing alcohol-label artwork with application information."
)

left, right = st.columns(2)

with left:
    st.subheader("1. Application information")

    expected_brand = st.text_input(
        "Brand name",
        placeholder="Example: OLD TOM DISTILLERY",
    )

    expected_abv = st.number_input(
        "Alcohol by volume (ABV %)",
        min_value=0.0,
        max_value=100.0,
        value=45.0,
        step=0.1,
    )

    expected_warning = st.text_area(
        "Required government warning",
        value=STANDARD_WARNING,
        height=180,
    )

with right:
    st.subheader("2. Label artwork")

    uploaded_file = st.file_uploader(
        "Upload a label image",
        type=["png", "jpg", "jpeg"],
    )
    ocr_text = ""
if uploaded_file:
    label_image = Image.open(uploaded_file).convert("RGB")

    st.image(
        label_image,
        caption=uploaded_file.name,
        use_container_width=True,
    )

with st.spinner("Reading text from label image..."):
            try:
                # Convert to RGB for consistent OCR processing
                ocr_image = label_image.convert("RGB")

                # Resize large phone/camera images to reduce memory usage
                max_dimension = 1600
                width, height = ocr_image.size

                if max(width, height) > max_dimension:
                    scale = max_dimension / max(width, height)
                    new_size = (
                        int(width * scale),
                        int(height * scale),
                    )
                    ocr_image = ocr_image.resize(new_size)


                # Improve contrast and clarity for OCR
                    processed_image = ImageOps.grayscale(ocr_image)
                    processed_image = ImageOps.autocontrast(processed_image)
                    processed_image = ImageEnhance.Sharpness(processed_image).enhance(2.0)

# Try two Tesseract layouts so we can detect both
# structured label text and scattered text
                    text_block = pytesseract.image_to_string(
                        processed_image,
                        config="--psm 6"
)

                    text_sparse = pytesseract.image_to_string(
                        processed_image,
                        config="--psm 11"
)

                ocr_text = text_block + "\n" + text_sparse

                if not ocr_text.strip():
                    st.warning(
                        "No readable text was detected. "
                        "Please upload a clearer, closer image of the label."
                    )

            except Exception:
                st.error(
                    "The label could not be processed. "
                    "Please upload a clearer or smaller image and try again."
                )
                ocr_text = ""
     


st.divider()

st.subheader("3. Text detected from label")
st.info(
    "Upload a label image above. The app will extract the visible text automatically. "
"You can correct the extracted text before running verification."
)

detected_text = st.text_area(
    "Label text",
    value=ocr_text,
    height=220,
    placeholder=(
        "OLD TOM DISTILLERY\n"
        "Kentucky Straight Bourbon Whiskey\n"
        "45% Alc./Vol. (90 Proof)\n"
        "750 mL\n"
        "GOVERNMENT WARNING: ..."
    ),
)

if st.button("Verify label", type="primary", use_container_width=True):
    if not expected_brand.strip():
        st.error("Enter the brand name from the application.")
    elif not detected_text.strip():
        st.error("Enter or extract the text from the label.")
    else:
        brand_normalized = normalize_text(expected_brand)
        label_normalized = normalize_text(detected_text)

        brand_words = brand_normalized.split()
        brand_matches = sum(word in label_normalized for word in brand_words)

        brand_score = brand_matches / len(brand_words) if brand_words else 0
        brand_passed = brand_score >= 0.67  

        detected_abv = extract_abv(detected_text)
        abv_passed = (
            detected_abv is not None
            and abs(float(detected_abv) - float(expected_abv)) < 0.01
        )

warning_keywords = [
            "government warning",
            "surgeon general",
            "pregnancy",
            "birth defects",
            "operate machinery",
            "health problems",
        ]

 warning_matches = sum(
            normalize_text(keyword) in label_normalized
            for keyword in warning_keywords
        )

 warning_passed = warning_matches >= 4

    st.subheader("Verification results")

    result_rows = [
            {
                "Check": "Brand name",
                "Result": f"{status_icon(brand_passed)} "
                f"{'Match' if brand_passed else 'Review required'}",
                "Details": (
                    f"Similarity score: {brand_score:.0%}. "
                    "Capitalization differences are allowed."
                ),
            },
            {
                "Check": "Alcohol content",
                "Result": f"{status_icon(abv_passed)} "
                f"{'Match' if abv_passed else 'Mismatch'}",
                "Details": (
                    f"Application: {expected_abv:g}% | "
                    f"Label: {detected_abv + '%' if detected_abv else 'Not found'}"
                ),
            },
            {
                "Check": "Government warning",
                "Result": f"{status_icon(warning_passed)} "
                f"{'Required warning detected' if warning_passed else 'Missing or altered'}",
                "Details": (
                    f"Detected {warning_matches} of {len(warning_keywords)} required warning indicators."
                ),
            },
        ]

    st.table(result_rows)

    all_passed = brand_passed and abv_passed and warning_passed

    if all_passed:
            st.success("Label passed all automated checks.")
    else:
            st.warning(
                "One or more checks require review by a compliance agent."
            )

    with st.expander("Detected label details"):
            st.write(
                {
                    "Detected ABV": detected_abv,
                    "Brand similarity": round(brand_score, 3),
                    "Government warning found": warning_passed,
                }
            )

st.caption(
    "Prototype only. Final compliance decisions remain with authorized TTB personnel."
)
