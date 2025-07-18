# -*- coding: utf-8 -*-
"""autism_app2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Yn6LFUMMyfMiXdSfcl8DxyuzOBAvAPkV
"""

# autism_app.py (로컬 실행용)

import streamlit as st
from PIL import Image as PILImage
import os
import numpy as np
import io
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import gdown

MODEL_URL = "https://drive.google.com/uc?id=1wo5U_9ETRvM4psqVIKwUj2Y-mjX6sCMY"
MODEL_PATH = "autism_detection_model.h5"

if not os.path.exists(MODEL_PATH):
    with st.spinner("📦 모델 파일 다운로드 중..."):
        gdown.download(MODEL_URL, MODEL_PATH, quiet=False)
        st.success("모델 다운로드 완료!")


# === AQ-10 관련 ===
AQ10_QUESTIONS = {
    1: "S/he often notices small sounds when others do not",
    2: "S/he usually concentrates more on the whole picture, rather than the small details",
    3: "In a social group, s/he can easily keep track of several different people's conversations",
    4: "S/he finds it easy to go back and forth between different activities",
    5: "S/he doesn't know how to keep a conversation going with his/her peers",
    6: "S/he is good at social chit-chat",
    7: "When s/he is read a story, s/he finds it difficult to work out the character's intentions or feelings",
    8: "When s/he was in preschool, s/he used to enjoy playing games involving pretending with other children",
    9: "S/he finds it easy to work out what someone is thinking or feeling just by looking at their face",
    10: "S/he finds it hard to make new friends"
}

AUTISM_INDICATOR_QUESTIONS = [1, 5, 7, 10]
NON_AUTISM_INDICATOR_QUESTIONS = [2, 3, 4, 6, 8, 9]

response_map = {
    "Definitely Disagree": 0,
    "Slightly Disagree": 1,
    "Slightly Agree": 2,
    "Definitely Agree": 3,
}

# === 분석 함수 ===
def calculate_aq10_score(responses):
    score = 0
    for question_num, response in responses.items():
        if question_num in AUTISM_INDICATOR_QUESTIONS and response >= 2:
            score += 1
        elif question_num in NON_AUTISM_INDICATOR_QUESTIONS and response <= 1:
            score += 1
    return score

def interpret_aq10_score(score):
    if score >= 6:
        return "High risk - Consider specialist diagnostic assessment", score / 10
    elif score >= 4:
        return "Moderate risk - Monitor and consider further evaluation", score / 10
    else:
        return "Low risk - Typical development likely", score / 10

def suggest_followup(combined_prob):
    if combined_prob >= 0.6:
        return (
            "High combined risk — strongly recommend consulting a specialist for formal diagnosis. "
            "Please contact a developmental pediatrician, child psychologist, or neurologist for a full evaluation."
        )
    elif combined_prob >= 0.4:
        return (
            "Moderate combined risk — recommend monitoring and considering professional screening. "
            "You may consider discussing these results with your child's primary care provider or a child development specialist."
        )
    else:
        return (
            "Low combined risk — current findings suggest typical development. "
            "However, if there are concerns, it's always good to consult with a pediatrician."
        )

def predict_image_model(image_path, model_path='autism_detection_model.h5'):
    model = load_model(model_path, compile=False)
    img = image.load_img(image_path, target_size=(150, 150))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0
    return model.predict(img_array)[0][0]

def plot_prediction_confidence(probability, categories):
    confidence = [1 - probability, probability]
    plt.figure(figsize=(6, 4))
    bars = plt.bar(categories, confidence, color=['blue', 'red'])
    for bar, conf in zip(bars, confidence):
        plt.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height(), f'{conf:.2%}', ha='center', va='bottom')
    plt.ylim(0, 1)
    plt.ylabel('Probability')
    plt.title("Prediction Confidence")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def combine_predictions(image_prob, aq10_prob, image_weight=0.4, aq10_weight=0.6):
    return (image_prob * image_weight) + (aq10_prob * aq10_weight)

