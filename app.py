import streamlit as st
from PIL import Image
from ocr.ocr_engine import extract_text_from_image
import re
import pandas as pd
import matplotlib.pyplot as plt


# -------------------------------
# Session State Initialization
# -------------------------------
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# -------------------------------
# Convert Words to Number
# -------------------------------
def words_to_number(words):
    number_dict = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "hundred": 100, "thousand": 1000
    }

    words = words.lower().split()
    total = 0
    current = 0

    for word in words:
        if word not in number_dict:
            continue

        value = number_dict[word]

        if value == 100:
            current *= 100
        elif value == 1000:
            current *= 1000
            total += current
            current = 0
        else:
            current += value

    total += current
    return total

# -------------------------------
# Extract Amount (Improved)
# -------------------------------
def extract_amount(text):

    # 1️⃣ Try amount in words
    words_match = re.search(r'Rupees (.*?) Only', text, re.IGNORECASE)
    if words_match:
        return words_to_number(words_match.group(1))

    # 2️⃣ Extract from TOTAL line (with decimals)
    total_match = re.search(
        r'TOTAL[^\d]*([\d,]+\.\d{2})',
        text,
        re.IGNORECASE
    )
    if total_match:
        return float(total_match.group(1).replace(",", ""))

    # 3️⃣ Fallback: largest decimal number
    numbers = re.findall(r'\d+\.\d{2}', text)
    if numbers:
        cleaned = [float(num.replace(",", "")) for num in numbers]
        return max(cleaned)

    return "Amount not found"

# -------------------------------
# Extract Merchant (Improved)
# -------------------------------
def extract_merchant(text):
    lines = text.split("\n")

    # Usually merchant is in first 3 lines
    for line in lines[:3]:
        if len(line.strip()) > 3:
            return line.strip()

    return "Merchant not found"

# -------------------------------
# Extract Date (Improved)
# -------------------------------
def extract_date(text):

    # Format: 24/04/2024
    match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', text)
    if match:
        return match.group()

    # Format: 30 Nov 2022
    match = re.search(r'\d{1,2}\s[A-Za-z]{3}\s\d{4}', text)
    if match:
        return match.group()

    return "Date not found"

# -------------------------------
# Extract Payment Method
# -------------------------------
def extract_payment_method(text):
    match = re.search(
        r'(Debit Card|Credit Card|UPI|Net Banking|Cash)',
        text,
        re.IGNORECASE
    )
    if match:
        return match.group()
    return "Not detected"

# -------------------------------
# Categorization
# -------------------------------
def categorize_transaction(merchant):
    merchant = merchant.lower()

    if "google" in merchant:
        return "Entertainment"
    elif "swiggy" in merchant or "zomato" in merchant:
        return "Food"
    elif "restaurant" in merchant or "hotel" in merchant:
        return "Food"
    elif "amazon" in merchant or "flipkart" in merchant:
        return "Shopping"
    else:
        return "Others"

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("💰 AI Financial Advisor")
st.write("Upload a payment screenshot to extract transaction details")

uploaded_file = st.file_uploader(
    "Upload Payment Screenshot",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:

    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Screenshot", use_column_width=True)

    with st.spinner("Extracting text using OCR..."):
        extracted_text = extract_text_from_image(image)

    st.subheader("📄 Extracted Text:")
    st.text(extracted_text)

    # Extract details
    amount = extract_amount(extracted_text)
    merchant = extract_merchant(extracted_text)
    date = extract_date(extracted_text)
    payment_method = extract_payment_method(extracted_text)
    category = categorize_transaction(merchant)

    # Display detected values
    st.subheader("💵 Detected Amount:")
    st.write(amount)

    st.subheader("🏪 Merchant:")
    st.write(merchant)

    st.subheader("📅 Date:")
    st.write(date)

    st.subheader("💳 Payment Method:")
    st.write(payment_method)

    # Create transaction dynamically
    transaction = {
        "amount": amount,
        "merchant": merchant,
        "date": date,
        "payment_method": payment_method,
        "category": category
    }

    st.subheader("📊 Structured Transaction Data")
    st.json(transaction)

    # Add transaction button (prevents duplicates)
    if st.button("Add Transaction"):
        st.session_state.transactions.append(transaction)
        st.success("Transaction Added Successfully!")

# -------------------------------
# Transaction History
# -------------------------------
st.subheader("📜 Transaction History")

if st.session_state.transactions:
    for i, txn in enumerate(st.session_state.transactions):
        st.write(f"Transaction {i+1}")
        st.json(txn)
else:
    st.write("No transactions yet.")
# -------------------------------
# Expense Summary Dashboard
# -------------------------------

if st.session_state.transactions:

    st.header("📊 Expense Summary Dashboard")

    df = pd.DataFrame(st.session_state.transactions)

    # Ensure amount is numeric
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # 🔹 Total Spending
    total_spent = df["amount"].sum()
    st.subheader("💰 Total Spending")
    st.write(f"₹ {total_spent:.2f}")

    # 🔹 Category-wise Spending
    category_summary = df.groupby("category")["amount"].sum()

    st.subheader("📂 Category-wise Spending")
    st.write(category_summary)

    # 🔹 Pie Chart
    st.subheader("🥧 Spending Distribution")

    fig, ax = plt.subplots()
    ax.pie(
        category_summary,
        labels=category_summary.index,
        autopct="%1.1f%%"
    )
    ax.axis("equal")

    st.pyplot(fig)

    # -------------------------------
    # Smart Financial Advice
    # -------------------------------

    st.header("🧠 AI Financial Advice")

    highest_category = category_summary.idxmax()
    highest_amount = category_summary.max()

    if highest_category == "Food":
        st.warning(
            f"You are spending ₹ {highest_amount:.2f} mostly on Food. "
            "Consider reducing outside dining to improve savings."
        )

    elif highest_category == "Entertainment":
        st.warning(
            f"Entertainment spending is ₹ {highest_amount:.2f}. "
            "Review subscriptions and non-essential expenses."
        )

    elif highest_category == "Shopping":
        st.warning(
            f"You spent ₹ {highest_amount:.2f} on Shopping. "
            "Try budgeting discretionary purchases."
        )

    else:
        st.info(
            f"Your highest spending is in '{highest_category}' category. "
            "Monitor this category to maintain financial balance."
        )

    # 🔹 Savings Suggestion
    suggested_savings = total_spent * 0.2
    st.success(
        f"If you reduce spending by just 20%, "
        f"you could save approximately ₹ {suggested_savings:.2f}."
    )
