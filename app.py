import streamlit as st
import pandas as pd
import re

# ==========================================
# [설정] 편의점 약 이미지 수동 매핑 (업데이트됨)
# ==========================================
# 실제 작동하는 이미지 링크로 교체했습니다. (2025.12.03 기준)
CONVENIENCE_DRUG_IMAGES = {
    "판콜에이내복액": "https://www.dong-wha.co.kr/product/images/product/pancol_a.png", 
    "판피린티정": "https://www.donga-st.com/upload/product/20210216_105244_414.jpg",
    "타이레놀정500밀리그람(아세트아미노펜)": "https://www.tylenol.co.kr/sites/tylenol_kr/files/styles/product_image/public/product-images/tylenol_500mg_prod_0.png",
    "어린이부루펜시럽": "https://samil-pharm.com/img/product/brufen_syrup.jpg",
    "베아제정": "https://www.daewoong.co.kr/images/product/otc/bease_img01.jpg",
    "닥터베아제정": "https://www.daewoong.co.kr/images/product/otc/dr_bease_img01.jpg",
    "훼스탈플러스정": "https://handok.co.kr/wp-content/uploads/2020/07/festal_plus.jpg",
    "신신파스아렉스": "https://sinsin.com/img/product/arex_img.jpg"
}

# ==========================================
# 1. 데이터 로드 및 전처리 (Cleaning)
# ==========================================
@st.cache_data
def load_and_clean_data():
    try:
        df = pd.read_csv('프로젝트/미니프로젝트(쵸비상약)/drugs_list_v2.csv')
        
        # [Issue 4 해결] 효능이나 사용법이 없는 데이터는 삭제 (결측치 제거)
        df = df.dropna(subset=['효능효과', '사용법'])
        
        # [NEW] 텍스트 정제 함수 (물결표 이슈 해결 포함)
        def advanced_clean(text):
            if pd.isna(text): return ""
            text = str(text)
            
            # 1. 식약처 데이터의 '삭제된 정보' 태그 제거 (<del>, <s>)
            text = re.sub(r'<del>.*?</del>', '', text, flags=re.DOTALL)
            text = re.sub(r'<s>.*?</s>', '', text, flags=re.DOTALL)
            
            # 2. 나머지 HTML 태그 제거
            text = re.sub(r'<.*?>', '', text)
            
            # 3. [핵심 수정] 물결표(~)가 취소선으로 인식되지 않도록 이스케이프(\) 처리
            # 예: "1~2정" -> "1\~2정" (이렇게 해야 화면에 정상적으로 나옵니다)
            text = text.replace('~', '\~')
            
            return text.strip()

        # 데이터프레임 전체에 적용
        df['효능효과'] = df['효능효과'].apply(advanced_clean)
        df['사용법'] = df['사용법'].apply(advanced_clean)
        df['주의사항'] = df['주의사항'].apply(advanced_clean)
        
        return df
    except Exception as e:
        return None

# ==========================================
# 2. 메인 앱 로직
# ==========================================
def main():
    st.set_page_config(layout="wide", page_title="쵸 비 상 약")

    # CSS 스타일링 (가독성 개선)
    st.markdown("""
        <style>
        .drug-title { font-size:18px; color: #2c3e50; font-weight: bold; }
        .efficacy-text { color: #e74c3c; font-weight: bold; }
        img { border-radius: 10px; } /* 이미지 모서리 둥글게 */
        </style>
    """, unsafe_allow_html=True)

    st.title("💊 쵸 비 상 약 (Cho-Bi-Sang-Yak)")
    st.markdown("### 🚑 내 손 안의 의사, 증상만 말씀하세요!")

    df = load_and_clean_data()
    
    if df is None:
        st.error("데이터 파일(drugs_list_v2.csv)이 없습니다.")
        return

    # 사용자 입력
    symptoms_list = ['선택하세요', '두통', '치통', '생리통', '근육통', '소화불량', '감기', '발열', '타박상']
    selected_symptom = st.selectbox("현재 겪고 계신 증상을 선택해주세요:", symptoms_list)

    if selected_symptom != '선택하세요':
        # 필터링 로직
        recommendations = df[df['효능효과'].str.contains(selected_symptom, na=False)]
        
        conv_drugs = recommendations[recommendations['구매처'].str.contains("편의점")]
        pharm_drugs = recommendations[~recommendations['구매처'].str.contains("편의점")]

        st.info(f"'{selected_symptom}' 증상에 대한 검색 결과: 총 {len(recommendations)}건")
        
        tab1, tab2 = st.tabs(["🏪 편의점/약국 겸용 (급할 때)", "약국 전용"])
        
        # ----------------------------------------
        # Tab 1: 편의점 약
        # ----------------------------------------
        with tab1:
            if not conv_drugs.empty:
                for idx, row in conv_drugs.iterrows():
                    with st.container():
                        st.markdown(f"#### {row['이름']}")
                        st.caption(f"제조사: {row['제조사']}")
                        
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            # 이미지 매칭 로직
                            matched_img = None
                            for key, url in CONVENIENCE_DRUG_IMAGES.items():
                                if key in row['이름']: # 이름이 포함되면 매칭
                                    matched_img = url
                                    break
                            
                            if matched_img:
                                st.image(matched_img, width=200)
                            elif pd.notna(row['이미지URL']):
                                st.image(row['이미지URL'], width=200, caption="식별용 이미지")
                            else:
                                st.text("이미지 없음")
                                
                        with col2:
                            # 물결표가 수정된 텍스트 출력
                            st.markdown(f"**효능:** :red[{row['효능효과']}]")
                            st.markdown(f"**용법:** {row['사용법']}")
                            
                            with st.expander("주의사항 보기"):
                                st.write(row['주의사항'])
                        
                        st.divider()
            else:
                st.warning("이 증상으로 편의점에서 살 수 있는 약은 없습니다.")

        # ----------------------------------------
        # Tab 2: 약국 약
        # ----------------------------------------
        with tab2:
            st.write(f"약국 구매 가능 품목: {len(pharm_drugs)}개")
            st.dataframe(
                pharm_drugs[['이름', '제조사', '효능효과']], 
                hide_index=True,
                use_container_width=True
            )

if __name__ == '__main__':
    main()