def plot_combined_analysis(image_prob, aq10_prob, combined_prob):
    categories = ['Image Analysis', 'AQ-10 Survey', 'Combined']
    probabilities = [image_prob, aq10_prob, combined_prob]
    plt.figure(figsize=(7, 4))
    bars = plt.bar(categories, probabilities, color=['skyblue', 'lightcoral', 'gold'])
    for bar, prob in zip(bars, probabilities):
        plt.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height(), f'{prob:.1%}', ha='center', va='bottom')
    plt.ylim(0, 1)
    plt.ylabel('Risk Probability')
    plt.axhline(y=0.6, color='red', linestyle='--')
    plt.axhline(y=0.4, color='orange', linestyle='--')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def generate_comprehensive_report(image_prob, aq10_responses, image_path, report_path='autism_report.pdf'):
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    aq10_score = calculate_aq10_score(aq10_responses)
    aq10_interp, aq10_prob = interpret_aq10_score(aq10_score)
    combined_prob = combine_predictions(image_prob, aq10_prob)
    recommendation = suggest_followup(combined_prob)

    # 첫 페이지: 이미지 분석
    elements.append(Paragraph("Image Model Prediction Report", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"According to the image model, the likelihood of being Autistic is {image_prob:.2%}.", styles['Normal']))
    elements.append(Spacer(1, 12))
    img_conf = plot_prediction_confidence(image_prob, ['Non_Autistic', 'Autistic'])
    elements.append(ReportImage(img_conf, width=400, height=250))
    try:
        img = PILImage.open(image_path)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        elements.append(Spacer(1, 12))
        elements.append(ReportImage(buf, width=250, height=250))
    except:
        elements.append(Paragraph("Image could not be loaded.", styles['Normal']))
    elements.append(PageBreak())

    # 두 번째 페이지: 설문 분석 + 사용자 응답표
    elements.append(Paragraph("Survey Model Prediction Report", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"According to the survey model, the likelihood of being Autistic is {aq10_prob:.2%}.", styles['Normal']))
    elements.append(Spacer(1, 12))
    aq_conf = plot_prediction_confidence(aq10_prob, ['Non_Autistic', 'Autistic'])
    elements.append(ReportImage(aq_conf, width=400, height=250))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("User Input Data", styles['Title']))
    table_data = [[f"A{num}_Score", score] for num, score in aq10_responses.items()]
    table_data += [["AQ10_Score", aq10_score], ["Interpretation", aq10_interp]]
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(PageBreak())

    # 세 번째 페이지: 종합 요약
    elements.append(Paragraph("Comprehensive Autism Risk Report", styles['Title']))
    elements.append(Spacer(1, 20))
    summary = f"""
    <b>Summary:</b><br/>
    Image model risk: {image_prob:.1%}<br/>
    AQ-10 score: {aq10_score}/10 ({aq10_interp})<br/>
    Combined risk: {combined_prob:.1%}<br/><br/>
    <b>Recommendation:</b> {recommendation}
    """
    elements.append(Paragraph(summary, styles['Normal']))
    elements.append(Spacer(1, 12))
    chart_buf = plot_combined_analysis(image_prob, aq10_prob, combined_prob)
    elements.append(ReportImage(chart_buf, width=400, height=250))

    try:
        img = PILImage.open(image_path)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        elements.append(Spacer(1, 24))
        elements.append(ReportImage(buf, width=250, height=250))
    except:
        elements.append(Paragraph("Image could not be loaded.", styles['Normal']))

    doc.build(elements)
    return report_path

# === Streamlit 앱 ===

st.set_page_config(page_title="Autism Risk App", layout="centered")
st.title("🧠 Autism Risk Assessment App")

uploaded_image = st.file_uploader("📷 Upload a face image", type=['jpg', 'jpeg', 'png'])
if uploaded_image:
    with open("temp_img.jpg", "wb") as f:
        f.write(uploaded_image.read())
    st.image("temp_img.jpg", caption="Uploaded Image", use_container_width=True)

st.subheader("🗘 AQ-10 Questionnaire")
aq10_responses = {}
for q_num, q_text in AQ10_QUESTIONS.items():
    response = st.radio(f"Q{q_num}: {q_text}", list(response_map.keys()), index=1, key=f"q{q_num}")
    aq10_responses[q_num] = response_map[response]

if st.button("🔍 Analyze and Generate Report") and uploaded_image:
    image_prob = predict_image_model("temp_img.jpg")
    aq10_score = calculate_aq10_score(aq10_responses)
    aq10_interp, aq10_prob = interpret_aq10_score(aq10_score)
    combined_prob = combine_predictions(image_prob, aq10_prob)
    recommendation = suggest_followup(combined_prob)

    st.markdown(f"**Image Risk**: {image_prob:.1%}")
    st.markdown(f"**AQ-10 Score**: {aq10_score}/10 → {aq10_interp}")
    st.markdown(f"**Combined Risk**: {combined_prob:.1%}")
    st.markdown(f"**Recommendation**: {recommendation}")

    report_file = generate_comprehensive_report(image_prob, aq10_responses, "temp_img.jpg")
    with open(report_file, "rb") as f:
        st.download_button("📄 Download PDF Report", f, file_name=report_file)
    st.success("Report generated successfully!")