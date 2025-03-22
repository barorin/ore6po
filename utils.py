import sendgrid  # type: ignore
import streamlit as st
from sendgrid.helpers.mail import Mail  # type: ignore


# SendGridでメール送信する関数
def send_report_via_sendgrid(error_event, url_report):
    SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]
    SENDGRID_FROM_EMAIL = st.secrets["SENDGRID_FROM_EMAIL"]
    SENDGRID_TO_EMAIL = st.secrets["SENDGRID_TO_EMAIL"]

    if not all([SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_TO_EMAIL]):
        st.error("SendGridの設定が正しく行われていません。")
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
