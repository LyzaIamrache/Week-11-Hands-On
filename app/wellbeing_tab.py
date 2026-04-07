import re
from collections import Counter

import pandas as pd
import streamlit as st


DRUG_KEYWORDS = [
    "drug", "drugs", "weed", "marijuana", "cannabis", "alcohol", "drinking",
    "vodka", "beer", "wine", "cocaine", "heroin", "pills", "opioid", "opioids",
    "fentanyl", "smoking", "vape", "vaping", "high", "overdose", "relapse",
    "substance", "addiction", "addicted", "prescription misuse", "edible"
]

DISTRESS_KEYWORDS = [
    "stress", "stressed", "anxiety", "anxious", "depressed", "depression",
    "sad", "hopeless", "burnout", "burned out", "lonely", "panic", "scared",
    "tired", "can't sleep", "cannot sleep", "insomnia", "overwhelmed",
    "crying", "mental health", "exhausted", "isolated", "pressure"
]

HIGH_RISK_KEYWORDS = [
    "overdose", "suicide", "kill myself", "hurt myself", "self harm",
    "i want to die", "can't go on", "relapse badly", "blackout"
]

RESOURCE_LINKS = {
    "UMKC Counseling Services": "https://www.umkc.edu/student-affairs/counseling-services/",
    "UMKC Student Health": "https://www.umkc.edu/student-affairs/student-health-and-wellness/",
    "SAMHSA National Helpline": "https://www.samhsa.gov/find-help/national-helpline",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def find_matches(text: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw in text]


def assess_risk(user_text: str) -> dict:
    text = clean_text(user_text)

    drug_matches = find_matches(text, DRUG_KEYWORDS)
    distress_matches = find_matches(text, DISTRESS_KEYWORDS)
    high_risk_matches = find_matches(text, HIGH_RISK_KEYWORDS)

    score = len(drug_matches) * 2 + len(distress_matches) + len(high_risk_matches) * 5

    if high_risk_matches or score >= 5:
        level = "High"
    elif score >= 2:
        level = "Medium"
    else:
        level = "Low"

    categories = []
    if drug_matches:
        categories.append("Substance Use Risk")
    if distress_matches:
        categories.append("Emotional Distress")
    if not categories:
        categories.append("General Check-in")

    explanation_parts = []
    if drug_matches:
        explanation_parts.append(
            f"Possible substance-related signals detected: {', '.join(drug_matches)}."
        )
    if distress_matches:
        explanation_parts.append(
            f"Possible emotional distress signals detected: {', '.join(distress_matches)}."
        )
    if high_risk_matches:
        explanation_parts.append(
            f"Urgent high-risk language detected: {', '.join(high_risk_matches)}."
        )
    if not explanation_parts:
        explanation_parts.append(
            "No strong substance-related or distress-related signals were detected in the text."
        )

    return {
        "level": level,
        "score": score,
        "categories": categories,
        "drug_matches": drug_matches,
        "distress_matches": distress_matches,
        "high_risk_matches": high_risk_matches,
        "explanation": " ".join(explanation_parts),
    }



def generate_support_message(result: dict) -> str:
    level = result["level"]
    if level == "High":
        return (
            "This message suggests a higher level of concern. Please consider contacting a trusted person, "
            "campus counseling, or emergency support if the situation feels urgent."
        )
    if level == "Medium":
        return (
            "This message may reflect stress or possible substance-related concern. Early support from a counselor, "
            "student support office, or health professional may help."
        )
    return (
        "No strong high-risk signals were detected. Wellness and counseling resources may still be helpful if needed."
    )



def init_history() -> None:
    if "wellbeing_history" not in st.session_state:
        st.session_state.wellbeing_history = []



def save_result(user_text: str, result: dict) -> None:
    st.session_state.wellbeing_history.append(
        {
            "text": user_text,
            "risk_level": result["level"],
            "score": result["score"],
            "categories": ", ".join(result["categories"]),
        }
    )



def summarize_history() -> dict:
    history = st.session_state.get("wellbeing_history", [])
    if not history:
        return {"Low": 0, "Medium": 0, "High": 0}
    counter = Counter(item["risk_level"] for item in history)
    return {level: counter.get(level, 0) for level in ["Low", "Medium", "High"]}



def render_wellbeing_tab() -> None:
    init_history()

    st.header("💙 Well-being & Substance Risk Assistant")
    st.write(
        "Analyze free-text student concerns for possible emotional distress or substance-use risk signals. "
        "The output is educational and supportive, not a medical diagnosis."
    )

    with st.expander("What this feature does", expanded=True):
        st.markdown(
            """
            - Detects possible risk language in student text
            - Provides an explainable risk level: Low, Medium, or High
            - Suggests support-oriented next steps
            - Builds a small dashboard for demo and presentation use
            """
        )

    example_text = st.selectbox(
        "Example prompts",
        [
            "Custom input",
            "I feel overwhelmed and I have been drinking a lot lately.",
            "My friend may be using drugs and I do not know how to help.",
            "I am stressed about exams and I cannot sleep.",
        ],
        index=0,
    )

    default_text = "" if example_text == "Custom input" else example_text
    user_text = st.text_area(
        "Enter a student message or concern",
        value=default_text,
        placeholder="Example: I feel overwhelmed and I have been drinking a lot lately.",
        height=150,
    )

    if st.button("Analyze Message", type="primary"):
        if not user_text.strip():
            st.warning("Please enter some text first.")
        else:
            result = assess_risk(user_text)
            save_result(user_text, result)

            c1, c2, c3 = st.columns(3)
            c1.metric("Risk Level", result["level"])
            c2.metric("Score", result["score"])
            c3.metric("Categories", len(result["categories"]))

            st.subheader("Explainability")
            st.write(result["explanation"])
            st.write(f"**Detected categories:** {', '.join(result['categories'])}")

            if result["drug_matches"]:
                st.write(f"**Drug-related keywords:** {', '.join(result['drug_matches'])}")
            if result["distress_matches"]:
                st.write(f"**Distress-related keywords:** {', '.join(result['distress_matches'])}")
            if result["high_risk_matches"]:
                st.write(f"**High-risk keywords:** {', '.join(result['high_risk_matches'])}")

            st.subheader("Suggested Response")
            st.info(generate_support_message(result))

            if result["level"] == "High":
                st.error(
                    "High-risk language detected. In a production deployment, this could trigger a referral or alert workflow."
                )

    st.divider()
    st.subheader("Campus / Support Resources")
    for name, link in RESOURCE_LINKS.items():
        st.markdown(f"- [{name}]({link})")

    st.divider()
    st.subheader("Simple Monitoring Dashboard")
    summary = summarize_history()
    c1, c2, c3 = st.columns(3)
    c1.metric("Low", summary["Low"])
    c2.metric("Medium", summary["Medium"])
    c3.metric("High", summary["High"])

    summary_df = pd.DataFrame({"risk_level": list(summary.keys()), "count": list(summary.values())})
    if summary_df["count"].sum() > 0:
        st.bar_chart(summary_df.set_index("risk_level"))

    if st.session_state.wellbeing_history:
        st.dataframe(pd.DataFrame(st.session_state.wellbeing_history), use_container_width=True)
