
# v2.0
# app.py
import streamlit as st
from multi_agent import(run_sync,chat_with_gpt)
import os
from dotenv import load_dotenv
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher
load_dotenv()
st.set_page_config(page_title="multi_agent")


# st.write("""###### PMI関連の質問に回答してくれるアシスタントAIです。\n
# ###### Graphデータベースとベクトルデータベースを利用したハイブリッドRAGシステムを採用しています。
#         """)

# hashed_pw = stauth.Hasher([os.getenv("APP_PASSWORD")]).generate()[0]
plain = os.getenv("APP_PASSWORD", "")
hashed_pw = Hasher.hash(plain)


config = {
    "credentials": {
        "usernames": {
            os.getenv("APP_USER"): {
                "name" : "user",
                "password": hashed_pw,
                # "roles": ["admin"],
            },
            os.getenv("APP_USER2"): {
                "name" : "rag",
                "password": hashed_pw,
                # "roles": ["admin"],
            },
        }
    },
    "cookie": {
        "name":  "app_auth",
        "key":   os.getenv("COOKIE_KEY"),          # ランダム文字列を Secrets で注入
        "expiry_days": int(3),
    },
}

authenticator = stauth.Authenticate(config["credentials"],
                                    cookie_name=config["cookie"]["name"],
                                    cookie_key=config["cookie"]["key"],
                                    cookie_expiry_days=config["cookie"]["expiry_days"])


# ログインフォームの表示（ここで入力欄が出る）
name, auth_status, username = authenticator.login(
    "マルチエージェントAI\nログイン画面",  # form_name
    "ログイン",                            # login_button_name
    location="main"
)

# 認証結果に応じてアプリの表示を切り替える
if auth_status:
    st.info("""### 課題解決マルチエージェント
         - 入力した課題に対してAIエージェントが解決策を議論します。
    - エージェントはストラテジスト、リスク管理、エンジニア、現場社員、ファシリテーターの5名です。
    - 使い方/質問例
        ✓ 地方創生、農業、DX、少子高齢化、海外展開をテーマに新しいビジネスを考えてください。""")
    st.warning("""
###### ※参照している書類は、全て生成AIで作成した架空の資料・案件メモです。
""")
    st.sidebar.write(f"ユーザー：{username}")
    authenticator.logout(location='sidebar')
    st.sidebar.divider()
 
# st.set_page_config(page_title="AutoGen 議論チャット", layout="centered")
# st.title("🤖 AIエージェントと議論しよう")






    # ——— セッションの初期化 ———
    if "qa_history" not in st.session_state:
        # 各質問ごとに { "question": str, "responses": list[(sender,content)] } を保存
        st.session_state.qa_history = []

    # ——— これまでの QA ペアを表示 ———
    for entry in st.session_state.qa_history:
        # ユーザー質問
        with st.chat_message("user"):
            st.markdown(entry["question"])
        # 対応するエージェント応答を折りたたみ表示
        with st.expander("エージェントの発言", expanded=False):
            for sender, msg in entry["responses"]:
                st.markdown(f"**{sender}**: {msg}")
        with st.chat_message("assistant"):
            st.markdown(entry["answer"])

    # ユーザー入力
    user_input = st.chat_input("💬 議論したい内容を入力してください")

    if user_input:
        # ユーザー発言を記録＆表示
        st.session_state.qa_history.append({
            "question": user_input,
            "responses": [],
            "answer":[]
        })
        with st.chat_message("user"):
            st.markdown(user_input)

        # “現在発言中のエージェント” を差し替えるプレースホルダー
        placeholder = st.empty()

        with st.spinner("エージェントたちが議論しています..."):
            temp_logs = []
            def handle_message(sender: str, content: str):
                st.session_state.qa_history[-1]["responses"].append((sender, content))
                temp_logs.append((sender, content))
                # 前の発言をクリアして、新しい発言だけ表示
                placeholder.empty()
                # 1) 最初の3行だけ抜き出してプレビュー
                lines = content.splitlines()
                preview = lines[:5]
                if len(lines) > 5:
                    preview.append("・・・・・")

                # 2) 発言者名とプレビューを結合
                preview_text = "\n".join(preview)
                full_preview = f"{sender}: {preview_text}"

                # 3) 各行をブロック引用に
                quoted = "\n".join(f"> {line}" for line in full_preview.splitlines())

                placeholder.markdown(quoted)

            run_sync(user_input, handle_message)
            final_answer = chat_with_gpt(user_input,temp_logs)

        with st.expander("エージェントの発言",expanded=False):
            placeholder.empty()
            for role, message in temp_logs:
                st.markdown(f"**{role}**: {message}")
        with st.chat_message("assistant"):
            st.markdown(final_answer)

        st.session_state.qa_history[-1]["answer"].append((final_answer))

elif auth_status is False:
    st.error("ユーザー名またはパスワードが間違っています。")
elif auth_status is None:
    st.info("ユーザー名とパスワードを入力してください。")
