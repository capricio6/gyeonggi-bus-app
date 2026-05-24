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

# 📱 방송국 설정
st.set_page_config(page_title="경기버스 실시간 정보", page_icon="🚌", layout="wide")

# 🎨 파스텔 블루 & 진한 검정 테마 (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700;900&display=swap');
    .main { background-color: #E3F2FD; }
    * { font-family: 'Noto Sans KR', sans-serif !important; color: #000000 !important; font-weight: 700 !important; }
    h1 { color: #000000 !important; font-size: 2.2rem; font-weight: 900; margin-bottom: 20px; border-bottom: 4px solid #1565C0; padding-bottom: 10px; }
    h2, h3 { color: #000000 !important; font-weight: 900; font-size: 1.5rem; margin-top: 15px; }
    .stForm { background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 2px solid #90CAF9; margin-bottom: 20px; }
    .stTextInput > div > div > input { font-size: 20px !important; padding: 15px !important; border-radius: 8px !important; border: 3px solid #1565C0 !important; background-color: #FFFFFF; color: #000000 !important; font-weight: 900; }
    .stButton > button { 
        background-color: #1565C0 !important; color: #FFFFFF !important; border-radius: 8px !important;
        border: none !important; font-weight: 900 !important; font-size: 16px !important; 
        padding: 12px 10px !important; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stButton > button:hover { background-color: #0D47A1 !important; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #000000 !important; font-weight: 900; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem !important; color: #424242 !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# 🕵️‍♂️ API 키 설정 (반드시 실제 키로 변경하세요!)
api_key = "여기에 API"

# ===== 세션 상태 초기화 =====
defaults = {
    'stops': [], 'map_center': None, 'search_mode': None, 
    'selected_stop': None, 'selected_bus_id': None, 
    'favorites': [], 'last_place_name': "", 'view_mode': 'search',
    'search_matches': None, 'last_update': time.time()
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

# ========================================
# 📂 국토교통부 CSV 데이터 로딩
# ========================================
@st.cache_data
def load_molit_csv():
    csv_files = glob.glob('*.csv') + glob.glob('**/*.csv', recursive=True)
    if not csv_files: 
        return None, "❌ CSV 파일을 찾을 수 없습니다."
    
    csv_file = max(csv_files, key=lambda f: os.path.getsize(f))
    
    try:
        try:
            df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', quotechar='"', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', quotechar='"', encoding='cp949')
            
        df = df[df.apply(lambda x: 8 <= len(x) <= 10, axis=1)].copy()
        if df.empty: return None, f"❌ 유효한 데이터가 없습니다."
            
        df = df.iloc[:, :9]
        df.columns = ['raw_id', 'name', 'lat', 'lon', 'date', 'ars', 'city_code', 'city', 'admin']
        df['stationId'] = df['raw_id'].astype(str).str.replace(r'\D', '', regex=True)
        df['name'] = df['name'].fillna('').astype(str).str.strip()
        df['ars'] = df['ars'].fillna('').astype(str).str.strip()
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df[(df['lat'] != 0) & (df['lon'] != 0) & df['lat'].notna() & df['lon'].notna()]
        return df, f"✅ DB 로딩 성공: {os.path.basename(csv_file)} ({len(df):,}건)"
    except Exception as e:
        return None, f"❌ 파싱 오류: {str(e)}"

# ========================================
# 🔧 경기버스 API 호출 함수들
# ========================================
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

# ========================================
# 🛣️ 노선 기반 시뮬레이션 엔진 (회차지/우회 완벽 반영)
# ========================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def simulate_eta_route_based(route_stops_list, bus_seq, target_seq, avg_speed_kmh=20, dwell_sec=20):
    """
    버스가 실제로 지나가야 하는 정류소들을 순서대로 연결하여 누적 거리를 계산합니다.
    회차지나 우회 구간도 정류소 좌표를 따라가므로 자연스럽게 반영됩니다.
    """
    # 1. 현재 버스 위치부터 목표 정류소까지의 구간 정류소만 필터링
    segment_stops = [s for s in route_stops_list if bus_seq <= int(s.get('stationSeq', 0)) <= target_seq]
    # 2. 순번(stationSeq) 기준으로 정렬
    segment_stops.sort(key=lambda x: int(x.get('stationSeq', 0)))
    
    total_dist = 0
    if len(segment_stops) > 1:
        for i in range(len(segment_stops) - 1):
            lat1 = float(segment_stops[i].get('y', segment_stops[i].get('stationY', 0)))
            lon1 = float(segment_stops[i].get('x', segment_stops[i].get('stationX', 0)))
            lat2 = float(segment_stops[i+1].get('y', segment_stops[i+1].get('stationY', 0)))
            lon2 = float(segment_stops[i+1].get('x', segment_stops[i+1].get('stationX', 0)))
            
            # Haversine 거리 * 도로 보정 계수(1.3)
            dist = haversine(lat1, lon1, lat2, lon2) * 1.3
            total_dist += dist
            
    # 3. 거쳐야 할 정류소 개수
    est_stops = len(segment_stops) - 1
    if est_stops < 1: est_stops = 1
    
    # 4. 이동 시간 및 정차 시간 계산
    travel_sec = total_dist / (avg_speed_kmh / 3.6)
    dwell_total_sec = est_stops * dwell_sec
    total_min = (travel_sec + dwell_total_sec) / 60
    
    # 5. 지도에 그릴 실제 이동 경로 좌표 추출
    segment_coords = [(float(s.get('y', s.get('stationY', 0))), float(s.get('x', s.get('stationX', 0)))) for s in segment_stops]
    
    return max(0.5, round(total_min, 1)), round(total_dist), est_stops, segment_coords

# ========================================
# 🔍 스마트 정류소 검색
# ========================================
def smart_search_stops(query):
    query_clean = query.strip()
    df, db_status = load_molit_csv()
    results = []
    
    if df is not None and not df.empty:
        if query_clean.isdigit():
            mask = (df['ars'] == query_clean) | (df['stationId'] == query_clean)
        else:
            mask = df['name'].str.contains(query_clean, na=False)
            
        matched = df[mask]
        for _, row in matched.iterrows():
            results.append({
                'id': str(row['stationId']), 
                'name': str(row['name']),
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'ars': str(row['ars'])
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
                                'id': str(item.get('stationId', '')),
                                'name': item.get('stationName', ''),
                                'lat': float(item.get('y', 0)),
                                'lon': float(item.get('x', 0)),
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
            
    unique_results = []
    seen = set()
    for r in results:
        key = (round(r['lat'], 5), round(r['lon'], 5))
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
            
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

# ===== 메인 화면 =====
st.title("🚌 경기버스 실시간 도착 정보")

df_check, db_status = load_molit_csv()
st.caption(f"📊 **DB 상태:** {db_status}")

with st.form(key='search_form'):
    col_s1, col_s2 = st.columns([4, 1])
    with col_s1:
        place = st.text_input("", key="search_input", placeholder="정류장명 또는 5자리 번호")
    with col_s2:
        submit_button = st.form_submit_button("🔍 검색")
    
    if submit_button:
        place_val = st.session_state.search_input
        if place_val:
            with st.spinner("데이터베이스 및 API 검색 중..."):
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

col_g1, col_g2 = st.columns([4, 1])
with col_g2:
    if st.button("📍 내 위치", key="btn_gps"):
        with st.spinner("위치 검색 중..."):
            loc = get_geolocation()
            if loc and 'coords' in loc:
                run_search_around(loc['coords']['latitude'], loc['coords']['longitude'], "gps", "내 위치")
            else:
                st.error("위치 권한을 허용해주세요.")

st.markdown("---")

# ========================================
# 뷰 모드: 검색 결과 여러 개
# ========================================
if st.session_state.view_mode == 'matches' and st.session_state.search_matches:
    st.subheader("🔍 검색 결과가 여러 개입니다.")
    cols = st.columns(min(len(st.session_state.search_matches), 2))
    for i, s in enumerate(st.session_state.search_matches):
        with cols[i % 2]:
            ars_str = f" ({s['ars']})" if s['ars'] and s['ars'] != '0' else ""
            label = f"🚏 {s['name']}{ars_str}\n(ID: {s['id']})"
            if st.button(label, key=f"match_btn_{i}"):
                if s.get('is_addr'):
                    run_search_around(s['lat'], s['lon'], "place", s['name'])
                else:
                    st.session_state.selected_stop = {"id": s['id'], "name": s['name'], "lat": s['lat'], "lon": s['lon']}
                    st.session_state.map_center = [s['lat'], s['lon']]
                    st.session_state.view_mode = 'detail'
                st.rerun()

elif st.session_state.view_mode == 'no_matches':
    st.error("😭 검색 결과가 없습니다.")

# ========================================
# 뷰 모드 1: 내 위치 주변 정류소 목록
# ========================================
elif st.session_state.view_mode == 'search':
    if st.session_state.favorites:
        st.subheader("⭐ 자주 찾는 정류소")
        cols = st.columns(min(len(st.session_state.favorites), 3))
        for i, fav in enumerate(st.session_state.favorites):
            with cols[i % 3]:
                if st.button(f"📍 {fav['name']}", key=f"fav_btn_{i}"):
                    st.session_state.selected_stop = fav
                    st.session_state.view_mode = 'detail'
                    st.rerun()
        st.markdown("---")

    st.subheader("🚏 주변 정류소 목록")
    if not st.session_state.stops:
        st.info("검색하거나 내 위치를 클릭하여 정류소를 찾아보세요.")
    else:
        sorted_stops = sorted(st.session_state.stops, key=lambda x: float(x.get('distance', 9999)) if st.session_state.search_mode == "gps" else x.get('stationName', ''))
        cols = st.columns(3)
        for i, s in enumerate(sorted_stops):
            with cols[i % 3]:
                name = s.get('stationName', '이름없음')
                sid = str(s.get('stationId', ''))
                dist = s.get('distance', '')
                mobile = s.get('mobileNo', '')
                mobile_str = f" ({mobile})" if mobile and mobile != '0' else ""
                label = f"🚏 {name}{mobile_str}\n({int(dist)}m)"
                
                if st.button(label, key=f"btn_stop_{sid}_{i}"):
                    st.session_state.selected_stop = {"id": sid, "name": name, "lat": float(s.get('y', 0)), "lon": float(s.get('x', 0))}
                    st.session_state.map_center = [float(s.get('y', 0)), float(s.get('x', 0))]
                    st.session_state.view_mode = 'detail'
                    st.rerun()

# ========================================
# 뷰 모드 2: 정류소 상세
# ========================================
elif st.session_state.view_mode == 'detail' and st.session_state.selected_stop:
    sel = st.session_state.selected_stop
    
    current_time = time.time()
    if current_time - st.session_state.last_update > 60:
        st.session_state.last_update = current_time
        st.rerun()

    if st.button("⬅️ 뒤로가기 (목록으로)", key="btn_back"):
        st.session_state.view_mode = 'search'
        st.session_state.selected_bus_id = None
        st.rerun()
    
    st.subheader(f"📍 {sel['name']}")
    st.caption(f"📌 정류소 ID: {sel['id']} | 🔄 업데이트: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update))}")
    
    is_fav = any(f['id'] == sel['id'] for f in st.session_state.favorites)
    col_fav1, col_fav2 = st.columns([4, 1])
    with col_fav2:
        if is_fav:
            if st.button("⭐ 해제", key="btn_unfav"):
                st.session_state.favorites = [f for f in st.session_state.favorites if f['id'] != sel['id']]
                st.rerun()
        else:
            if st.button("⭐ 저장", key="btn_fav"):
                st.session_state.favorites.append(sel)
                st.rerun()

    st.markdown("---")
    st.subheader("🚌 운행 노선 목록")
    
    with st.spinner("노선 정보 로딩 중..."):
        arrivals = fetch_bus_arrival(sel['id'])
        
        if not arrivals:
            st.info("현재 운행 중인 버스 정보가 없습니다.")
        else:
            cols = st.columns(3)
            for i, bus in enumerate(arrivals):
                with cols[i % 3]:
                    route_name = bus.get('routeName', '미상')
                    route_id = bus.get('routeId', '')
                    time1 = bus.get('predictTime1')
                    time2 = bus.get('predictTime2')
                    
                    t1_str = f"{time1}분" if time1 else "정보없음"
                    t2_str = f"{time2}분" if time2 else "정보없음"

                    btn_label = f"🚌 {route_name}번\n(첫째: {t1_str} / 둘째: {t2_str})"
                    
                    if st.button(btn_label, key=f"btn_bus_{route_id}_{i}", use_container_width=True):
                        st.session_state.selected_bus_id = route_id

    # ========================================
    # 🗺️ 버스 상세 시뮬레이션 (노선 기반 실제 경로)
    # ========================================
    if st.session_state.selected_bus_id:
        selected_bus_info = next((b for b in arrivals if b.get('routeId') == st.session_state.selected_bus_id), None)
        if selected_bus_info:
            route_name = selected_bus_info.get('routeName', '미상')
            route_id = selected_bus_info.get('routeId', '')
            
            st.markdown("---")
            st.subheader(f"🚌 {route_name}번 실제 이동 경로 및 예측")
            
            with st.spinner("노선 경로 분석 및 시뮬레이션 중..."):
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
                        
                        best_bus = None
                        min_diff = 9999
                        best_bus_lat = 0
                        best_bus_lon = 0
                        best_bus_seq = 0
                        
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
                            # 🟢 노선 기반 시뮬레이션 실행 (회차지/우회 반영)
                            sim_min, road_dist_m, est_stops, segment_coords = simulate_eta_route_based(route_stops_list, best_bus_seq, target_seq)
                            
                            if road_dist_m > 150000 or est_stops > 50 or sim_min > 120:
                                st.info("🚌 먼 거리 운행 중이거나 위치 정보가 불안정합니다.")
                            else:
                                # 전체 노선 좌표 (배경용)
                                route_coords = [(float(s.get('y', s.get('stationY', 0))), float(s.get('x', s.get('stationX', 0)))) for s in route_stops_list]
                                center_lat = (best_bus_lat + target_lat) / 2
                                center_lon = (best_bus_lon + target_lon) / 2
                                
                                m_detail = folium.Map(location=[center_lat, center_lon], zoom_start=15)
                                
                                # 1. 전체 노선 (옅은 회색 점선)
                                folium.PolyLine(route_coords, color='gray', weight=3, opacity=0.4, dash_array='5, 5').add_to(m_detail)
                                
                                # 2. 🟢 실제 버스가 이동할 경로 (진한 파란색 실선 - 회차지 포함!)
                                if segment_coords:
                                    folium.PolyLine(segment_coords, color='#0D47A1', weight=6, opacity=0.9).add_to(m_detail)
                                
                                # 3. 마커 표시
                                folium.Marker([best_bus_lat, best_bus_lon], popup=f"현재 {route_name}번 위치 ({best_bus_seq}번)", icon=folium.Icon(color='red', icon='bus', prefix='fa')).add_to(m_detail)
                                folium.Marker([target_lat, target_lon], popup=f"도착 예정: {sel['name']} ({target_seq}번)", icon=folium.Icon(color='green', icon='star', prefix='fa')).add_to(m_detail)
                                
                                st_folium(m_detail, width=None, height=450)
                                
                                st.markdown("---")
                                c1, c2, c3 = st.columns(3)
                                with c1: st.metric("🚌 노선", f"{route_name}번")
                                with c2: st.metric("🚏 거쳐야 할 정류소", f"{est_stops}개")
                                with c3: st.metric("⏱️ 노선 기반 예상 도착", f"{sim_min}분 후")
                                
                                st.info(f"📊 **분석:** 버스는 현재 {road_dist_m:,}m 떨어져 있으며, 노선을 따라 {est_stops}개의 정류소를 거쳐 도착합니다. (회차지 및 우회 구간이 포함된 실제 이동 경로입니다)")
                        else:
                            st.info("🚌 해당 노선의 버스가 목표 정류소 반대 방향에 있거나 운행 중이 아닙니다.")

# ===== 하단 안내 =====
st.markdown("---")
st.caption("경기버스 실시간 도착 정보 | Made 이봉수 ❤️ for 대중교통 이용자들")
