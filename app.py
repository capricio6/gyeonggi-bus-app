import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation
import urllib.parse
import math
import time
import pandas as pd
import os
import glob

try:
    api_key = st.secrets.get("API_KEY")
except Exception:
    api_key = None

if not api_key:
    api_key = os.environ.get("API_KEY", "a632cce2ef4ce525623e1348ef4502304284bf10dc238e36efe7925a3c59323b")

st.set_page_config(page_title="경기버스 실시간", page_icon="🚌", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');

* { font-family: 'Pretendard', 'Noto Sans KR', sans-serif !important; }

/* 전체 배경 */
.stApp { background: #F0F4FF !important; }
[data-testid="stAppViewContainer"] > .main { background: #F0F4FF !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* 사이드바 숨기기 */
[data-testid="collapsedControl"] { display: none; }

/* 헤더 타이틀 */
h1 {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    color: #1A1D2E !important;
    letter-spacing: -0.5px;
    margin-bottom: 4px !important;
    padding-bottom: 0 !important;
    border: none !important;
}
h2 {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #1A1D2E !important;
    margin-top: 20px !important;
}
h3 { font-size: 1rem !important; font-weight: 600 !important; color: #3D4166 !important; }

/* caption */
[data-testid="stCaptionContainer"] p {
    font-size: 0.75rem !important;
    color: #8B8FA8 !important;
    font-weight: 400 !important;
}

/* 검색 입력창 */
[data-testid="stTextInput"] input {
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: #1A1D2E !important;
    background: #FFFFFF !important;
    border: 1.5px solid #D8DCF0 !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 0 2px 8px rgba(80,100,200,0.06) !important;
    transition: border 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border: 1.5px solid #4B6BF5 !important;
    box-shadow: 0 0 0 3px rgba(75,107,245,0.12) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #B0B5CC !important; }

/* Form 배경 제거 */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* 버튼 — 기본 (정류소, 버스 카드) */
.stButton > button {
    background: #FFFFFF !important;
    color: #1A1D2E !important;
    border: 1.5px solid #E2E5F5 !important;
    border-radius: 14px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 12px 14px !important;
    width: 100% !important;
    text-align: left !important;
    line-height: 1.5 !important;
    box-shadow: 0 2px 8px rgba(80,100,200,0.05) !important;
    transition: all 0.15s ease !important;
    white-space: pre-wrap !important;
}
.stButton > button:hover {
    background: #F5F7FF !important;
    border-color: #4B6BF5 !important;
    box-shadow: 0 4px 16px rgba(75,107,245,0.12) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* 검색 버튼 */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #4B6BF5, #7B55F0) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    padding: 14px 20px !important;
    box-shadow: 0 4px 16px rgba(75,107,245,0.35) !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 6px 20px rgba(75,107,245,0.45) !important;
    transform: translateY(-1px) !important;
}

/* 구분선 */
hr { border: none !important; border-top: 1px solid #E2E5F5 !important; margin: 16px 0 !important; }

/* info / warning / error 박스 */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: none !important;
    font-weight: 500 !important;
}

/* Metric 카드 */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    border: 1.5px solid #E2E5F5 !important;
    box-shadow: 0 2px 8px rgba(80,100,200,0.05) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #4B6BF5 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    color: #8B8FA8 !important;
    font-weight: 500 !important;
}

/* spinner 텍스트 */
[data-testid="stSpinner"] p { color: #4B6BF5 !important; font-weight: 500 !important; }

/* 전체 패딩 조정 */
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 960px !important; }
</style>
""", unsafe_allow_html=True)

# ===== 세션 상태 초기화 =====
defaults = {
    'stops': [], 'map_center': None, 'search_mode': None,
    'selected_stop': None, 'selected_bus_id': None,
    'favorites': [], 'last_place_name': "", 'view_mode': 'search',
    'search_matches': None, 'last_update': time.time()
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

@st.cache_data
def load_gyeonggi_stops_csv():
    csv_files = glob.glob('*.csv') + glob.glob('**/*.csv', recursive=True)
    if not csv_files:
        return None, "❌ CSV 파일을 찾을 수 없습니다."
    csv_file = max(csv_files, key=lambda f: os.path.getsize(f))
    try:
        try:
            df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', quotechar='"', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', quotechar='"', encoding='cp949')
        df = df[df.apply(lambda x: len(x) == 9, axis=1)].copy()
        if df.empty: return None, "❌ 유효한 데이터가 없습니다."
        df.columns = ['raw_id', 'name', 'lat', 'lon', 'date', 'ars', 'city_code', 'city', 'admin']
        df = df[df['city'].str.contains("경기도", na=False)].copy()
        df['stationId'] = df['raw_id'].astype(str).str.replace(r'\D', '', regex=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df['ars'] = df['ars'].fillna('').astype(str).str.strip()
        df = df[(df['lat'] != 0) & (df['lon'] != 0) & df['lat'].notna() & df['lon'].notna()]
        return df, f"✅ {len(df):,}개 정류소 로딩 완료"
    except Exception as e:
        return None, f"❌ 파싱 오류: {str(e)}"

def fetch_bus_stops_around(lat, lon, radius=500):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationAroundListv2"
    params = {"serviceKey": decoded_key, "pageNo": 1, "numOfRows": 50, "x": lon, "y": lat, "radius": radius, "_type": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return []
        data = res.json()
        header = data.get('response', {}).get('msgHeader', {})
        if str(header.get('resultCode', 99)) != '0': return []
        items = data.get('response', {}).get('msgBody', {}).get('busStationAroundList', [])
        return (items if isinstance(items, list) else [items]) if items else []
    except: return []

def fetch_bus_arrival(station_id):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/busarrivalservice/v2/getBusArrivalListv2"
    params = {"serviceKey": decoded_key, "stationId": str(station_id), "_type": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return []
        data = res.json()
        header = data.get('response', {}).get('msgHeader', {})
        if str(header.get('resultCode', 99)) != '0': return []
        arrivals = data.get('response', {}).get('msgBody', {}).get('busArrivalList', [])
        return (arrivals if isinstance(arrivals, list) else [arrivals]) if arrivals else []
    except: return []

def fetch_bus_locations(route_id):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2"
    params = {"serviceKey": decoded_key, "routeId": str(route_id), "pageNo": 1, "numOfRows": 50, "_type": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return []
        data = res.json()
        header = data.get('response', {}).get('msgHeader', {})
        if str(header.get('resultCode', 99)) != '0': return []
        buses = data.get('response', {}).get('msgBody', {}).get('busLocationList', [])
        return (buses if isinstance(buses, list) else [buses]) if buses else []
    except: return []

def fetch_route_stops(route_id):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2"
    params = {"serviceKey": decoded_key, "routeId": str(route_id), "pageNo": 1, "numOfRows": 200, "_type": "json"}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code != 200: return []
        data = res.json()
        header = data.get('response', {}).get('msgHeader', {})
        if str(header.get('resultCode', 99)) != '0': return []
        body = data.get('response', {}).get('msgBody', {})
        stops = body.get('busRouteStationList', body.get('items', []))
        return (stops if isinstance(stops, list) else [stops]) if stops else []
    except: return []

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def simulate_eta_route_based(route_stops_list, bus_seq, target_seq, avg_speed_kmh=20, dwell_sec=20):
    segment_stops = [s for s in route_stops_list if bus_seq <= int(s.get('stationSeq', 0)) <= target_seq]
    segment_stops.sort(key=lambda x: int(x.get('stationSeq', 0)))
    total_dist = 0
    if len(segment_stops) > 1:
        for i in range(len(segment_stops) - 1):
            lat1 = float(segment_stops[i].get('y', segment_stops[i].get('stationY', 0)))
            lon1 = float(segment_stops[i].get('x', segment_stops[i].get('stationX', 0)))
            lat2 = float(segment_stops[i+1].get('y', segment_stops[i+1].get('stationY', 0)))
            lon2 = float(segment_stops[i+1].get('x', segment_stops[i+1].get('stationX', 0)))
            total_dist += haversine(lat1, lon1, lat2, lon2) * 1.3
    est_stops = max(1, len(segment_stops) - 1)
    travel_sec = total_dist / (avg_speed_kmh / 3.6)
    dwell_total_sec = est_stops * dwell_sec
    total_min = (travel_sec + dwell_total_sec) / 60
    segment_coords = [(float(s.get('y', s.get('stationY', 0))), float(s.get('x', s.get('stationX', 0)))) for s in segment_stops]
    return max(0.5, round(total_min, 1)), round(total_dist), est_stops, segment_coords

def arrival_class(minutes):
    try:
        m = int(minutes)
    except (ValueError, TypeError):
        m = 999
    if m == 0: return "arriving", "🟢 도착"
    elif m <= 3: return "soon", f"🟢 {m}분"
    elif m <= 10: return "close", f"🟡 {m}분"
    elif m <= 20: return "medium", f"🟠 {m}분"
    else: return "far", f"⚪ {m}분"

def smart_search_stops(query):
    query_clean = query.strip()
    df, db_status = load_gyeonggi_stops_csv()
    results = []
    if df is not None and not df.empty:
        if query_clean.isdigit():
            mask = (df['ars'] == query_clean) | (df['stationId'] == query_clean)
        else:
            mask = df['name'].str.contains(query_clean, na=False)
        matched = df[mask]
        for _, row in matched.iterrows():
            results.append({
                'id': str(row['stationId']), 'name': str(row['name']),
                'lat': float(row['lat']), 'lon': float(row['lon']), 'ars': str(row['ars'])
            })
    if not results:
        decoded_key = urllib.parse.unquote(api_key)
        url = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2"
        params = {"serviceKey": decoded_key, "stationName": query_clean, "pageNo": 1, "numOfRows": 50, "_type": "json"}
        try:
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                data = res.json()
                header = data.get('response', {}).get('msgHeader', {})
                if str(header.get('resultCode', 99)) == '0':
                    items = data.get('response', {}).get('msgBody', {}).get('busStationList', [])
                    if items:
                        for item in (items if isinstance(items, list) else [items]):
                            results.append({
                                'id': str(item.get('stationId', '')), 'name': item.get('stationName', ''),
                                'lat': float(item.get('y', 0)), 'lon': float(item.get('x', 0)),
                                'ars': str(item.get('mobileNo', ''))
                            })
        except: pass
    if not results and not query_clean.isdigit():
        geo = Nominatim(user_agent="bus_app", timeout=10)
        for q in [f"{query_clean} 파주시 경기도", f"{query_clean} 경기도", query_clean]:
            try:
                loc = geo.geocode(q, language='ko')
                if loc:
                    return [{'id': 'ADDR', 'name': q, 'lat': loc.latitude, 'lon': loc.longitude, 'ars': '', 'is_addr': True}], db_status
            except: pass
    unique_results, seen = [], set()
    for r in results:
        key = (round(r['lat'], 5), round(r['lon'], 5))
        if key not in seen: seen.add(key); unique_results.append(r)
    return unique_results, db_status

def run_search_around(lat, lon, mode, place_name=""):
    st.session_state.map_center = [lat, lon]
    st.session_state.search_mode = mode
    st.session_state.last_place_name = place_name
    st.session_state.view_mode = 'search'
    st.session_state.selected_stop = None
    st.session_state.selected_bus_id = None
    st.session_state.search_matches = None
    with st.spinner("주변 정류소 검색 중..."):
        st.session_state.stops = fetch_bus_stops_around(lat, lon)

# ===== 헤더 =====
st.markdown("""
<div style="margin-bottom: 6px;">
  <span style="font-size:2rem;">🚌</span>
  <span style="font-size:1.7rem; font-weight:800; color:#1A1D2E; letter-spacing:-0.5px; margin-left:8px;">경기버스 실시간</span>
</div>
""", unsafe_allow_html=True)

df_check, db_status = load_gyeonggi_stops_csv()
st.caption(f"🗄️ {db_status}")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ===== 검색 폼 =====
with st.form(key='search_form'):
    col_s1, col_s2 = st.columns([5, 1])
    with col_s1:
        place = st.text_input("", key="search_input", placeholder="🔍  정류장명 또는 5자리 번호 입력")
    with col_s2:
        submit_button = st.form_submit_button("검색")
    if submit_button:
        place_val = st.session_state.search_input
        if place_val:
            with st.spinner("검색 중..."):
                matches, status = smart_search_stops(place_val)
                if matches:
                    if len(matches) == 1 and not matches[0].get('is_addr'):
                        s = matches[0]
                        st.session_state.selected_stop = {"id": s['id'], "name": s['name'], "lat": s['lat'], "lon": s['lon']}
                        st.session_state.map_center = [s['lat'], s['lon']]
                        st.session_state.view_mode = 'detail'
                    elif len(matches) == 1 and matches[0].get('is_addr'):
                        run_search_around(matches[0]['lat'], matches[0]['lon'], "place", matches[0]['name'])
                    else:
                        st.session_state.search_matches = matches
                        st.session_state.view_mode = 'matches'
                else:
                    st.session_state.view_mode = 'no_matches'

col_g1, col_g2 = st.columns([5, 1])
with col_g2:
    if st.button("📍 내 위치", key="btn_gps"):
        with st.spinner("위치 확인 중..."):
            loc = get_geolocation()
            if loc and 'coords' in loc:
                run_search_around(loc['coords']['latitude'], loc['coords']['longitude'], "gps", "내 위치")
            else:
                st.error("위치 권한을 허용해주세요.")

st.markdown("<hr>", unsafe_allow_html=True)

# ===== 검색 결과 여러 개 =====
if st.session_state.view_mode == 'matches' and st.session_state.search_matches:
    st.markdown(f"**🔍 검색 결과 {len(st.session_state.search_matches)}개**")
    cols = st.columns(min(len(st.session_state.search_matches), 2))
    for i, s in enumerate(st.session_state.search_matches):
        with cols[i % 2]:
            ars_str = f"  |  번호 {s['ars']}" if s['ars'] and s['ars'] != '0' else ""
            label = f"🚏  {s['name']}{ars_str}"
            if st.button(label, key=f"match_btn_{i}"):
                if s.get('is_addr'):
                    run_search_around(s['lat'], s['lon'], "place", s['name'])
                else:
                    st.session_state.selected_stop = {"id": s['id'], "name": s['name'], "lat": s['lat'], "lon": s['lon']}
                    st.session_state.map_center = [s['lat'], s['lon']]
                    st.session_state.view_mode = 'detail'
                st.rerun()

elif st.session_state.view_mode == 'no_matches':
    st.error("😔 검색 결과가 없습니다. 다른 이름으로 검색해보세요.")

# ===== 주변 정류소 목록 =====
elif st.session_state.view_mode == 'search':
    if st.session_state.favorites:
        st.markdown("**⭐ 즐겨찾기**")
        cols = st.columns(min(len(st.session_state.favorites), 3))
        for i, fav in enumerate(st.session_state.favorites):
            with cols[i % 3]:
                if st.button(f"📍  {fav['name']}", key=f"fav_btn_{i}"):
                    st.session_state.selected_stop = fav
                    st.session_state.view_mode = 'detail'
                    st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    if not st.session_state.stops:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color:#B0B5CC;">
            <div style="font-size:3rem; margin-bottom:12px;">🚌</div>
            <div style="font-size:1rem; font-weight:600; color:#8B8FA8;">정류장명 검색 또는 내 위치 버튼을 누르세요</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"**🚏 주변 정류소** &nbsp;<span style='color:#8B8FA8; font-size:0.85rem; font-weight:400;'>{len(st.session_state.stops)}개</span>", unsafe_allow_html=True)
        sorted_stops = sorted(st.session_state.stops, key=lambda x: float(x.get('distance', 9999)) if st.session_state.search_mode == "gps" else x.get('stationName', ''))
        cols = st.columns(3)
        for i, s in enumerate(sorted_stops):
            with cols[i % 3]:
                name = s.get('stationName', '이름없음')
                sid = str(s.get('stationId', ''))
                dist = s.get('distance', '')
                mobile = s.get('mobileNo', '')
                mobile_str = f"  |  {mobile}번" if mobile and mobile != '0' else ""
                dist_str = f"  📏 {int(dist)}m" if dist else ""
                label = f"🚏  {name}{mobile_str}\n{dist_str}"
                if st.button(label, key=f"btn_stop_{sid}_{i}"):
                    st.session_state.selected_stop = {"id": sid, "name": name, "lat": float(s.get('y', 0)), "lon": float(s.get('x', 0))}
                    st.session_state.map_center = [float(s.get('y', 0)), float(s.get('x', 0))]
                    st.session_state.view_mode = 'detail'
                    st.rerun()

# ===== 정류소 상세 =====
elif st.session_state.view_mode == 'detail' and st.session_state.selected_stop:
    sel = st.session_state.selected_stop
    current_time = time.time()
    if current_time - st.session_state.last_update > 60:
        st.session_state.last_update = current_time
        st.rerun()

    col_back, col_fav = st.columns([4, 1])
    with col_back:
        if st.button("← 목록으로", key="btn_back"):
            st.session_state.view_mode = 'search'
            st.session_state.selected_bus_id = None
            st.rerun()
    with col_fav:
        is_fav = any(f['id'] == sel['id'] for f in st.session_state.favorites)
        if is_fav:
            if st.button("⭐ 해제", key="btn_unfav"):
                st.session_state.favorites = [f for f in st.session_state.favorites if f['id'] != sel['id']]
                st.rerun()
        else:
            if st.button("☆ 저장", key="btn_fav"):
                st.session_state.favorites.append(sel)
                st.rerun()

    st.markdown(f"""
    <div style="background:#FFFFFF; border-radius:18px; border:1.5px solid #E2E5F5;
                padding:18px 22px; margin:10px 0 16px 0;
                box-shadow:0 2px 12px rgba(80,100,200,0.07);">
        <div style="font-size:1.25rem; font-weight:800; color:#1A1D2E; margin-bottom:4px;">📍 {sel['name']}</div>
        <div style="font-size:0.78rem; color:#8B8FA8; font-weight:400;">
            정류소 ID: {sel['id']} &nbsp;·&nbsp; 업데이트: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**🚌 운행 노선**")
    with st.spinner("노선 정보 불러오는 중..."):
        arrivals = fetch_bus_arrival(sel['id'])
        if not arrivals:
            st.info("현재 운행 중인 버스 정보가 없습니다.")
        else:
            cols = st.columns(3)
            for i, bus in enumerate(arrivals):
                with cols[i % 3]:
                    route_name = bus.get('routeName', '미상')
                    route_id = bus.get('routeId', '')
                    t1, t2 = bus.get('predictTime1'), bus.get('predictTime2')
                    cls1, str1 = arrival_class(t1)
                    cls2, str2 = arrival_class(t2)
                    label = f"🚌  {route_name}번\n첫번째 {str1}  /  두번째 {str2}"
                    if st.button(label, key=f"btn_bus_{route_id}_{i}", use_container_width=True):
                        st.session_state.selected_bus_id = route_id

    # ===== 버스 시뮬레이션 =====
    if st.session_state.selected_bus_id:
        selected_bus_info = next((b for b in arrivals if b.get('routeId') == st.session_state.selected_bus_id), None)
        if selected_bus_info:
            route_name = selected_bus_info.get('routeName', '미상')
            route_id = selected_bus_info.get('routeId', '')
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"**🗺️ {route_name}번 실시간 경로**")
            with st.spinner("경로 분석 중..."):
                buses = fetch_bus_locations(route_id)
                route_stops_list = fetch_route_stops(route_id)
                if not buses or not route_stops_list:
                    st.warning("실시간 정보를 가져올 수 없습니다.")
                else:
                    target_stop = next((s for s in route_stops_list if str(s.get('stationId')) == str(sel['id'])), None)
                    if not target_stop:
                        st.error("목표 정류소 정보를 찾을 수 없습니다.")
                    else:
                        target_seq = int(target_stop.get('stationSeq', 0))
                        target_lat = float(target_stop.get('stationY', target_stop.get('y', 0)))
                        target_lon = float(target_stop.get('stationX', target_stop.get('x', 0)))
                        best_bus, min_diff = None, 9999
                        for bus in buses:
                            bus_station_id = bus.get('stationId')
                            bus_stop_data = next((s for s in route_stops_list if str(s.get('stationId')) == str(bus_station_id)), None)
                            if bus_stop_data:
                                bus_seq = int(bus_stop_data.get('stationSeq', 0))
                                diff = target_seq - bus_seq
                                if 0 < diff < min_diff:
                                    min_diff = diff
                                    best_bus = bus
                                    best_bus_seq = bus_seq
                                    best_bus_lat = float(bus_stop_data.get('stationY', bus_stop_data.get('y', 0)))
                                    best_bus_lon = float(bus_stop_data.get('stationX', bus_stop_data.get('x', 0)))
                        if best_bus:
                            sim_min, road_dist_m, est_stops, segment_coords = simulate_eta_route_based(route_stops_list, best_bus_seq, target_seq)
                            if road_dist_m > 150000 or est_stops > 50 or sim_min > 120:
                                st.info("🚌 먼 거리 운행 중이거나 위치 정보가 불안정합니다.")
                            else:
                                route_coords = [(float(s.get('y', s.get('stationY', 0))), float(s.get('stationX', s.get('stationX', 0)))) for s in route_stops_list]
                                center_lat = (best_bus_lat + target_lat) / 2
                                center_lon = (best_bus_lon + target_lon) / 2
                                m_detail = folium.Map(location=[center_lat, center_lon], zoom_start=16,
                                                      tiles='CartoDB positron')
                                folium.PolyLine(route_coords, color='#CBD0F0', weight=3, opacity=0.6, dash_array='6,4').add_to(m_detail)
                                if segment_coords:
                                    folium.PolyLine(segment_coords, color='#4B6BF5', weight=6, opacity=0.95).add_to(m_detail)
                                folium.Marker([best_bus_lat, best_bus_lon],
                                              popup=f"{route_name}번 현재 위치",
                                              icon=folium.Icon(color='red', icon='bus', prefix='fa')).add_to(m_detail)
                                folium.Marker([target_lat, target_lon],
                                              popup=f"도착: {sel['name']}",
                                              icon=folium.Icon(color='blue', icon='star', prefix='fa')).add_to(m_detail)
                                st_folium(m_detail, width=None, height=420)
                                st.markdown("<hr>", unsafe_allow_html=True)
                                c1, c2, c3 = st.columns(3)
                                with c1: st.metric("노선", f"{route_name}번")
                                with c2: st.metric("남은 정류소", f"{est_stops}개")
                                with c3: st.metric("예상 도착", f"{sim_min}분 후")
                        else:
                            st.info("🚌 해당 노선 버스가 반대 방향이거나 운행 중이 아닙니다.")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#B0B5CC; font-size:0.78rem; font-weight:400;'>경기버스 실시간 도착 정보 · Made with ❤️</p>", unsafe_allow_html=True)
