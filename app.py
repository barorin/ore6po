import tempfile

import pandas as pd
import requests
import sendgrid  # type: ignore
import streamlit as st
import streamlit.components.v1 as components
from sendgrid.helpers.mail import Mail  # type: ignore
from streamlit_pdf_viewer import pdf_viewer  # type: ignore

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


def set_selected_item(item_id):
    st.session_state.selected_item_id = item_id


with st.sidebar:
    st.title("俺の会計監査六法 ver.2025")
    search_term = st.text_input("項目名を検索", "")
    filtered_df = (
        df[df["項目名"].str.contains(search_term, case=False)] if search_term else df
    )
    st.write(f"表示件数: {len(filtered_df)}件")
    st.markdown("---")
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

if st.session_state.selected_item_id is not None:
    selected_df = df[df["ID"] == st.session_state.selected_item_id]
    if not selected_df.empty:
        item = selected_df.iloc[0]
        st.markdown(
            f"""
            <a href="{item["URL"]}" target="_blank" rel="noopener noreferrer">
                新しいタブで開く
            </a>""",
            unsafe_allow_html=True,
        )
        if item["URL"].lower().endswith(".pdf"):
            try:
                # PDFファイルをリモートからダウンロード
                response = requests.get(item["URL"])
                if response.status_code == 200:
                    # 一時ファイルに保存してパスを取得
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        tmp_file.write(response.content)
                        pdf_path = tmp_file.name
                    pdf_viewer(pdf_path, height=1080)
                else:
                    st.error("PDFの取得に失敗しました。")
            except Exception as e:
                st.error(e)
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
else:
    st.info("サイドバーから表示したい項目を選択してください。")

# -----------------------------
# リンク報告セクション
# -----------------------------
st.markdown("---")
st.subheader("不具合報告")
# 選択中の項目があればそのURLを初期値として設定、なければ空欄
default_url = item["URL"] if st.session_state.selected_item_id is not None else ""
st.write("リンク切れや誤リンクを見つけた場合、以下のフォームからご報告ください。")


# SendGridでメール送信する関数
def send_report_via_sendgrid(error_event, url_report):
    SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]
    SENDGRID_FROM_EMAIL = st.secrets["SENDGRID_FROM_EMAIL"]
    SENDGRID_TO_EMAIL = st.secrets["SENDGRID_TO_EMAIL"]

    if not all([SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_TO_EMAIL]):
        st.error("SendGridの設定が正しく行われていません。.envを確認してください。")
        return None

    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = f"【俺の会計監査六法】不具合報告 - {error_event}"
    content = f"不具合報告が送信されました。\n\n【エラー種別】{error_event}\n【報告URL】{url_report}"

    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=SENDGRID_TO_EMAIL,
        subject=subject,
        plain_text_content=content,
    )

    try:
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        st.error(f"メール送信に失敗しました: {str(e)}")
        return None


with st.form("report_form", clear_on_submit=True):
    error_event = st.radio(
        "報告内容",
        options=["リンク切れ", "誤リンク", "リンクが古い"],
        horizontal=True,
        help="リンクに発生しているエラーの種類を選択してください。",
    )
    url_report = st.text_input(
        "該当リンクのURL",
        value=default_url,
        help="報告するリンクのURLを入力してください。",
    )
    submit_report = st.form_submit_button("送信")
    if submit_report:
        with st.spinner("送信中です...お待ちください"):
            status = send_report_via_sendgrid(error_event, url_report)
        if status and status == 202:
            st.success("ご報告ありがとうございます。確認後、対応いたします。")
        else:
            st.error("報告送信中にエラーが発生しました。")

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
