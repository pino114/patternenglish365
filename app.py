import streamlit as st
import openai
import os
import sqlite3
from gtts import gTTS
import base64
from datetime import datetime

openai.api_key = st.secrets["OPENAI_API_KEY"]

# SQLite DB 초기화
def init_db():
    conn = sqlite3.connect("sentences.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sentences (user TEXT, sentence TEXT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="패턴영어365 AI 피드백", page_icon="📘")
st.title("📘 패턴영어365 AI 회화 & 피드백 파트너")

username = st.text_input("사용자 이름을 입력해 주세요:", "guest")
pattern = st.text_input("오늘의 패턴 예시:", "I'm good at ~")

# AI 질문 버튼
if st.button("AI가 먼저 질문해줘!"):
    system_prompt = f"You are a friendly English conversation partner. Please ask the user a question using the pattern: '{pattern}'."
    with st.spinner("질문을 생성 중입니다..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please ask me a question using today's English pattern."}
                ]
            )
            ai_question = response.choices[0].message.content
            st.success("🤖 AI 질문:")
            st.markdown(ai_question)
        except Exception as e:
            st.error(f"오류 발생: {e}")

user_sentence = st.text_area("패턴을 활용한 나만의 문장을 입력해 보세요:", height=100)

# 피드백 요청
if st.button("AI에게 피드백 받기"):
    if not user_sentence:
        st.warning("문장을 입력해 주세요.")
    else:
        with st.spinner("AI가 분석 중입니다..."):
            prompt = f"""\
The user is learning the English pattern: \"{pattern}\"\n
They wrote this sentence: \"{user_sentence}\"\n
\n
Please do the following:\n
1. Evaluate the sentence's naturalness.\n
2. Suggest two alternative natural sentences.\n
3. Translate the sentence into Korean.\n
4. Explain in Korean how this sentence can be used in conversation.\n"""
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful English tutor who explains clearly in Korean."},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = response.choices[0].message.content

                st.success("✅ AI 피드백 결과")
                st.markdown(result)

                conn = sqlite3.connect("sentences.db")
                c = conn.cursor()
                c.execute("INSERT INTO sentences (user, sentence) VALUES (?, ?)", (username, user_sentence))
                conn.commit()
                conn.close()

                tts = gTTS(text=user_sentence, lang='en')
                tts.save("temp.mp3")
                with open("temp.mp3", "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")

            except Exception as e:
                st.error(f"오류 발생: {e}")

# 복습
if st.checkbox("🧠 저장된 문장 복습하기"):
    st.markdown("### 📚 내가 만든 문장 모음:")
    conn = sqlite3.connect("sentences.db")
    c = conn.cursor()
    c.execute("SELECT sentence, created FROM sentences WHERE user = ? ORDER BY created DESC", (username,))
    rows = c.fetchall()
    for i, (sentence, created) in enumerate(rows, 1):
        st.markdown(f"**{i}.** {sentence} _(입력일: {created})_")
    conn.close()

st.markdown("---")
st.caption("Made with 💬 by 패턴영어365 x AI")