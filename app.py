import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils import send_report_via_sendgrid

# ページ設定
st.set_page_config(page_title="俺の会計監査六法", page_icon="📖", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("会計監査六法一覧.csv", encoding="utf-8")
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df["セクション内番号"] = pd.to_numeric(df["セクション内番号"], errors="coerce")
    return df


df = load_data()

if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
if "show_dify" not in st.session_state:
    st.session_state.show_dify = False


def set_selected_item(item_id):
    st.session_state.selected_item_id = item_id
    st.session_state.show_dify = False


def set_show_dify():
    st.session_state.show_dify = True
    st.session_state.selected_item_id = None


# サイドバー
with st.sidebar:
    st.title("俺の会計監査六法 ver.2025")
    search_term = st.text_input("項目名を検索", "")
    filtered_df = (
        df[df["項目名"].str.contains(search_term, case=False)] if search_term else df
    )
    st.write(f"表示件数: {len(filtered_df)}件")
    st.markdown("---")
    if st.button("🤖に質問する", use_container_width=True):
        set_show_dify()
    sections = filtered_df["セクション名"].unique()
    for section in sections:
        with st.expander(f"{section}", expanded=bool(search_term)):
            section_df = filtered_df[
                filtered_df["セクション名"] == section
            ].sort_values("セクション内番号")
            for _, row in section_df.iterrows():
                button_label = f"{row['セクション内番号']}. {row['項目名']}"
                if st.button(
                    button_label, key=f"btn_{row['ID']}", use_container_width=True
                ):
                    set_selected_item(row["ID"])

# メインコンテンツ
if st.session_state.get("show_dify"):
    st.markdown("### 🤖日本の会計基準に詳しい君2号")
    with st.expander("ヘルプ：使い方", expanded=False):
        st.info(
            "シークレットコードを入力し、「Start Chat」を押してください。会計基準等に則って回答してくれます。"
        )
    st.error(
        "機密情報の入力は避けてください。また、回答内容は必ずご自身でレビューしてください。",
        icon="🚨",
    )
    components.html(
        """
        <iframe
         src="https://udify.app/chatbot/zP13RfYRyo8rOxis"
         style="width: 100%; height: 100%; min-height: 700px"
         frameborder="0"
         allow="microphone">
        </iframe>
        """,
        height=800,
        scrolling=True,
    )

elif st.session_state.selected_item_id is not None:
    selected_df = df[df["ID"] == st.session_state.selected_item_id]
    if not selected_df.empty:
        item = selected_df.iloc[0]

        st.markdown(
            f"""
            <a href="{item["URL"]}" target="_blank" rel="noopener noreferrer"
            style="display: inline-block; color: #ffffff; background-color: #0066cc;
            padding: 8px 15px; text-decoration: none; border-radius: 4px;
            text-align: center; margin-bottom: 10px; font-weight: 500;">
                新しいタブで開く
            </a>""",
            unsafe_allow_html=True,
        )

        with st.expander("ヘルプ：ページが表示されない場合", expanded=False):
            st.info(
                "上記の「新しいタブで開く」を使用してください。それでも表示されない場合はページ下部の不具合報告フォームからご報告ください。"
            )

        if item["URL"].lower().endswith(".pdf"):
            try:
                # item["URL"]をGoogleドキュメントビューアで表示
                google_docs_viewer_url = (
                    f"https://docs.google.com/viewer?url={item['URL']}&embedded=true"
                )
                components.iframe(google_docs_viewer_url, width=1920, height=1080)

                # item["URL2"]が存在し、空文字やNaNでない場合は追加表示
                if (
                    pd.notnull(item["URL2"])
                    and isinstance(item["URL2"], str)
                    and item["URL2"].strip() != ""
                ):
                    google_docs_viewer_url2 = (
                        "https://docs.google.com/viewer?url="
                        + f"{item['URL2']}&embedded=true"
                    )
                    components.iframe(google_docs_viewer_url2, width=1920, height=1080)
            except Exception as e:
                st.error(f"ドキュメントの読み込み中にエラーが発生しました: {e}")
        else:
            components.html(
                f"""
                <iframe
                    src="{item['URL']}"
                    width="100%"
                    height="100%"
                    style="border:none; min-height: 1080px;"
                    sandbox="allow-same-origin allow-scripts allow-popups allow-forms">
                </iframe>
                """,
                width=1920,
                height=1080,
            )

        # リンク報告セクション
        st.markdown("---")
        st.subheader("不具合報告")
        st.write("このページに不具合を見つけた場合、以下のフォームからご報告ください。")

        with st.form("report_form", clear_on_submit=True):
            error_event = st.radio(
                "報告内容",
                options=["リンク切れ", "誤リンク", "リンクが古い"],
                horizontal=True,
                help="リンクに発生しているエラーの種類を選択してください。",
            )
            submit_report = st.form_submit_button("送信")
            if submit_report:
                with st.spinner("送信中です...お待ちください"):
                    status = send_report_via_sendgrid(error_event, item["URL"])
                if status and status == 202:
                    st.success("ご報告ありがとうございます。確認後、対応いたします。")
                else:
                    st.error("報告送信中にエラーが発生しました。")
else:
    st.info("サイドバーから表示したい項目を選択してください。")
    st.markdown(
        "姉妹サイト：[俺の監査実務ハンドブック](https://orekansa.streamlit.app/)"
    )
    # 以下、更新履歴
    st.markdown("### 📋 更新履歴")
    st.markdown("以下の更新を反映しました。")

    # updates = [
    #     {
    #         "date": "20YY/MM/DD",
    #         "title": "title",
    #         "url": "https://xxxx",
    #     },
    #     # 新しい更新情報はここに追加していけます
    # ]

    # for update in updates:
    #     col1, col2 = st.columns([1, 4])
    #     with col1:
    #         st.markdown(f"**{update['date']}**")
    #     with col2:
    #         st.markdown(f"[{update['title']}]({update['url']})")
    #     st.markdown("---")


st.markdown(
    """
    <style>
    .stButton button {
        text-align: left;
        padding: 8px 15px;
        border-radius: 4px;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
