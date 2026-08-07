# AI-Powered Alcohol Label Verification

A prototype application that uses OCR and automated validation to compare information from an alcohol label image against application information.

## Overview

The application allows a user to:

- Enter an expected brand name.
- Enter the expected Alcohol by Volume (ABV).
- Upload an alcohol label image.
- Automatically extract visible text from the label using OCR.
- Review and correct the OCR-extracted text.
- Verify the brand name.
- Verify the alcohol content.
- Detect required government-warning indicators.
- Display clear pass, mismatch, or review-required results.

## Technology Used

- Python
- Streamlit
- EasyOCR
- Pillow
- NumPy

## How It Works

1. The user enters application information.
2. The user uploads a PNG, JPG, or JPEG label image.
3. EasyOCR extracts text from the uploaded image.
4. The extracted text is normalized for comparison.
5. The application compares the expected brand name with the label text.
6. The application extracts and compares the ABV percentage.
7. Government-warning indicators are checked in the detected label text.
8. Verification results are displayed to the user.

## Installation

Install the required Python packages:

    pip install -r requirements.txt

## Run the Application

From the project directory, run:

    streamlit run app.py

Then open the local Streamlit URL displayed in the terminal.

## Verification Results

The prototype reports results for:

- Brand name
- Alcohol content
- Required government warning

A failed automated check is flagged for human review rather than treated as a final compliance decision.

## Assumptions and Limitations

- OCR accuracy depends on image quality, orientation, font, and label design.
- Brand-name matching uses normalized text similarity.
- Government-warning verification uses required warning indicators to tolerate minor OCR errors.
- The application is a prototype and does not make final regulatory compliance decisions.
- Final compliance decisions remain with authorized TTB personnel.

## Future Improvements

Potential enhancements include:

- More advanced fuzzy matching.
- Improved OCR preprocessing.
- Additional regulatory validation rules.
- Persistent storage of verification results.
- Audit logging.
- API integration with application data.
- Cloud deployment and authentication.
