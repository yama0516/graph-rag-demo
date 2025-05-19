import streamlit as st
from rag_logic import run_graph_rag  # ロジックをインポート
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Graph RAG Demo")
st.title("Graph RAG デモ")

# パスワード認証
password = st.text_input("パスワードを入力してください", type="password")
if password != os.getenv("APP_PASSWORD"):
    st.warning("正しいパスワードを入力してください")
    st.stop()

# 質問フォーム
query = st.text_input("質問を入力してください")

if st.button("実行") and query:
    with st.spinner("回答生成中..."):
        try:
            result = run_graph_rag(query)
            st.success("✅ 回答:")
            st.write(result)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")