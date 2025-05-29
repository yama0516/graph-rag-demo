import streamlit as st
from rag_logic import run_graph_rag  # ロジックをインポート
import os
from dotenv import load_dotenv
import streamlit_authenticator as stauth

load_dotenv()

st.set_page_config(page_title="Graph RAG Demo")
st.title("移転価格Graph RAG")

hashed_pw = stauth.Hasher([os.getenv("APP_PASSWORD")]).generate()[0]

config = {
    "credentials": {
        "usernames": {
            os.getenv("APP_USER"): {
                "name" : "time",
                "password": hashed_pw,
                # "roles": ["admin"],
            }
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
name, auth_status, username = authenticator.login(location='main')

# 認証結果に応じてアプリの表示を切り替える
if auth_status:
    authenticator.logout(location='sidebar')
    st.write(f"ようこそ、ユーザーさん！")
    st.success("ログインに成功しました。")
    USER_NAME = "user"
    ASSISTANT_NAME = "AI"

# チャットログを保存したセッション情報を初期化
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []


query = st.chat_input("ここにメッセージを入力")
if query:
    # 以前のチャットログを表示
    for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.write(chat["msg"])

    # 最新のメッセージを表示
    with st.chat_message(USER_NAME):
        st.write(query)

    # アシスタントのメッセージを表示
    with st.spinner("回答中...少々お待ちください..."):
        response = run_graph_rag(query)
    with st.chat_message(ASSISTANT_NAME):
        assistant_msg = ""
        placeholder = st.empty()
        for chunk in response:
            # たとえば OpenAI のチャンクなら .choices[0].delta.content でテキスト取得
            delta = chunk
            assistant_msg += delta
            placeholder.write(assistant_msg)

    # セッションにチャットログを追加
    st.session_state.chat_log.append({"name": USER_NAME, "msg": query})
    st.session_state.chat_log.append({"name": ASSISTANT_NAME, "msg": assistant_msg})
    # ← ここに本体のアプリ処理を書く
elif auth_status is False:
    st.error("ユーザー名またはパスワードが間違っています。")
elif auth_status is None:
    st.info("ユーザー名とパスワードを入力してください。")