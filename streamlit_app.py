import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

# -----------------------------
# 1. 화면 기본 설정
# -----------------------------
st.set_page_config(
    page_title="우리 동네 공기 보기",
    page_icon="🌤️",
    layout="wide"
)

st.title("🌤️ 우리 동네 공기 보기")
st.write("2025년 1월 공기 데이터를 쉽게 살펴보는 화면이에요!")
st.write("왼쪽에서 지역과 측정소를 고르면 공기 상태를 볼 수 있어요.")

# -----------------------------
# 2. 데이터 불러오기
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

    pollutants = ["SO2", "CO", "O3", "NO2", "PM10", "PM25"]
    for p in pollutants:
        df[p] = pd.to_numeric(df[p], errors="coerce")

    return df

# 파일 경로
data_path = Path("data/202501-air.csv")
if not data_path.exists():
    data_path = Path("202501-air.csv")

try:
    df = load_air_data(data_path)
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요: {e}")
    st.stop()

# -----------------------------
# 3. 사이드바
# -----------------------------
with st.sidebar:
    st.header("🎛️ 선택하기")

    all_regions = sorted(df["지역"].dropna().unique())
    selected_regions = st.multiselect(
        "어느 지역을 볼까요?",
        options=all_regions,
        default=all_regions[:2] if len(all_regions) >= 2 else all_regions
    )

    if selected_regions:
        station_df = df[df["지역"].isin(selected_regions)]
    else:
        station_df = df.copy()

    all_stations = sorted(station_df["측정소명"].dropna().unique())
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

# 날짜 처리
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

# -----------------------------
# 4. 데이터 고르기
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
# 5. 쉬운 설명
# -----------------------------
st.subheader("📝 지금 보고 있는 내용")
st.write(
    f"선택한 지역: {', '.join(selected_regions) if selected_regions else '전체'} / "
    f"측정소 수: {len(selected_stations) if selected_stations else len(all_stations)}개"
)

# -----------------------------
# 6. 큰 숫자로 보여주기
# -----------------------------
pm10_avg = filtered_df["PM10"].mean()
pm25_avg = filtered_df["PM25"].mean()
o3_avg = filtered_df["O3"].mean()
count_data = len(filtered_df)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("😷 미세먼지 평균", f"{pm10_avg:.1f}")
    st.caption("숫자가 높을수록 먼지가 많아요.")

with col2:
    st.metric("🌫️ 초미세먼지 평균", f"{pm25_avg:.1f}")
    st.caption("아주 작은 먼지예요.")

with col3:
    st.metric("☀️ 오존 평균", f"{o3_avg:.3f}")
    st.caption("햇빛과 만나 만들어지는 공기 성분이에요.")

with col4:
    st.metric("📦 데이터 개수", f"{count_data:,}")
    st.caption("살펴본 기록 수예요.")

st.divider()

# -----------------------------
# 7. 그래프 1 - 시간에 따라 어떻게 달라질까?
# -----------------------------
st.subheader("📈 시간에 따라 미세먼지가 어떻게 달라질까요?")

fig_pm10 = px.line(
    filtered_df,
    x="날짜시간",
    y="PM10",
    color="측정소명",
    markers=True
)
fig_pm10.update_layout(
    xaxis_title="시간",
    yaxis_title="미세먼지(PM10)",
    title="시간별 미세먼지 변화"
)
st.plotly_chart(fig_pm10, use_container_width=True)

st.info("그래프의 선이 높아질수록 공기 속 먼지가 많아진다는 뜻이에요.")

# -----------------------------
# 8. 그래프 2 - 미세먼지와 초미세먼지는 비슷할까?
# -----------------------------
st.subheader("🔍 미세먼지와 초미세먼지는 비슷하게 움직일까요?")

fig_scatter = px.scatter(
    filtered_df,
    x="PM10",
    y="PM25",
    color="측정소명",
    opacity=0.6
)
fig_scatter.update_layout(
    xaxis_title="미세먼지(PM10)",
    yaxis_title="초미세먼지(PM25)",
    title="미세먼지와 초미세먼지 비교"
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.info("점들이 오른쪽 위로 모일수록 두 값이 함께 커지는 경우가 많아요.")

# -----------------------------
# 9. 그래프 3 - 어느 지역 공기가 더 나쁠까?
# -----------------------------
st.subheader("🏙️ 지역별 평균 공기 비교")

regional_avg = df[
    (df["날짜"] >= start_date) & (df["날짜"] <= end_date)
].groupby("지역")[["PM10", "PM25", "O3", "NO2"]].mean().reset_index()

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
    barmode="group"
)
fig_bar.update_layout(
    xaxis_title="지역",
    yaxis_title="평균값",
    title="지역별 공기 상태 비교"
)
st.plotly_chart(fig_bar, use_container_width=True)

st.info("막대가 높을수록 그 지역의 값이 더 큰 거예요.")

# -----------------------------
# 10. 데이터 표
# -----------------------------
st.subheader("📋 직접 데이터 보기")
st.write("아래 표에서 실제 측정값을 볼 수 있어요.")

show_cols = ["지역", "측정소명", "날짜시간", "PM10", "PM25", "O3", "NO2"]
st.dataframe(
    filtered_df[show_cols],
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# 11. 쉬운 설명 상자
# -----------------------------
st.subheader("🎓 이것만 알면 돼요!")

with st.expander("미세먼지와 초미세먼지가 뭐예요?"):
    st.write("미세먼지는 공기 중에 떠다니는 아주 작은 먼지예요.")
    st.write("초미세먼지는 그보다 더 작아서 몸속 깊이 들어갈 수 있어요.")

with st.expander("오존은 뭐예요?"):
    st.write("오존은 햇빛 때문에 만들어질 수 있는 공기 성분이에요.")
    st.write("너무 많으면 숨 쉬기 불편할 수 있어요.")

with st.expander("그래프는 어떻게 보면 되나요?"):
    st.write("선이 높으면 값이 큰 거예요.")
    st.write("막대가 높으면 그 지역의 평균이 더 큰 거예요.")
    st.write("점이 오른쪽 위에 많으면 두 값이 함께 큰 경우가 많아요.")
