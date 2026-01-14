import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os

# ==========================================
# 1. 系統設定
# ==========================================
st.set_page_config(layout="wide", page_title="金門智慧商旅 v3.0 (雲端版)", page_icon="🏝️")

# 預設檔案名稱 (當使用者沒有上傳檔案時使用)
DEFAULT_DATA_FILE = 'history_data.csv'
DEFAULT_REVIEW_FILE = '民宿數據.xlsx - 客戶評價.csv'

# ==========================================
# 2. 資料讀取模組 (升級版：支援上傳)
# ==========================================

def load_data(uploaded_file, default_file):
    """
    通用讀取函數：
    1. 如果使用者有上傳 -> 讀取上傳檔
    2. 如果沒上傳 -> 嘗試讀取本地預設檔
    3. 如果都沒有 -> 回傳空表
    """
    if uploaded_file is not None:
        try:
            # 讀取上傳的 CSV
            df = pd.read_csv(uploaded_file)
            # 如果欄位包含 '日期'，強制轉為 datetime 格式
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
            return df
        except Exception as e:
            st.error(f"檔案讀取失敗: {e}")
            return pd.DataFrame()

    elif os.path.exists(default_file):
        df = pd.read_csv(default_file)
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
        return df
    else:
        return pd.DataFrame()

# ==========================================
# 3. Gemini AI 模組
# ==========================================
def ask_gemini(prompt, api_key):
    if not api_key: return "⚠️ 請先輸入 API Key"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"連線錯誤: {str(e)}"

# ==========================================
# 4. 介面層 (UI)
# ==========================================

with st.sidebar:
    st.title("🏝️ 數位經理人 Pro")

    page = st.radio("功能選單", [
        "A. 顧客心聲洞察",
        "B. 營運戰情室 (分析)",
        "C. 資料輸入 (記帳)"
    ])

    st.markdown("---")
    st.subheader("📂 資料匯入")
    st.caption("若無上傳，將使用預設資料庫")

    # 這裡就是你要的功能：上傳 CSV
    upload_reviews = st.file_uploader("上傳評價 CSV (取代頁面 A)", type=['csv'])
    upload_history = st.file_uploader("上傳營收 CSV (取代頁面 B)", type=['csv'])

    st.markdown("---")
    api_key = st.text_input("Gemini API Key", type="password")

