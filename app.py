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

st.set_page_config(page_title="경기버스", page_icon="🚌", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');

/* ── 기본 리셋 ── */
html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.main { background: #0A0F1E !important; }
.block-container { padding: 1.5rem 2rem 4rem !important; max-width: 1100px !important; }

/* ── 헤더 ── */
.app-header {
    background: linear-gradient(135deg, #0D47A1 0%, #1565C0 50%, #0288D1 100%);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 8px 32px rgba(13,71,161,0.4);
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.app-header::after {
    content: '';
    position: absolute;
    bottom: -60px; right: 60px;
    width: 150px; height: 150px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.app-title {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #FFFFFF !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
}
.app-subtitle {
    font-size: 0.85rem !important;
    color: rgba(255,255,255,0.7) !important;
    margin: 4px 0 0 !important;
}

/* ── 검색 박스 ── */
.search-wrap {
    background: #111827;
    border: 1.5px solid #1E3A5F;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
div[data-testid="stTextInput"] input {
    background: #0A0F1E !important;
    color: #E8F4FD !important;
    border: 2px solid #1E3A5F !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-family: 'Pretendard', sans-serif !important;
    font-weight: 500 !important;
    padding: 14px 18px !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #2196F3 !important;
    box-shadow: 0 0 0 3px rgba(33,150,243,0.15) !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #4A6080 !important;
}

/* ── 기본 버튼 ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1565C0, #0288D1) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Pretendard', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 12px 20px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(21,101,192,0.3) !important;
    letter-spacing: 0.2px !important;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #1976D2, #039BE5) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(21,101,192,0.4) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0) !important;
}

/* ── 폼 제출 버튼 ── */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #1565C0, #0288D1) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Pretendard', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 14px 28px !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(21,101,192,0.3) !important;
    transition: all 0.2s !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(21,101,192,0.45) !important;
}

/* ── 섹션 제목 ── */
.section-title {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #90CAF9 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin: 24px 0 12px !important;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1E3A5F;
    margin-left: 8px;
}

/* ── 정류소 카드 버튼 ── */
.stop-card {
    background: #111827;
    border: 1.5px solid #1E3A5F;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #E8F4FD !important;
}
.stop-card:hover {
    border-color: #2196F3;
    background: #151F30;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(33,150,243,0.15);
}
.stop-name { font-size: 1rem; font-weight: 700; color: #E8F4FD; }
.stop-meta { font-size: 0.8rem; color: #607D8B; font-family: 'IBM Plex Mono', monospace; }
.stop-dist {
    background: rgba(33,150,243,0.15);
    color: #64B5F6;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── 버스 도착 카드 ── */
.bus-card {
    background: #111827;
    border: 1.5px solid #1E3A5F;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 10px;
    transition: all 0.2s;
}
.bus-route-name {
    font-size: 1.3rem;
    font-weight: 800;
    color: #FFFFFF;
    font-family: 'IBM Plex Mono', monospace;
}
.bus-arrival-soon { color: #4CAF50; font-weight: 700; font-size: 0.95rem; }
.bus-arrival-mid  { color: #FF9800; font-weight: 700; font-size: 0.95rem; }
.bus-arrival-far  { color: #607D8B; font-weight: 700; font-size: 0.95rem; }

/* ── 즐겨찾기 뱃지 ── */
.fav-badge {
    background: rgba(255,193,7,0.15);
    border: 1.5px solid rgba(255,193,7,0.3);
    color: #FFD54F;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.85rem;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 8px;
}

/* ── 메트릭 ── */
div[data-testid="stMetric"] {
    background: #111827 !important;
    border: 1.5px solid #1E3A5F !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
}
div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.6rem !important;
    color: #64B5F6 !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] {
    color: #607D8B !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
}

/* ── 알림/정보 박스 ── */
div[data-testid="stAlert"] {
    background: #111827 !important;
    border: 1.5px solid #1E3A5F !important;
    border-radius: 12px !important;
    color: #B0BEC5 !important;
}

/* ── 구분선 ── */
hr { border-color: #1E3A5F !important; margin: 20px 0 !important; }

/* ── 캡션 / 상태 ── */
div[data-testid="stCaptionContainer"] p {
    color: #4A6080 !important;
    font-size: 0.78rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── 스피너 ── */
div[data-testid="stSpinner"] { color: #64B5F6 !important; }

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0A0F1E; }
::-webkit-scrollbar-thumb { background: #1E3A5F; border-radius: 3px; }

/* 모바일 반응형 */
@media (max-width: 768px) {
    .block-container { padding: 1rem 1rem 3rem !important; }
    .app-title { font-size: 1.4rem !important; }
}
</style>
""", unsafe_allow_html=True)

api_key = "a632cce2ef4ce525623e1348ef4502304284bf10dc238e36efe7925a3c59323b"

defaults = {
    'stops': [], 'map_center': None, 'search_mode': None,
    'selected_stop': None, 'selected_bus_id': None,
    'favorites': [], 'last_place_name': "", 'view_mode': 'search',
    'search_matches': None, 'last_update': time.time()
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

@st.cache_data
def load_molit_csv():
    search_paths = ['gyeonggi_stops.csv', 'data/gyeonggi_stops.csv']
    search_paths += glob.glob('*.csv') + glob.glob('**/*.csv', recursive=True)
    csv_file = next((p for p in search_paths if os.path.exists(p)), None)
    if not csv_file:
        return None, "❌ CSV 파일 없음"
    try:
        for enc in ['utf-8', 'cp949', 'euc-kr']:
            try:
                df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', encoding=enc)
                break
            except (UnicodeDecodeError, Exception):
                continue
        else:
            return None, "❌ 인코딩 오류"
        df = df[df.apply(lambda x: 8 <= len(x) <= 10, axis=1)].copy()
        df = df[~df[0].str.contains('정류장번호', na=False)]
        if df.empty: return None, "❌ 데이터 없음"
        df = df.iloc[:, :9]
        df.columns = ['raw_id','name','lat','lon','date','ars','city_code','city','admin']
        df['stationId'] = df['raw_id'].astype(str).str.replace(r'\D','',regex=True)
        df['name'] = df['name'].fillna('').astype(str).str.strip()
        df['ars']  = df['ars'].fillna('').astype(str).str.strip()
        df['lat']  = pd.to_numeric(df['lat'], errors='coerce')
        df['lon']  = pd.to_numeric(df['lon'], errors='coerce')
        df = df[(df['lat']!=0)&(df['lon']!=0)&df['lat'].notna()&df['lon'].notna()]
        return df, f"DB {len(df):,}건 로딩됨"
    except Exception as e:
        return None, f"❌ {str(e)}"

def fetch_bus_stops_around(lat, lon, radius=500):
    url = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationAroundListv2"
    params = {"serviceKey": urllib.parse.unquote(api_key), "pageNo":1,"numOfRows":50,"x":lon,"y":lat,"radius":radius,"_type":"json"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code!=200: return []
        d = r.json()
        if str(d.get('response',{}).get('msgHeader',{}).get('resultCode',99))!='0': return []
        items = d.get('response',{}).get('msgBody',{}).get('busStationAroundList',[])
        return (items if isinstance(items,list) else [items]) if items else []
    except: return []

def fetch_bus_arrival(station_id):
    url = "https://apis.data.go.kr/6410000/busarrivalservice/v2/getBusArrivalListv2"
    params = {"serviceKey": urllib.parse.unquote(api_key), "stationId":str(station_id),"_type":"json"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code!=200: return []
        d = r.json()
        if str(d.get('response',{}).get('msgHeader',{}).get('resultCode',99))!='0': return []
        arr = d.get('response',{}).get('msgBody',{}).get('busArrivalList',[])
        return (arr if isinstance(arr,list) else [arr]) if arr else []
    except: return []

def fetch_bus_locations(route_id):
    url = "https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2"
    params = {"serviceKey": urllib.parse.unquote(api_key), "routeId":str(route_id),"pageNo":1,"numOfRows":50,"_type":"json"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code!=200: return []
        d = r.json()
        if str(d.get('response',{}).get('msgHeader',{}).get('resultCode',99))!='0': return []
        buses = d.get('response',{}).get('msgBody',{}).get('busLocationList',[])
        return (buses if isinstance(buses,list) else [buses]) if buses else []
    except: return []

def fetch_route_stops(route_id):
    url = "https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2"
    params = {"serviceKey": urllib.parse.unquote(api_key), "routeId":str(route_id),"pageNo":1,"numOfRows":200,"_type":"json"}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code!=200: return []
        d = r.json()
        if str(d.get('response',{}).get('msgHeader',{}).get('resultCode',99))!='0': return []
        body = d.get('response',{}).get('msgBody',{})
        stops = body.get('busRouteStationList', body.get('items',[]))
        return (stops if isinstance(stops,list) else [stops]) if stops else []
    except: return []

def haversine(lat1,lon1,lat2,lon2):
    R=6371000
    p1,p2=math.radians(lat1),math.radians(lat2)
    a=math.sin(math.radians(lat2-lat1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def simulate_eta_route_based(route_stops_list, bus_seq, target_seq, avg_speed_kmh=20, dwell_sec=20):
    seg=[s for s in route_stops_list if bus_seq<=int(s.get('stationSeq',0))<=target_seq]
    seg.sort(key=lambda x:int(x.get('stationSeq',0)))
    dist=sum(haversine(float(seg[i].get('y',seg[i].get('stationY',0))),float(seg[i].get('x',seg[i].get('stationX',0))),
                       float(seg[i+1].get('y',seg[i+1].get('stationY',0))),float(seg[i+1].get('x',seg[i+1].get('stationX',0))))*1.3
             for i in range(len(seg)-1)) if len(seg)>1 else 0
    est=max(1,len(seg)-1)
    total_min=(dist/(avg_speed_kmh/3.6)+est*dwell_sec)/60
    coords=[(float(s.get('y',s.get('stationY',0))),float(s.get('x',s.get('stationX',0)))) for s in seg]
    return max(0.5,round(total_min,1)),round(dist),est,coords

def smart_search_stops(query):
    q=query.strip()
    df,status=load_molit_csv()
    results=[]
    if df is not None and not df.empty:
        mask=(df['ars']==q)|(df['stationId']==q) if q.isdigit() else df['name'].str.contains(q,na=False)
        for _,row in df[mask].iterrows():
            results.append({'id':str(row['stationId']),'name':str(row['name']),'lat':float(row['lat']),'lon':float(row['lon']),'ars':str(row['ars'])})
    if not results:
        try:
            r=requests.get("https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2",
                           params={"serviceKey":urllib.parse.unquote(api_key),"stationName":q,"pageNo":1,"numOfRows":50,"_type":"json"},timeout=5)
            if r.status_code==200:
                d=r.json()
                if str(d.get('response',{}).get('msgHeader',{}).get('resultCode',99))=='0':
                    items=d.get('response',{}).get('msgBody',{}).get('busStationList',[])
                    for item in (items if isinstance(items,list) else [items]):
                        results.append({'id':str(item.get('stationId','')),'name':item.get('stationName',''),
                                        'lat':float(item.get('y',0)),'lon':float(item.get('x',0)),'ars':str(item.get('mobileNo',''))})
        except: pass
    if not results and not q.isdigit():
        geo=Nominatim(user_agent="bus_app",timeout=10)
        for gq in [f"{q} 파주시 경기도",f"{q} 경기도",q]:
            try:
                loc=geo.geocode(gq,language='ko')
                if loc: return [{'id':'ADDR','name':gq,'lat':loc.latitude,'lon':loc.longitude,'ars':'','is_addr':True}],status
            except: pass
    seen=set(); unique=[]
    for r in results:
        k=(round(r['lat'],5),round(r['lon'],5))
        if k not in seen: seen.add(k); unique.append(r)
    return unique,status

def arrival_class(minutes):
    if minutes is None: return "bus-arrival-far", "정보없음"
    m=int(minutes)
    if m<=5: return "bus-arrival-soon", f"{m}분 후 🟢"
    elif m<=15: return "bus-arrival-mid", f"{m}분 후 🟡"
    else: return "bus-arrival-far", f"{m}분 후"

def run_search_around(lat,lon,mode,place_name=""):
    st.session_state.map_center=[lat,lon]; st.session_state.search_mode=mode
    st.session_state.last_place_name=place_name; st.session_state.view_mode='search'
    st.session_state.selected_stop=None; st.session_state.selected_bus_id=None
    st.session_state.search_matches=None
    with st.spinner("주변 정류소 검색 중..."): st.session_state.stops=fetch_bus_stops_around(lat,lon)

# ══════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div style="font-size:2.8rem; z-index:1;">🚌</div>
  <div style="z-index:1;">
    <div class="app-title">경기버스 실시간</div>
    <div class="app-subtitle">Gyeonggi-do Bus Arrival Information</div>
  </div>
</div>
""", unsafe_allow_html=True)

df_check, db_status = load_molit_csv()
st.caption(f"🗄️ {db_status}")

# ══════════════════════════════════════════
# 검색 폼
# ══════════════════════════════════════════
with st.form(key='search_form'):
    col_s1, col_s2, col_s3 = st.columns([5, 1, 1])
    with col_s1:
        place = st.text_input("", key="search_input", placeholder="🔍  정류장명 또는 5자리 번호 입력")
    with col_s2:
        submit_button = st.form_submit_button("검색")
    with col_s3:
        pass

if st.button("📍 내 위치로 검색", key="btn_gps"):
    with st.spinner("위치 확인 중..."):
        loc = get_geolocation()
        if loc and 'coords' in loc:
            run_search_around(loc['coords']['latitude'], loc['coords']['longitude'], "gps", "내 위치")
        else:
            st.error("위치 권한을 허용해주세요.")

if submit_button and st.session_state.get('search_input'):
    with st.spinner("검색 중..."):
        matches, status = smart_search_stops(st.session_state.search_input)
        if matches:
            if len(matches)==1 and not matches[0].get('is_addr'):
                s=matches[0]
                st.session_state.selected_stop={"id":s['id'],"name":s['name'],"lat":s['lat'],"lon":s['lon']}
                st.session_state.map_center=[s['lat'],s['lon']]
                st.session_state.view_mode='detail'
            elif len(matches)==1 and matches[0].get('is_addr'):
                run_search_around(matches[0]['lat'],matches[0]['lon'],"place",matches[0]['name'])
            else:
                st.session_state.search_matches=matches
                st.session_state.view_mode='matches'
        else:
            st.session_state.view_mode='no_matches'

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# 뷰: 복수 검색 결과
# ══════════════════════════════════════════
if st.session_state.view_mode=='matches' and st.session_state.search_matches:
    st.markdown('<div class="section-title">🔍 검색 결과</div>', unsafe_allow_html=True)
    cols=st.columns(2)
    for i,s in enumerate(st.session_state.search_matches):
        with cols[i%2]:
            ars_str=f" · {s['ars']}" if s['ars'] and s['ars']!='0' else ""
            if st.button(f"🚏 {s['name']}{ars_str}", key=f"match_btn_{i}", use_container_width=True):
                if s.get('is_addr'):
                    run_search_around(s['lat'],s['lon'],"place",s['name'])
                else:
                    st.session_state.selected_stop={"id":s['id'],"name":s['name'],"lat":s['lat'],"lon":s['lon']}
                    st.session_state.map_center=[s['lat'],s['lon']]
                    st.session_state.view_mode='detail'
                st.rerun()

elif st.session_state.view_mode=='no_matches':
    st.markdown("""
    <div style="text-align:center; padding:48px 0; color:#4A6080;">
      <div style="font-size:3rem;">😕</div>
      <div style="font-size:1.1rem; font-weight:600; margin-top:12px;">검색 결과가 없습니다</div>
      <div style="font-size:0.85rem; margin-top:6px;">정류장명 또는 5자리 단축번호로 검색해보세요</div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# 뷰: 주변 정류소 목록
# ══════════════════════════════════════════
elif st.session_state.view_mode=='search':
    if st.session_state.favorites:
        st.markdown('<div class="section-title">⭐ 즐겨찾기</div>', unsafe_allow_html=True)
        cols=st.columns(min(len(st.session_state.favorites),3))
        for i,fav in enumerate(st.session_state.favorites):
            with cols[i%3]:
                if st.button(f"⭐ {fav['name']}", key=f"fav_{i}", use_container_width=True):
                    st.session_state.selected_stop=fav
                    st.session_state.view_mode='detail'
                    st.rerun()

    if st.session_state.stops:
        st.markdown('<div class="section-title">🚏 주변 정류소</div>', unsafe_allow_html=True)
        sorted_stops=sorted(st.session_state.stops,
            key=lambda x: float(x.get('distance',9999)) if st.session_state.search_mode=="gps" else x.get('stationName',''))
        cols=st.columns(2)
        for i,s in enumerate(sorted_stops):
            with cols[i%2]:
                name=s.get('stationName','이름없음')
                sid=str(s.get('stationId',''))
                dist=s.get('distance','')
                mobile=s.get('mobileNo','')
                mobile_str=f"  ·  {mobile}" if mobile and mobile!='0' else ""
                dist_str=f"{int(float(dist))}m" if dist else ""
                label=f"🚏 {name}{mobile_str}"
                if dist_str: label+=f"  ({dist_str})"
                if st.button(label, key=f"stop_{sid}_{i}", use_container_width=True):
                    st.session_state.selected_stop={"id":sid,"name":name,"lat":float(s.get('y',0)),"lon":float(s.get('x',0))}
                    st.session_state.map_center=[float(s.get('y',0)),float(s.get('x',0))]
                    st.session_state.view_mode='detail'
                    st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center; padding:64px 0; color:#4A6080;">
          <div style="font-size:3.5rem;">🗺️</div>
          <div style="font-size:1.15rem; font-weight:700; margin-top:16px; color:#607D8B;">정류소를 검색하거나</div>
          <div style="font-size:1rem; margin-top:6px;">📍 내 위치 버튼으로 주변 정류소를 찾아보세요</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# 뷰: 정류소 상세 / 버스 도착 정보
# ══════════════════════════════════════════
elif st.session_state.view_mode=='detail' and st.session_state.selected_stop:
    sel=st.session_state.selected_stop
    current_time=time.time()
    if current_time-st.session_state.last_update>60:
        st.session_state.last_update=current_time
        st.rerun()

    col_back, col_fav = st.columns([3,1])
    with col_back:
        if st.button("← 목록으로", key="btn_back"):
            st.session_state.view_mode='search'
            st.session_state.selected_bus_id=None
            st.rerun()
    with col_fav:
        is_fav=any(f['id']==sel['id'] for f in st.session_state.favorites)
        if is_fav:
            if st.button("⭐ 즐겨찾기 해제", key="btn_unfav"):
                st.session_state.favorites=[f for f in st.session_state.favorites if f['id']!=sel['id']]
                st.rerun()
        else:
            if st.button("☆ 즐겨찾기 추가", key="btn_fav"):
                st.session_state.favorites.append(sel)
                st.rerun()

    # 정류소 정보 헤더
    st.markdown(f"""
    <div style="background:#111827; border:1.5px solid #1E3A5F; border-radius:16px; padding:20px 24px; margin:16px 0;">
      <div style="font-size:1.4rem; font-weight:800; color:#E8F4FD;">📍 {sel['name']}</div>
      <div style="font-size:0.8rem; color:#4A6080; margin-top:6px; font-family:'IBM Plex Mono',monospace;">
        ID: {sel['id']} &nbsp;·&nbsp; 🔄 {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update))} 기준
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🚌 도착 예정 버스</div>', unsafe_allow_html=True)

    with st.spinner("도착 정보 불러오는 중..."):
        arrivals=fetch_bus_arrival(sel['id'])

    if not arrivals:
        st.markdown("""
        <div style="text-align:center;padding:32px;color:#4A6080;background:#111827;border-radius:14px;border:1.5px solid #1E3A5F;">
          <div style="font-size:2rem;">🚫</div>
          <div style="margin-top:8px;font-weight:600;">현재 운행 중인 버스가 없습니다</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        cols=st.columns(3)
        for i,bus in enumerate(arrivals):
            with cols[i%3]:
                route_name=bus.get('routeName','?')
                route_id=bus.get('routeId','')
                t1=bus.get('predictTime1'); t2=bus.get('predictTime2')
                cls1,str1=arrival_class(t1); cls2,str2=arrival_class(t2)
                btn_label=f"🚌 {route_name}번\n{str1} / {str2}"
                if st.button(btn_label, key=f"bus_{route_id}_{i}", use_container_width=True):
                    st.session_state.selected_bus_id=route_id

    # ── 버스 경로 지도 ──
    if st.session_state.selected_bus_id:
        bus_info=next((b for b in arrivals if b.get('routeId')==st.session_state.selected_bus_id),None)
        if bus_info:
            route_name=bus_info.get('routeName','?')
            route_id=bus_info.get('routeId','')
            st.markdown(f'<div class="section-title">🗺️ {route_name}번 실시간 경로</div>', unsafe_allow_html=True)
            with st.spinner("경로 분석 중..."):
                buses=fetch_bus_locations(route_id)
                route_stops_list=fetch_route_stops(route_id)
            if not buses or not route_stops_list:
                st.warning("실시간 위치 정보를 불러올 수 없습니다.")
            else:
                target_stop=next((s for s in route_stops_list if str(s.get('stationId'))==str(sel['id'])),None)
                if not target_stop:
                    st.error("목표 정류소를 찾을 수 없습니다.")
                else:
                    tseq=int(target_stop.get('stationSeq',0))
                    tlat=float(target_stop.get('stationY',target_stop.get('y',0)))
                    tlon=float(target_stop.get('stationX',target_stop.get('x',0)))
                    best_bus=None; min_diff=9999; blat=0; blon=0; bseq=0
                    for bus in buses:
                        bsd=next((s for s in route_stops_list if str(s.get('stationId'))==str(bus.get('stationId'))),None)
                        if bsd:
                            bs=int(bsd.get('stationSeq',0)); diff=tseq-bs
                            if 0<diff<min_diff:
                                min_diff=diff; best_bus=bus; bseq=bs
                                blat=float(bsd.get('stationY',bsd.get('y',0))); blon=float(bsd.get('stationX',bsd.get('x',0)))
                    if best_bus:
                        sim_min,road_dist,est_stops,seg_coords=simulate_eta_route_based(route_stops_list,bseq,tseq)
                        if road_dist>150000 or est_stops>50 or sim_min>120:
                            st.info("🚌 먼 거리 운행 중이거나 위치 정보가 불안정합니다.")
                        else:
                            route_coords=[(float(s.get('y',s.get('stationY',0))),float(s.get('x',s.get('stationX',0)))) for s in route_stops_list]
                            m=folium.Map(location=[(blat+tlat)/2,(blon+tlon)/2],zoom_start=14,
                                        tiles="CartoDB dark_matter")
                            folium.PolyLine(route_coords,color='#37474F',weight=3,opacity=0.5,dash_array='6,6').add_to(m)
                            if seg_coords:
                                folium.PolyLine(seg_coords,color='#2196F3',weight=5,opacity=0.9).add_to(m)
                            folium.Marker([blat,blon],popup=f"🚌 {route_name}번",
                                icon=folium.DivIcon(html=f'<div style="background:#F44336;color:white;padding:4px 8px;border-radius:8px;font-weight:700;font-size:12px;white-space:nowrap">🚌 {route_name}</div>')).add_to(m)
                            folium.Marker([tlat,tlon],popup=sel['name'],
                                icon=folium.DivIcon(html=f'<div style="background:#4CAF50;color:white;padding:4px 8px;border-radius:8px;font-weight:700;font-size:12px;white-space:nowrap">📍 {sel["name"][:6]}</div>')).add_to(m)
                            st_folium(m,width=None,height=420,returned_objects=[])
                            st.markdown("<br>", unsafe_allow_html=True)
                            c1,c2,c3=st.columns(3)
                            with c1: st.metric("🚌 노선",f"{route_name}번")
                            with c2: st.metric("🚏 남은 정류소",f"{est_stops}개")
                            with c3: st.metric("⏱️ 예상 도착",f"{sim_min}분")
                            st.info(f"버스가 현재 {road_dist:,}m 거리에서 {est_stops}개 정류소를 거쳐 도착합니다.")
                    else:
                        st.info("🚌 해당 노선 버스가 반대 방향에 있거나 운행 종료 상태입니다.")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#2A3A5A;font-size:0.8rem;">경기버스 실시간 도착 정보 · Made with ❤️ by 이봉수</p>', unsafe_allow_html=True)
