import pytest
from app.ai.preprocessing import preprocessor, TextPreprocessor

def test_html_removal_and_entity_unescaping():
    raw_html = (
        "<p>Dear Support Team,</p><br/>"
        "<div>I was <b>double charged</b> on invoice INV-9901 &amp; need a refund of $149.00!</div>"
        "<script>alert('malicious')</script><!-- internal note -->"
    )
    res = preprocessor.preprocess(raw_html)
    processed = res["processed_text"]

    assert "<p>" not in processed
    assert "<b>" not in processed
    assert "<script>" not in processed
    assert "alert" not in processed
    assert "internal note" not in processed
    assert "&amp;" not in processed
    assert "&" in processed
    assert "INV-9901" in processed
    assert "$149.00" in processed
    assert res["original_text"] == raw_html

def test_email_signature_removal():
    email_text = (
        "My account has been locked and I cannot access my transactions.\n\n"
        "Best regards,\n"
        "John Doe\n"
        "Senior Analyst, FinCorp\n"
        "Phone: +1-555-0199\n"
        "Sent from my iPhone"
    )
    res = preprocessor.preprocess(email_text)
    processed = res["processed_text"]

    assert "account has been locked" in processed
    assert "Sent from my iPhone" not in processed
    assert "Senior Analyst" not in processed

def test_quoted_reply_removal():
    thread_text = (
        "I still have not received my replacement order #ORD-8821.\n\n"
        "On Mon, Mar 2, 2026 at 10:00 AM Customer Support wrote:\n"
        "> Dear Customer,\n"
        "> We have dispatched your item via priority courier.\n"
        "> Tracking #EXP-9912"
    )
    res = preprocessor.preprocess(thread_text)
    processed = res["processed_text"]

    assert "#ORD-8821" in processed
    assert "On Mon, Mar 2, 2026" not in processed
    assert "> Dear Customer" not in processed
    assert "dispatched your item" not in processed

def test_unnecessary_whitespace_and_normalization():
    messy_text = "Urgent     issue\t\twith  login.\n\n\n\n\nPlease    reset   password.\n\n"
    res = preprocessor.preprocess(messy_text)
    processed = res["processed_text"]

    assert "     " not in processed
    assert "\t" not in processed
    assert "\n\n\n" not in processed
    assert "Urgent issue with login." in processed
    assert "Please reset password." in processed

def test_url_cleaning_and_punctuation_preservation():
    text_with_urls = (
        "Check error log at https://click.track.service.com/trace?id=84920&user=99281 !!!!!!! "
        "Will I get my $500.00 refund back??? Transaction TXN-8849 is failing."
    )
    res = preprocessor.preprocess(text_with_urls)
    processed = res["processed_text"]

    assert "https://click.track" not in processed
    assert "[URL]" in processed
    # Repetitive punctuation compressed without destroying semantic marks
    assert "!!!!!!" not in processed
    assert "!" in processed
    assert "???" not in processed
    assert "?" in processed
    # Preserves dollar amount and transaction hyphen
    assert "$500.00" in processed
    assert "TXN-8849" in processed

def test_duplicate_text_removal():
    repeated_text = (
        "Payment was deducted twice. Payment was deducted twice. "
        "Please reverse the charge immediately."
    )
    res = preprocessor.preprocess(repeated_text)
    processed = res["processed_text"]

    # Consecutive identical sentence deduplicated
    assert processed.count("Payment was deducted twice.") == 1
    assert "Please reverse the charge immediately." in processed

def test_empty_and_whitespace_text():
    res_none = preprocessor.preprocess(None)
    assert res_none["is_empty"] is True
    assert res_none["processed_text"] == ""
    assert res_none["original_text"] == ""

    res_spaces = preprocessor.preprocess("   \t  \n  ")
    assert res_spaces["is_empty"] is True
    assert res_spaces["processed_text"] == ""

def test_language_detection():
    en_res = preprocessor.preprocess("I would like to file a complaint regarding an unexpected billing fee on my account.")
    assert en_res["language"] == "en"
    assert en_res["language_name"] == "English"
    assert en_res["language_confidence"] >= 0.70

    es_res = preprocessor.preprocess("Tengo un problema con el pago de mi cuenta y necesito un reembolso urgente.")
    assert es_res["language"] == "es"
    assert es_res["language_name"] == "Spanish"

def test_both_original_and_processed_text_retained():
    original = "<b>Urgent:</b> System outage down on https://api.prod.io   at $10,000/hr loss! Sent from my Android"
    res = preprocessor.preprocess(original)

    assert res["original_text"] == original
    assert res["processed_text"] != original
    assert "<b>" not in res["processed_text"]
    assert "Sent from my Android" not in res["processed_text"]
    assert "$10,000" in res["processed_text"]
    assert res["original_length"] == len(original)
    assert res["processed_length"] == len(res["processed_text"])
