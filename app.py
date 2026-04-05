import streamlit as st
import pandas as pd
import re
import json
from datetime import datetime
from groq import Groq

api_key = st.text_input("Groq API Key", type="password", value="")
client = Groq(api_key=api_key) if api_key else None

st.set_page_config(page_title="inVision U AI Scorer", page_icon="🔍", layout="wide")

# Немного стиля
st.markdown("""
<style>
    .main {background-color: #0E1117; color: #FAFAFA;}
    .stButton>button {
        background-color: #00C853 !important; 
        color: white !important; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 3.2em;
    }
    .stButton>button:hover {background-color: #00A140 !important;}
    h1, h2, h3 {color: #00C853 !important;}
</style>
""", unsafe_allow_html=True)

st.title("🔍 inVision U — AI система отбора")
st.subheader("Decentrathon 5.0 | Трек AI inDrive")

st.write("### Введи текст анкеты + эссе кандидата")
text = st.text_area("Текст", height=380, placeholder="Вставь сюда всё...")

# ====================== АНАЛИЗ ЭССЕ ======================
def analyze_essay(text: str):
    prompt = f"""
Ты — строгий член приёмной комиссии inVision U. 
Оцени эссе кандидата честно и внимательно.

Текст:
{text}

Анализируй максимально критично. Современные ИИ-тексты часто имеют следующие признаки:
- Слишком идеальная структура и логическая последовательность
- Шаблонные переходы ("в заключение", "таким образом", "следует отметить", "подводя итог")
- Отсутствие настоящих живых эмоций и уникальных личных деталей
- Слишком формальный или "книжный" стиль для школьника/студента
- Предсказуемый ритм предложений и излишняя гладкость
- Общие фразы вместо конкретных примеров из жизни
- Отсутствие ошибок, опечаток или небрежностей, которые обычно есть в человеческих текстах
- Чрезмерное использование сложных слов и фраз, которые не соответствуют уровню кандидата
- Слишком "идеальный" и безличный тон, который не отражает индивидуальность автора
- Отсутствие уникальных, неожиданных мыслей или идей, которые обычно возникают в человеческом творчестве

Также скажи, похоже ли это на текст, написанный ИИ.

Ответь только в формате JSON:

{{
  "leadership": число от 0 до 100,
  "motivation": число от 0 до 100,
  "growth": число от 0 до 100,
  "total_score": число от 0 до 100,
  "detect": "HUMAN" или "AI",
  "explanation": "Короткое объяснение (2-4 предложения)"
}}
"""

    try:
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=600
        )
        response = chat.choices[0].message.content.strip()

        # Ищем JSON в ответе
        json_match = re.search(r'\{[\s\S]*?\}', response)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            return None
    except:
        return None

if st.button("Анализировать кандидата", type="primary", use_container_width=True):
    if text.strip():
        with st.spinner("Анализирую эссе..."):
            result = analyze_essay(text)

        if result:
            total = result.get("total_score", 0)
            leadership = result.get("leadership", 0)
            motivation = result.get("motivation", 0)
            growth = result.get("growth", 0)
            detect = result.get("detect", "HUMAN")
            explanation = result.get("explanation", "Нет объяснения")

            # Если ИИ — полностью обнуляем баллы
            if detect == "AI":
                total = 0
                leadership = 0
                motivation = 0
                growth = 0
                st.error("**Детект ИИ: ChatGPT / ИИ** — Баллы обнулены")
            else:
                st.success("**Детект ИИ: Аутентично (человек)**")

            st.success(f"**ИТОГОВЫЙ SCORE: {total}/100**")

            col1, col2, col3 = st.columns(3)
            col1.metric("Лидерство", f"{leadership}%")
            col2.metric("Мотивация", f"{motivation}%")
            col3.metric("Рост", f"{growth}%")

            st.write("**Объяснение:**")
            st.info(explanation)

            # Сохранение в историю
            if "candidates" not in st.session_state:
                st.session_state.candidates = []
            st.session_state.candidates.append({
                "Кандидат": f"Кандидат {len(st.session_state.candidates)+1}",
                "Score": total,
                "Лидерство": leadership,
                "Мотивация": motivation,
                "Рост": growth,
                "Детект": detect,
                "Время": datetime.now().strftime("%H:%M")
            })
        else:
            st.error("Не получилось обработать ответ от Groq. Попробуй ещё раз.")
    else:
        st.warning("Сначала введи текст эссе!")

# Таблица в боковой панели
st.sidebar.header("📋 Рейтинг кандидатов")

if "candidates" in st.session_state and st.session_state.candidates:
    df = pd.DataFrame(st.session_state.candidates)
    st.sidebar.dataframe(df.sort_values("Score", ascending=False), use_container_width=True)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.sidebar.button("Сбросить список"):
            st.session_state.candidates = []
            st.rerun()
    with col2:
        if st.sidebar.button("Экспорт в Excel"):
            df.to_excel("candidates.xlsx", index=False)
            st.sidebar.success("Файл сохранён!")
else:
    st.sidebar.info("Пока нет анализов")

st.caption("Прототип для inVision U • Groq LLM")