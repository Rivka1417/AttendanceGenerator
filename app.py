
import streamlit as st
from pathlib import Path
import html
import hashlib
import tempfile

from main import process_single_pdf


st.set_page_config(
    page_title="מחולל דוחות נוכחות",
    page_icon="📋",
    layout="centered",
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800;900&display=swap');

.stApp {
    background: #f4f7fc;
    font-family: 'Heebo', Arial, sans-serif;
}

.block-container {
    max-width: 820px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
}

#MainMenu, footer, header {
    visibility: hidden;
}

h1, h2, h3, p, label, div {
    font-family: 'Heebo', Arial, sans-serif;
}

/* Header */
.hero {
    text-align: center;
    padding: 25px 10px 32px;
}

.hero-icon {
    width: 76px;
    height: 76px;
    background: linear-gradient(135deg, #2563eb, #60a5fa);
    border-radius: 23px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 37px;
    margin: 0 auto 20px;
    box-shadow: 0 10px 25px rgba(37,99,235,.22);
}

.hero-title {
    color: #172554;
    font-size: 35px;
    font-weight: 900;
    margin-bottom: 8px;
    direction: rtl;
}

.hero-subtitle {
    color: #718096;
    font-size: 16px;
    direction: rtl;
}

/* Section title */
.section-title {
    color: #1e293b;
    font-size: 19px;
    font-weight: 800;
    text-align: right;
    direction: rtl;
    margin: 15px 0;
}

/* Upload card */
.upload-card {
    background: white;
    border: 2px dashed #b9c9e3;
    border-radius: 20px;
    padding: 27px 20px;
    text-align: center;
    box-shadow: 0 5px 20px rgba(30,64,175,.04);
    margin-bottom: 12px;
}

.upload-icon {
    font-size: 42px;
    margin-bottom: 10px;
}

.upload-title {
    color: #243b63;
    font-size: 19px;
    font-weight: 800;
    direction: rtl;
}

.upload-subtitle {
    color: #8492a6;
    font-size: 14px;
    margin-top: 5px;
    direction: rtl;
}

/* File card */
.file-card {
    background: #eff6ff;
    border: 1px solid #d5e5ff;
    border-radius: 13px;
    padding: 14px 17px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    direction: rtl;
    margin: 15px 0;
    color: #234b87;
}

.file-name {
    font-weight: 700;
    overflow-wrap: anywhere;
}

.file-status {
    color: #16845b;
    font-size: 13px;
    font-weight: 700;
    white-space: nowrap;
}

/* Buttons */
.stButton > button {
    width: 100%;
    height: 54px;
    border-radius: 13px;
    border: none;
    background: linear-gradient(100deg, #2563eb, #397ff0);
    color: white;
    font-size: 17px;
    font-weight: 800;
    box-shadow: 0 7px 17px rgba(37,99,235,.20);
    transition: .2s ease;
}

.stButton > button:hover {
    background: linear-gradient(100deg, #1d4ed8, #2563eb);
    color: white;
    transform: translateY(-2px);
}

/* Results */
.result-card {
    background: white;
    border: 1px solid #e5eaf2;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 5px 18px rgba(15,23,42,.035);
    min-height: 105px;
    direction: rtl;
}

.result-icon {
    font-size: 28px;
    margin-bottom: 9px;
}

.result-title {
    color: #243b63;
    font-size: 15px;
    font-weight: 800;
}

.result-description {
    color: #8a97aa;
    font-size: 12px;
    margin-top: 4px;
}

.footer {
    text-align: center;
    color: #a0aabd;
    font-size: 12px;
    margin-top: 45px;
    direction: ltr;
}

/* RTL */
.stFileUploader, .stAlert {
    direction: rtl;
    text-align: right;
}

.stFileUploader label {
    direction: rtl;
    text-align: right;
}

[data-testid="stFileUploaderDropzone"] {
    background: #ffffff;
    border: none;
}

/* Download buttons */
.stDownloadButton > button {
    width: 100%;
    border-radius: 11px;
    font-family: 'Heebo', Arial, sans-serif;
    font-weight: 700;
    min-height: 43px;
}

</style>
""", unsafe_allow_html=True)


# אתחול מצב התוצאות
if "processing_result" not in st.session_state:
    st.session_state.processing_result = None

if "processed_file_hash" not in st.session_state:
    st.session_state.processed_file_hash = None


# Header
st.markdown("""
<div class="hero">
    <div class="hero-icon">📋</div>
    <div class="hero-title">מחולל דוחות נוכחות</div>
    <div class="hero-subtitle">
        מעלים דוח נוכחות ומקבלים תוצאות מסודרות בכמה רגעים
    </div>
</div>
""", unsafe_allow_html=True)


# Upload section
st.markdown(
    '<div class="section-title">העלאת דוח חדש</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="upload-card">
    <div class="upload-icon">📄</div>
    <div class="upload-title">הקובץ שלך מתחיל כאן</div>
    <div class="upload-subtitle">
        בחרי קובץ PDF מהמחשב כדי להתחיל
    </div>
</div>
""", unsafe_allow_html=True)


uploaded_file = st.file_uploader(
    "בחירת קובץ PDF",
    type=["pdf"],
    label_visibility="collapsed",
)


# קריאת הקובץ וחישוב מזהה ייחודי
file_bytes = None
file_hash = None

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    safe_name = html.escape(uploaded_file.name)

    st.markdown(f"""
    <div class="file-card">
        <span class="file-name">📄 {safe_name}</span>
        <span class="file-status">✓ הקובץ נבחר</span>
    </div>
    """, unsafe_allow_html=True)

    # לא מציגים תוצאה ישנה עבור קובץ אחר
    if st.session_state.processed_file_hash != file_hash:
        st.session_state.processing_result = None
        st.session_state.processed_file_hash = None


# Processing section
st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀  התחלת עיבוד", key="process_button"):

    if uploaded_file is None:
        st.warning("יש לבחור קובץ PDF לפני תחילת העיבוד.")

    else:
        # שמירת הקובץ והפלט בסביבת עבודה זמנית
        try:
            with st.spinner("מעבד את הדוח... אנא המתיני"):

                with tempfile.TemporaryDirectory(
                    prefix="attendance_generator_"
                ) as temp_dir:

                    workspace = Path(temp_dir)

                    input_dir = workspace / "input"
                    output_dir = workspace / "output"

                    input_dir.mkdir()
                    output_dir.mkdir()

                    # שמירת הקובץ שהועלה
                    safe_filename = Path(
                        uploaded_file.name.replace("\\", "/")
                    ).name

                    input_path = input_dir / safe_filename
                    input_path.write_bytes(file_bytes)

                    # הפעלת מנוע העיבוד הקיים
                    pdf_path, html_path = process_single_pdf(
                        input_pdf_path=input_path,
                        output_dir=output_dir
                    )

                    # קריאת התוצאות לפני מחיקת סביבת העבודה הזמנית
                    pdf_bytes = pdf_path.read_bytes()
                    html_content = html_path.read_text(
                        encoding="utf-8"
                    )

                    # שמירת התוצאות בזיכרון של הממשק
                    st.session_state.processing_result = {
                        "pdf_bytes": pdf_bytes,
                        "html_content": html_content,
                        "pdf_name": pdf_path.name,
                        "html_name": html_path.name,
                    }

                    st.session_state.processed_file_hash = file_hash

            st.success("הדוח עובד בהצלחה! התוצאות מוכנות.")

        except Exception:
            st.session_state.processing_result = None
            st.session_state.processed_file_hash = None

            st.error(
                "לא הצלחנו לעבד את הקובץ. "
                "בדקי שה-PDF תקין ונסי שוב."
            )


# Results section
result = st.session_state.processing_result

if result is not None and file_hash == st.session_state.processed_file_hash:

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">התוצאות שלך</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="result-card">
            <div class="result-icon">📕</div>
            <div class="result-title">דוח PDF</div>
            <div class="result-description">
                הדוח המעובד שלך
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️ הורדת דוח PDF",
            data=result["pdf_bytes"],
            file_name=result["pdf_name"],
            mime="application/pdf",
            key="download_pdf",
            use_container_width=True,
        )

    with col2:
        st.markdown("""
        <div class="result-card">
            <div class="result-icon">🌐</div>
            <div class="result-title">דוח HTML</div>
            <div class="result-description">
                גרסת הדוח לצפייה בדפדפן
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️ הורדת דוח HTML",
            data=result["html_content"].encode("utf-8"),
            file_name=result["html_name"],
            mime="text/html",
            key="download_html",
            use_container_width=True,
        )

    # תצוגה מקדימה של דוח ה-HTML
    with st.expander("👁️ צפייה בתוצאה בתוך הממשק"):
        st.components.v1.html(
            result["html_content"],
            height=700,
            scrolling=True,
        )


# Footer
st.markdown("""
<div class="footer">
    ATTENDANCE GENERATOR
</div>
""", unsafe_allow_html=True)