# --- 頁面 A: 顧客心聲 ---
if page == "A. 顧客心聲洞察":
    st.header("🗣️ 顧客評價分析")

    # 呼叫讀取函數 (優先讀取上傳檔)
    df_reviews = load_data(upload_reviews, DEFAULT_REVIEW_FILE)

    if df_reviews.empty:
        st.warning("⚠️ 目前沒有資料。請上傳 `客戶評價.csv` 或確認預設檔案存在。")
    else:
        st.success(f"✅ 已載入 {len(df_reviews)} 筆評價資料")

        # 資料處理與圖表
        def parse_tags(series):
            all_tags = []
            for item in series:
                if pd.isna(item): continue
                item = str(item).replace('、', ',').replace('，', ',')
                tags = [t.strip() for t in item.split(',') if t.strip() not in ['无', '無', '無提及']]
                all_tags.extend(tags)
            return all_tags

        pros = parse_tags(df_reviews['民宿優點'])
        cons = parse_tags(df_reviews['民宿缺點'])

        if '同行類型' in df_reviews.columns:
            cust_type = df_reviews['同行類型'].value_counts()

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("客群分佈")
                fig = px.pie(values=cust_type.values, names=cust_type.index, hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                from collections import Counter
                st.subheader("主要痛點分析")
                common_cons = Counter(cons).most_common(5)
                if common_cons:
                    df_c = pd.DataFrame(common_cons, columns=['缺點', '次數'])
                    fig = px.bar(df_c, x='次數', y='缺點', orientation='h', color='次數', color_continuous_scale='Reds')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("目前沒有顯著的負評數據。")

            # AI 分析按鈕
            if st.button("呼叫 AI 分析評價"):
                prompt = f"根據評價數據：客群主要是{cust_type.index[0]}，最大缺點是{Counter(cons).most_common(3)}。請給出3點改善建議。"
                st.markdown(ask_gemini(prompt, api_key))
        else:
            st.error("CSV 格式錯誤：缺少 '同行類型' 欄位。")

# --- 頁面 B: 營運戰情室 ---
elif page == "B. 營運戰情室 (分析)":
    st.header("📈 營運趨勢預測")

    # 呼叫讀取函數
    df_trends = load_data(upload_history, DEFAULT_DATA_FILE)

    if df_trends.empty:
        st.warning("⚠️ 無數據。請上傳歷史營收 CSV 或先在頁面 C 輸入資料。")
    else:
        # 簡單檢查必要欄位
        required_cols = ['日期', '營收', '住房率']
        if all(col in df_trends.columns for col in required_cols):
            # 數據預測
            df_trends['營收預測(MA7)'] = df_trends['營收'].rolling(7).mean()

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_trends['日期'], y=df_trends['營收'], name='實際營收', marker_color='#A0C4FF'))
            fig.add_trace(go.Scatter(x=df_trends['日期'], y=df_trends['營收預測(MA7)'], name='趨勢(MA7)', line=dict(color='#FF6B6B')))
            st.plotly_chart(fig, use_container_width=True)

            # ... (以上程式碼不變)

            if st.button("AI 營運診斷"):
                # 1. 準備數據摘要
                last_month = df_trends.tail(30)
                summary = f"近30天營收總和: {last_month['營收'].sum()}, 平均住房率: {last_month['住房率'].mean():.2f}"

                # 2. 獲取當前月份，作為「外部環境」的判斷依據
                current_date = datetime.now()
                current_month = current_date.month

                # 3. 超級 Prompt (這就是核心差異！)
                prompt = f"""
                角色設定：你是一位精通「金門觀光市場」的資深經營顧問，具備敏銳的市場嗅覺。

                現況背景：
                - 現在時間是：{current_month} 月 (請結合金門此時的氣候特性、霧季風險、或節慶活動來分析)。
                - 店家經營數據：{summary}。

                任務目標：
                請不需要客套，直接給出 3 點經營策略，必須包含：
                1. 【外部機會/威脅】：結合現在的月份(例如霧季、暑假、連假、東北季風)，預測接下來人流變化。
                2. 【庫存與備貨】：根據上述預測，針對早餐食材或備品提出建議。
                3. 【行銷亮點】：針對這個季節的遊客痛點(例如太冷、怕沒飛機)，提出一個暖心服務建議。

                請用繁體中文，條列式回答。
                """

                # 呼叫 Gemini
                st.markdown(ask_gemini(prompt, api_key))
        else:
            st.error(f"CSV 格式錯誤。必須包含欄位：{required_cols}")

# --- 頁面 C: 資料輸入 ---
elif page == "C. 資料輸入 (記帳)":
    st.header("📝 每日營運紀錄")
    # 如果是上傳的檔案，這裡是唯讀的，只有本地檔案模式才能寫入
    if upload_history is not None:
        st.info("💡 正在檢視「上傳檔案」模式，無法在此新增資料。請重新整理頁面並使用預設模式以啟用寫入功能。")
    else:
        with st.form("entry"):
            d = st.date_input("日期", datetime.today())
            r = st.number_input("營收", step=100)
            o = st.number_input("住房率 (0-1)", max_value=1.0, step=0.01)
            c = st.number_input("轉換率", step=0.1)
            if st.form_submit_button("儲存"):
                new_row = pd.DataFrame([[d, r, o, c]], columns=['日期', '營收', '住房率', '轉換率'])
                # 寫入邏輯同前一版
                hdr = not os.path.exists(DEFAULT_DATA_FILE)
                new_row.to_csv(DEFAULT_DATA_FILE, mode='a', header=hdr, index=False)
                st.success("已儲存！請至戰情室查看。")