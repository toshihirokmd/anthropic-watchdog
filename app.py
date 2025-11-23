import streamlit as st
import google.generativeai as genai
import os
import glob
import re # リンク書き換え用

# --- 設定 ---
st.set_page_config(page_title="Anthropic Watchdog", page_icon="🛡️")
st.title("🛡️ Anthropic Watchdog (Pro)")

# SecretsからAPIキーを読み込む
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # 予備: サイドバー入力
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.warning("👈 APIキーが必要です（Secrets設定推奨）")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-flash-latest')

# --- 便利関数: リンクを別タブで開く ---
def make_links_open_new_tab(text):
    # [text](url) -> <a href="url" target="_blank">text</a>
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    replacement = r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>'
    return re.sub(pattern, replacement, text)

# --- データ読み込み ---
list_of_files = glob.glob('data/*.txt')
if not list_of_files:
    st.error("データがありません。GitHub Actionsを実行してください。")
    st.stop()

latest_file = max(list_of_files, key=os.path.getctime)
file_date = os.path.basename(latest_file).replace('.txt', '')

with open(latest_file, "r", encoding="utf-8") as f:
    news_content = f.read()

st.info(f"📅 取得データ: {file_date}")

# --- UI ---
tab1, tab2 = st.tabs(["🛠 技術レポート", "💬 開発チャット"])

# === タブ1: エンジニア向け要約 ===
with tab1:
    st.write("開発への影響を分析します。")
    if st.button("🚀 分析開始"):
        with st.spinner("仕様変更やCookbookを解析中..."):
            prompt = f"""
            あなたはAnthropic製品のエキスパートエンジニアです。
            以下の最新情報（GitHub更新やブログ）を読み解き、開発者が知るべき点をレポートしてください。
            
            【出力フォーマット】
            1. **🚨 Breaking Changes / 注意点**: SDKの仕様変更や非推奨化など、コード修正が必要なもの。
            2. **💡 Cookbook / 実装例**: 新しく追加されたサンプルコード（レシピ）の内容と活用法。
            3. **🆕 New Features**: 新機能の概要。
            
            データ:
            {news_content}
            """
            response = model.generate_content(prompt)
            # リンクを別タブ化して表示
            st.markdown(make_links_open_new_tab(response.text), unsafe_allow_html=True)

# === タブ2: チャット ===
with tab2:
    st.write("実装方法などを相談できます。")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        # 初期コンテキスト
        st.session_state.chat_history.append({
            "role": "user",
            "parts": [f"以下の技術情報を前提知識として覚えてください。\n\n{news_content}"]
        })
        st.session_state.chat_history.append({
            "role": "model",
            "parts": ["了解しました。技術的な質問にお答えします。"]
        })

    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []

    # 履歴表示
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(make_links_open_new_tab(msg["content"]), unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])

    if prompt := st.chat_input("例: Cookbookに追加されたPDF解析の実装方法は？"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.display_messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("🤖 コードや仕様を確認中..."):
                try:
                    chat = model.start_chat(history=st.session_state.chat_history)
                    response = chat.send_message(prompt)
                    
                    converted_text = make_links_open_new_tab(response.text)
                    st.markdown(converted_text, unsafe_allow_html=True)
                    
                    # 履歴保存
                    st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
                    st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
                    st.session_state.display_messages.append({"role": "assistant", "content": response.text})
                    
                except Exception as e:
                    st.error(f"エラー: {e}")
