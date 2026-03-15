import streamlit as st
import cv2
import numpy as np
import easyocr
from fpdf import FPDF
from PIL import Image
import tempfile
import os

# 1. OCR 엔진 초기화 (캐싱하여 속도 향상)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ko', 'en'], gpu=False) # 무료 서버는 GPU가 없으므로 False

reader = load_ocr()

# 2. 이미지 보정 함수 (스캔 효과)
def process_image(img_array):
    # 그레이스케일 변환
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # 노이즈 제거 및 선명도 조절 (Adaptive Thresholding)
    # 이 과정을 거쳐야 배경은 하얗게, 글씨는 진하게 변합니다.
    scan_effect = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    return scan_effect

st.title("scan2pdf")
st.write("사진을 올리면 보정 후 OCR을 거쳐 PDF로 만들어줍니다.")

# 파일 업로드 (여러 장 가능)
uploaded_files = st.file_uploader("사진을 선택하세요 (JPG, PNG)", accept_multiple_files=True)

if uploaded_files and st.button("스캔 시작 🚀"):
    pdf = FPDF()
    progress_bar = st.progress(0)
    
    # 임시 폴더 생성 (PDF에 이미지를 넣기 위해 필요)
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, file in enumerate(uploaded_files):
            # 1) 이미지 로드
            file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            # 2) 보정 실행
            processed_img = process_image(img)
            
            # 3) OCR 실행 (텍스트 추출)
            # detail=0으로 설정하면 위치 정보 없이 글자만 슥 긁어옵니다.
            text_results = reader.readtext(processed_img, detail=0)
            full_text = "\n".join(text_results)
            
            # 4) PDF 페이지 추가
            pdf.add_page()
            
            # 보정된 이미지를 임시 파일로 저장 후 PDF에 삽입
            img_path = os.path.join(temp_dir, f"page_{i}.png")
            cv2.imwrite(img_path, processed_img)
            pdf.image(img_path, x=10, y=10, w=190) # A4 사이즈에 맞춰 삽입
            
            # (옵션) 추출된 텍스트를 다음 페이지나 하단에 추가 가능
            # pdf.add_page()
            # pdf.set_font("Arial", size=12) # 한글 폰트 설정 필요
            # pdf.multi_cell(0, 10, txt=full_text)
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            st.write(f"✅ {i+1}번 페이지 처리 완료")

        # 5) 최종 PDF 저장 및 다운로드 버튼
        pdf_output = pdf.output(dest='S').encode('latin-1') # 바이트로 변환
        st.download_button(
            label="📄 완성된 PDF 다운로드",
            data=pdf_output,
            file_name="scanned_medical_doc.pdf",
            mime="application/pdf"
        )