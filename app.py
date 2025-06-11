import streamlit as st
from rag_logic import run_graph_rag  # ロジックをインポート
import os
from dotenv import load_dotenv
import streamlit_authenticator as stauth

load_dotenv()

st.set_page_config(page_title="Graph RAG Demo")


# st.write("""###### PMI関連の質問に回答してくれるアシスタントAIです。\n
# ###### Graphデータベースとベクトルデータベースを利用したハイブリッドRAGシステムを採用しています。
#         """)

hashed_pw = stauth.Hasher([os.getenv("APP_PASSWORD")]).generate()[0]

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
name, auth_status, username = authenticator.login(location='main', fields={'Form name': 'PMIアシスタントAI\nログイン画面','Login': 'ログイン'})

# 認証結果に応じてアプリの表示を切り替える
if auth_status:
    st.info("""### PMIアシスタントAI
         - PMI関連の質問に回答してくれるアシスタントAIです
    - Graphデータベースとベクトルデータベースを利用したハイブリッドRAGシステムを採用しています。
    - 使い方/質問例
        ✓ 製造業のPMIを計画しています。過去の案件から検討すべき論点を教えてください。
        ✓ 買収先のITセキュリティポリシーが極めて緩く、ウイルス検知やID管理が不十分です。
         　Day30までに講じるべき最低限の対策は何ですか？
        ✓ 会計ポリシーの統一に関して、過去の案件及び論点を全て教えてください。
        ✓ ITセキュリティ体制が買収先に存在しない場合、PMIで最初に実施すべきステップは？""")
    st.warning("""
###### ※参照している書類は、全て生成AIで作成した架空の資料・案件メモです。
""")
    st.sidebar.write(f"ユーザー：{username}")
    authenticator.logout(location='sidebar')
    st.sidebar.divider()
    st.sidebar.markdown("""
### 参照している資料・案件メモ一覧
###### 1.PMIマイルストーンリスト（会計税務/IT/人事/法務）
###### 2.国内物流企業によるIT関連子会社の買収に伴うクロスファンクショナルPMI整理メモ
###### 3.海外M&Aによる製造子会社の買収に伴うPMI実務整理メモ
###### 4.欧州拠点の製薬企業買収に伴うPMI論点整理メモ（機能別課題と実行上の示唆）
###### 5.北米医療機器メーカー買収に伴う統合実務に関するPMI案件整理メモ
###### 6.国内製造業による異業種ベンチャー買収におけるPMI論点整理メモ
###### 7.中堅エネルギー商社による再生可能エネルギー事業会社買収に関するPMI案件
###### 8.国内ITサービス企業による地方金融機関向けソリューション会社の買収におけるPMI
###### 9.日系商社による物流スタートアップ買収に関するPMI案件
###### 10.製造業による同業統合における会計・業務・管理体制のPMI
###### 11.欧州BPO企業買収に伴う機能別統合マネジメントの実務整理メモ
###### 12.北米子会社統合に伴う論点整理
###### 13.欧州製造業買収後におけるグループ内制度整備と早期安定化に関する論点整理
###### 14.グローバル製造業の買収後Day360フェーズにおける制度統合とシナジー実現のための論点整理
###### 15.国内物流業界の買収案件における初期PMIフェーズにおける制度整備と関係構築の論点整理
###### 16.業務プロセスとシステム基盤の融合を軸としたPMI実行案件整理メモ
###### 17.データ・制度・人材の融合を軸とした中堅IT企業の統合案件整理
###### 18.大手製薬企業によるバイオベンチャー買収後の管理基盤統合に向けたPMI対応
###### 19.国内大手製造業による中堅IT企業買収後のリスク統合・人材強化を重視したPMI推進
###### 20.欧州ITインフラ企業の買収に伴うPMI計画に関する論点整理
###### 21.海外子会社買収後の会計領域における統合作業に関するPMI案件整理メモ
###### 22.アクシオン・グループによる海外医療機器メーカー「メディトロン社」の買収後PMI案件
###### 23.アサヒテクス株式会社によるベトナムの樹脂製品メーカーの買収後統合（PMI）整理メモ
###### 24.グローバル電機部品メーカーによるインド拠点のM&A
###### 25.サンエレクトロニクス株式会社によるトルコ半導体メーカーの買収とPMI実行に関する案件整理メモ
###### 26.ライフロジックス株式会社による南米医薬品物流企業の買収とPMI統合計画
###### 27.日本イーコマース株式会社による米国ECプラットフォーム企業買収後の統合対応記録
###### 28.アジアライフホールディングスによるメディフューチャー社買収における初期統合施策メモ
###### 29.ソライメディカルによるエコフィルム社買収後の統合初期対応メモ
###### 30.アスタリクス社によるテクノレイン社買収に伴う機能統合メモ
###### 31.シグナス物流によるグローバル倉庫運営会社の買収案件整理メモ
                                                """)

    # USER_NAME = "user01"
    # ASSISTANT_NAME = "AI"

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
        with st.chat_message("user"):
            st.write(query)

        # アシスタントのメッセージを表示
        with st.spinner("回答生成中...少々お待ちください..."):
            response = run_graph_rag(query)
        with st.chat_message("AI"):
            assistant_msg = ""
            placeholder = st.empty()
            for chunk in response:
                # たとえば OpenAI のチャンクなら .choices[0].delta.content でテキスト取得
                delta = chunk
                assistant_msg += delta
                placeholder.write(assistant_msg)

        # セッションにチャットログを追加
        st.session_state.chat_log.append({"name": "user", "msg": query})
        st.session_state.chat_log.append({"name": "AI", "msg": assistant_msg})
    # ← ここに本体のアプリ処理を書く
elif auth_status is False:
    st.error("ユーザー名またはパスワードが間違っています。")
elif auth_status is None:
    st.info("ユーザー名とパスワードを入力してください。")