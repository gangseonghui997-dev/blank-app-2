import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

# -----------------------------
# 1. 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="우리 동네 공기 발표 대시보드",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# 2. 발표용 스타일
# -----------------------------
st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #1f4e79;
    text-align: center;
    margin-bottom: 10px;
}
.sub-title {
    font-size: 20px;
    text-align: center;
    color: #4f4f4f;
    margin-bottom: 30px;
}
.big-card {
    background: linear-gradient(135deg, #e0f7fa, #f1f8ff);
    padding: 24px;
    border-radius: 22px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    text-align: center;
    margin-bottom: 16px;
}
.card-title {
    font-size: 20px;
    font-weight: 700;
    color: #1f4e79;
}
.card-value {
    font-size: 34px;
    font-weight: 900;
    color: #0d47a1;
    margin-top: 8px;
}
.small-text {
    font-size: 14px;
    color: #666666;
}
.section-title {
    font-size: 28px;
    font-weight: 800;
    color: #1565c0;
    margin-top: 15px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 3. 제목
# -----------------------------
st.markdown('<div class="main-title">🌤️ 우리 동네 공기 발표 대시보드</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">2025년 1월 공기 데이터를 쉽고 예쁘게 살펴봐요!</div>',
    unsafe_allow_html=True
)

# -----------------------------
# 4. 요일 한글 매핑
# -----------------------------
weekday_map = {
    0: "월",
    1: "화",
    2: "수",
    3: "목",
    4: "금",
    5: "토",
    6: "일"
}

def format_date_with_korean_day(dt):
    if pd.isna(dt):
        return ""
    return f"{dt.year}-{dt.month:02d}-{dt.day:02d} ({weekday_map[dt.weekday()]})"

def format_datetime_with_korean_day(dt):
    if pd.isna(dt):
        return ""
    return f"{dt.month:02d}-{dt.day:02d} ({weekday_map[dt.weekday()]}) {dt.hour:02d}시"

# -----------------------------
# 5. 공기 상태 함수
# -----------------------------
def air_quality_status(pm10):
    if pd.isna(pm10):
        return "❓ 알 수 없음", "#bdbdbd"
    elif pm10 <= 30:
        return "🟢 좋음", "#66bb6a"
    elif pm10 <= 80:
        return "🟡 보통", "#ffca28"
    else:
        return "🔴 나쁨", "#ef5350"

def air_score(pm10):
    if pd.isna(pm10):
        return 0
    score = max(0, 100 - int(pm10))
    return score

# -----------------------------
# 6. 데이터 로드
# -----------------------------
@st.cache_data
def load_air_data(file_path):
    df = pd.read_csv(file_path)

    def parse_hour_24(dt_str):
        dt_str = str(dt_str)
        date_part = dt_str[:8]
        hour_part = dt_str[8:]

        try:
            if hour_part == "24":
                dt = datetime.strptime(date_part, "%Y%m%d")
                return dt + pd.Timedelta(days=1)
            else:
                return datetime.strptime(dt_str, "%Y%m%d%H")
        except:
            return pd.NaT

    df["날짜시간"] = df["측정일시"].apply(parse_hour_24)
    df["날짜"] = df["날짜시간"].dt.date
    df["요일"] = df["날짜시간"].dt.weekday.map(weekday_map)
    df["날짜표시"] = df["날짜시간"].apply(format_date_with_korean_day)
    df["시간표시"] = df["날짜시간"].apply(format_datetime_with_korean_day)

    pollutants = ["SO2", "CO", "O3", "NO2", "PM10", "PM25"]
    for p in pollutants:
        df[p] = pd.to_numeric(df[p], errors="coerce")

    return df

# -----------------------------
# 7. 파일 경로
# -----------------------------
data_path = Path("data/202501-air.csv")
if not data_path.exists():
    data_path = Path("202501-air.csv")

try:
    df = load_air_data(data_path)
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요: {e}")
    st.stop()

# -----------------------------
# 8. 사이드바
# -----------------------------
with st.sidebar:
    st.header("🎛️ 발표용 설정")

    all_regions = sorted(df["지역"].dropna().unique())
    selected_regions = st.multiselect(
        "어느 지역을 볼까요?",
        options=all_regions,
        default=all_regions[:2] if len(all_regions) >= 2 else all_regions
    )

    station_base_df = df[df["지역"].isin(selected_regions)] if selected_regions else df.copy()
    all_stations = sorted(station_base_df["측정소명"].dropna().unique())

    selected_stations = st.multiselect(
        "어느 측정소를 볼까요?",
        options=all_stations,
        default=all_stations[:1] if len(all_stations) >= 1 else all_stations
    )

    min_date = df["날짜"].min()
    max_date = df["날짜"].max()

    date_range = st.date_input(
        "언제의 공기를 볼까요?",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.divider()

    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

# -----------------------------
# 9. 날짜 처리
# -----------------------------
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
elif isinstance(date_range, list) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

# -----------------------------
# 10. 필터링
# -----------------------------
filtered_df = df.copy()

if selected_regions:
    filtered_df = filtered_df[filtered_df["지역"].isin(selected_regions)]

if selected_stations:
    filtered_df = filtered_df[filtered_df["측정소명"].isin(selected_stations)]

filtered_df = filtered_df[
    (filtered_df["날짜"] >= start_date) &
    (filtered_df["날짜"] <= end_date)
].sort_values("날짜시간")

if filtered_df.empty:
    st.warning("선택한 조건에 맞는 데이터가 없어요.")
    st.stop()

# -----------------------------
# 11. 현재 요약
# -----------------------------
latest = filtered_df.iloc[-1]
status_text, status_color = air_quality_status(latest["PM10"])
score = air_score(latest["PM10"])

st.markdown('<div class="section-title">🌈 지금 공기 상태는 어떨까요?</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 2])

with col_a:
    st.markdown(
        f"""
        <div class="big-card">
            <div class="card-title">오늘의 공기 점수</div>
            <div class="card-value">{score}점</div>
            <div class="small-text">점수가 높을수록 공기가 좋아요</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_b:
    st.markdown(
        f"""
        <div style="
            background:{status_color};
            padding:28px;
            border-radius:22px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
            text-align:center;
            color:white;
            font-weight:800;
            font-size:32px;">
            {status_text}
            <div style="font-size:18px; margin-top:10px; font-weight:600;">
                {format_date_with_korean_day(latest["날짜시간"])}
            </div>
            <div style="font-size:16px; margin-top:8px; font-weight:500;">
                선택한 지역의 공기 상태를 한눈에 보여줘요
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# 12. 안내 문구
# -----------------------------
selected_regions_text = ", ".join(selected_regions) if selected_regions else "전체 지역"
selected_stations_text = ", ".join(selected_stations) if selected_stations else "전체 측정소"

st.info(
    f"📌 지금은 **{selected_regions_text}** 지역과 **{selected_stations_text}** 측정소 데이터를 보고 있어요. "
    f"조회 기간은 **{start_date} ~ {end_date}** 입니다."
)

# -----------------------------
# 13. 주요 숫자 카드
# -----------------------------
st.markdown('<div class="section-title">📊 중요한 숫자를 먼저 볼까요?</div>', unsafe_allow_html=True)

pm10_avg = filtered_df["PM10"].mean()
pm25_avg = filtered_df["PM25"].mean()
o3_avg = filtered_df["O3"].mean()
count_data = len(filtered_df)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="big-card">
            <div class="card-title">😷 미세먼지 평균</div>
            <div class="card-value">{pm10_avg:.1f}</div>
            <div class="small-text">숫자가 높을수록 먼지가 많아요</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div class="big-card">
            <div class="card-title">🌫️ 초미세먼지 평균</div>
            <div class="card-value">{pm25_avg:.1f}</div>
            <div class="small-text">아주 작은 먼지예요</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="big-card">
            <div class="card-title">☀️ 오존 평균</div>
            <div class="card-value">{o3_avg:.3f}</div>
            <div class="small-text">햇빛과 관련 있는 공기 성분이에요</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"""
        <div class="big-card">
            <div class="card-title">📦 데이터 개수</div>
            <div class="card-value">{count_data:,}</div>
            <div class="small-text">살펴본 기록의 수예요</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# 14. 탭 구성
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📈 변화 보기", "🏙️ 지역 비교", "📋 데이터와 설명"])

# -----------------------------
# 15. 탭 1 - 변화 보기
# -----------------------------
with tab1:
    st.markdown('<div class="section-title">📈 시간에 따라 공기가 어떻게 바뀔까요?</div>', unsafe_allow_html=True)

    fig_pm10 = px.line(
        filtered_df,
        x="날짜시간",
        y="PM10",
        color="측정소명",
        markers=True,
        title="시간별 미세먼지 변화"
    )
    fig_pm10.update_layout(
        xaxis_title="날짜와 시간",
        yaxis_title="미세먼지(PM10)",
        template="plotly_white",
        title_x=0.1
    )
    st.plotly_chart(fig_pm10, use_container_width=True)

    st.success("선이 높아질수록 공기 속 먼지가 많아졌다는 뜻이에요.")

    st.markdown('<div class="section-title">🔍 미세먼지와 초미세먼지는 함께 움직일까요?</div>', unsafe_allow_html=True)

    fig_scatter = px.scatter(
        filtered_df,
        x="PM10",
        y="PM25",
        color="측정소명",
        opacity=0.65,
        title="미세먼지와 초미세먼지 비교"
    )
    fig_scatter.update_layout(
        xaxis_title="미세먼지(PM10)",
        yaxis_title="초미세먼지(PM25)",
        template="plotly_white",
        title_x=0.1
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.info("점들이 오른쪽 위로 많으면 두 값이 함께 커지는 경우가 많다고 볼 수 있어요.")

# -----------------------------
# 16. 탭 2 - 지역 비교
# -----------------------------
with tab2:
    st.markdown('<div class="section-title">🏙️ 어느 지역의 공기 값이 더 클까요?</div>', unsafe_allow_html=True)

    regional_source = df[
        (df["날짜"] >= start_date) &
        (df["날짜"] <= end_date)
    ].copy()

    if selected_regions:
        regional_source = regional_source[regional_source["지역"].isin(selected_regions)]

    regional_avg = regional_source.groupby("지역")[["PM10", "PM25", "O3", "NO2"]].mean().reset_index()

    regional_long = regional_avg.melt(
        id_vars="지역",
        var_name="공기 종류",
        value_name="평균값"
    )

    fig_bar = px.bar(
        regional_long,
        x="지역",
        y="평균값",
        color="공기 종류",
        barmode="group",
        title="지역별 공기 상태 비교"
    )
    fig_bar.update_layout(
        xaxis_title="지역",
        yaxis_title="평균값",
        template="plotly_white",
        title_x=0.1
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.warning("막대가 높을수록 그 지역의 값이 더 큰 거예요.")

# -----------------------------
# 17. 탭 3 - 데이터와 설명
# -----------------------------
with tab3:
    st.markdown('<div class="section-title">📋 직접 데이터도 볼 수 있어요</div>', unsafe_allow_html=True)

    show_cols = ["지역", "측정소명", "날짜시간", "요일", "PM10", "PM25", "O3", "NO2"]

    st.dataframe(
        filtered_df[show_cols],
        use_container_width=True,
        hide_index=True
    )

    csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 필터링된 데이터 CSV 다운로드",
        data=csv_data,
        file_name="air_quality_filtered_data.csv",
        mime="text/csv"
    )

    st.markdown('<div class="section-title">🎓 어려운 말도 쉽게 알아봐요</div>', unsafe_allow_html=True)

    with st.expander("미세먼지는 뭐예요?"):
        st.write("미세먼지는 공기 중에 떠다니는 아주 작은 먼지예요.")
        st.write("숫자가 높을수록 공기가 탁할 수 있어요.")

    with st.expander("초미세먼지는 뭐예요?"):
        st.write("초미세먼지는 미세먼지보다 더 작아요.")
        st.write("그래서 몸속 깊이 들어갈 수 있어요.")

    with st.expander("오존은 뭐예요?"):
        st.write("오존은 햇빛 때문에 만들어질 수 있는 공기 성분이에요.")
        st.write("너무 많으면 숨쉬기 불편할 수 있어요.")

    with st.expander("그래프는 어떻게 보면 되나요?"):
        st.write("선이 높으면 값이 큰 거예요.")
        st.write("막대가 높으면 그 지역 평균이 더 큰 거예요.")
        st.write("점이 오른쪽 위에 많으면 두 값이 함께 큰 경우가 많아요.")

# -----------------------------
# 18. 발표 마무리 문구
# -----------------------------
st.divider()
st.markdown(
    """
    <div style="text-align:center; font-size:20px; font-weight:700; color:#1f4e79; margin-top:10px;">
        🌟 발표 한 줄 정리: 공기 데이터는 시간과 지역에 따라 달라질 수 있어요!
    </div>
    """,
    unsafe_allow_html=True
)
