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
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif !important; }

/* ── 배경 그라디언트 ── */
.stApp {
    background: linear-gradient(135deg, #FDF2FF 0%, #F0E6FF 30%, #E8F0FF 60%, #EDF9FF 100%) !important;
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] > .main {
    background: transparent !important;
}
[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
[data-testid="collapsedControl"] { display: none; }
.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 860px !important;
}

/* ── 타이포그래피 ── */
h1,h2,h3,h4 { letter-spacing: -0.3px !important; }
[data-testid="stCaptionContainer"] p {
    font-size: 0.73rem !important;
    color: #A89BC2 !important;
    font-weight: 400 !important;
}
p { color: #3D2B6B !important; }

/* ── 검색창 ── */
[data-testid="stTextInput"] input {
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: #2D1B69 !important;
    background: rgba(255,255,255,0.85) !important;
    border: 1.5px solid rgba(167,139,250,0.3) !important;
    border-radius: 18px !important;
    padding: 15px 20px !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 4px 20px rgba(139,92,246,0.08) !important;
    transition: all 0.25s ease !important;
}
[data-testid="stTextInput"] input:focus {
    border: 1.5px solid #A78BFA !important;
    box-shadow: 0 0 0 4px rgba(167,139,250,0.15) !important;
    background: rgba(255,255,255,0.97) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #C4B3E8 !important; font-weight: 400 !important; }
[data-testid="stForm"] { background: transparent !important; border: none !important; padding: 0 !important; }

/* ── 기본 버튼 (정류소·버스 카드) ── */
.stButton > button {
    background: rgba(255,255,255,0.75) !important;
    color: #2D1B69 !important;
    border: 1.5px solid rgba(167,139,250,0.2) !important;
    border-radius: 18px !important;
    font-size: 0.87rem !important;
    font-weight: 600 !important;
    padding: 13px 16px !important;
    width: 100% !important;
    text-align: left !important;
    line-height: 1.55 !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 12px rgba(139,92,246,0.06) !important;
    transition: all 0.2s ease !important;
    white-space: pre-wrap !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.95) !important;
    border-color: #A78BFA !important;
    box-shadow: 0 6px 24px rgba(139,92,246,0.18) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── 검색 제출 버튼 & 내 위치 버튼 공통 ── */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #A78BFA, #EC4899) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 18px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    padding: 15px 12px !important;
    box-shadow: 0 6px 20px rgba(167,139,250,0.4) !important;
    letter-spacing: 0.2px !important;
    width: 100% !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 8px 28px rgba(167,139,250,0.55) !important;
    transform: translateY(-2px) !important;
}

/* ── 구분선 ── */
hr { border: none !important; border-top: 1px solid rgba(167,139,250,0.15) !important; margin: 20px 0 !important; }

/* ── Alert 박스 ── */
[data-testid="stAlert"] {
    border-radius: 16px !important;
    border: none !important;
    font-weight: 500 !important;
    backdrop-filter: blur(8px) !important;
}

/* ── Metric 카드 ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.7) !important;
    border-radius: 20px !important;
    padding: 18px 20px !important;
    border: 1.5px solid rgba(167,139,250,0.2) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 4px 16px rgba(139,92,246,0.08) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #7C3AED, #EC4899);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    color: #A89BC2 !important;
    font-weight: 500 !important;
}

/* ── spinner ── */
[data-testid="stSpinner"] p { color: #A78BFA !important; font-weight: 500 !important; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 ──
defaults = {
    'stops': [], 'map_center': None, 'search_mode': None,
    'selected_stop': None, 'selected_bus_id': None,
    'favorites': [], 'last_place_name': "", 'view_mode': 'search',
    'search_matches': None, 'last_update': time.time()
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

@st.cache_data
def load_gyeonggi_stops_csv():
    csv_files = glob.glob('*.csv') + glob.glob('**/*.csv', recursive=True)
    if not csv_files: return None, "❌ CSV 없음"
    csv_file = max(csv_files, key=lambda f: os.path.getsize(f))
    try:
        try:
            df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file, header=None, dtype=str, on_bad_lines='skip', encoding='cp949')
        df = df[df.apply(lambda x: len(x) == 9, axis=1)].copy()
        if df.empty: return None, "❌ 데이터 없음"
        df.columns = ['raw_id','name','lat','lon','date','ars','city_code','city','admin']
        df = df[df['city'].str.contains("경기도", na=False)].copy()
        df['stationId'] = df['raw_id'].astype(str).str.replace(r'\D','',regex=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df['ars'] = df['ars'].fillna('').astype(str).str.strip()
        df = df[(df['lat']!=0)&(df['lon']!=0)&df['lat'].notna()&df['lon'].notna()]
        return df, f"정류소 {len(df):,}개 로딩됨"
    except Exception as e:
        return None, f"❌ 오류: {e}"

def fetch_bus_stops_around(lat, lon, radius=500):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationAroundListv2"
    params = {"serviceKey":decoded_key,"pageNo":1,"numOfRows":50,"x":lon,"y":lat,"radius":radius,"_type":"json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return []
        data = res.json()
        if str(data.get('response',{}).get('msgHeader',{}).get('resultCode',99)) != '0': return []
        items = data.get('response',{}).get('msgBody',{}).get('busStationAroundList',[])
        return (items if isinstance(items,list) else [items]) if items else []
    except: return []

def fetch_bus_arrival(station_id):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/busarrivalservice/v2/getBusArrivalListv2"
    params = {"serviceKey":decoded_key,"stationId":str(station_id),"_type":"json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return []
        data = res.json()
        if str(data.get('response',{}).get('msgHeader',{}).get('resultCode',99)) != '0': return []
        arrivals = data.get('response',{}).get('msgBody',{}).get('busArrivalList',[])
        return (arrivals if isinstance(arrivals,list) else [arrivals]) if arrivals else []
    except: return []

def fetch_bus_locations(route_id):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2"
    params = {"serviceKey":decoded_key,"routeId":str(route_id),"pageNo":1,"numOfRows":50,"_type":"json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return []
        data = res.json()
        if str(data.get('response',{}).get('msgHeader',{}).get('resultCode',99)) != '0': return []
        buses = data.get('response',{}).get('msgBody',{}).get('busLocationList',[])
        return (buses if isinstance(buses,list) else [buses]) if buses else []
    except: return []

def fetch_route_stops(route_id):
    decoded_key = urllib.parse.unquote(api_key)
    url = "https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2"
    params = {"serviceKey":decoded_key,"routeId":str(route_id),"pageNo":1,"numOfRows":200,"_type":"json"}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code != 200: return []
        data = res.json()
        if str(data.get('response',{}).get('msgHeader',{}).get('resultCode',99)) != '0': return []
        body = data.get('response',{}).get('msgBody',{})
        stops = body.get('busRouteStationList', body.get('items',[]))
        return (stops if isinstance(stops,list) else [stops]) if stops else []
    except: return []

def haversine(la1,lo1,la2,lo2):
    R=6371000; p1,p2=math.radians(la1),math.radians(la2)
    dp,dl=math.radians(la2-la1),math.radians(lo2-lo1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def simulate_eta_route_based(route_stops_list, bus_seq, target_seq, avg_speed_kmh=20, dwell_sec=20):
    seg=[s for s in route_stops_list if bus_seq<=int(s.get('stationSeq',0))<=target_seq]
    seg.sort(key=lambda x:int(x.get('stationSeq',0)))
    dist=0
    if len(seg)>1:
        for i in range(len(seg)-1):
            la1=float(seg[i].get('y',seg[i].get('stationY',0))); lo1=float(seg[i].get('x',seg[i].get('stationX',0)))
            la2=float(seg[i+1].get('y',seg[i+1].get('stationY',0))); lo2=float(seg[i+1].get('x',seg[i+1].get('stationX',0)))
            dist+=haversine(la1,lo1,la2,lo2)*1.3
    n=max(1,len(seg)-1)
    mins=(dist/(avg_speed_kmh/3.6)+n*dwell_sec)/60
    coords=[(float(s.get('y',s.get('stationY',0))),float(s.get('x',s.get('stationX',0)))) for s in seg]
    return max(0.5,round(mins,1)),round(dist),n,coords

def arrival_badge(minutes):
    try: m=int(minutes)
    except: m=999
    if m==0:   return "도착!", "#DCFCE7","#15803D"
    elif m<=3: return f"{m}분", "#DCFCE7","#15803D"
    elif m<=10:return f"{m}분", "#FEF9C3","#A16207"
    elif m<=20:return f"{m}분", "#FFE4E6","#BE123C"
    else:      return f"{m}분", "#F3F4F6","#6B7280"

def smart_search_stops(query):
    q = query.strip()
    df, db_status = load_gyeonggi_stops_csv()
    results = []
    if df is not None and not df.empty:
        mask = (df['ars']==q)|(df['stationId']==q) if q.isdigit() else df['name'].str.contains(q,na=False)
        for _,row in df[mask].iterrows():
            results.append({'id':str(row['stationId']),'name':str(row['name']),'lat':float(row['lat']),'lon':float(row['lon']),'ars':str(row['ars'])})
    if not results:
        decoded_key = urllib.parse.unquote(api_key)
        try:
            res = requests.get("https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2",
                params={"serviceKey":decoded_key,"stationName":q,"pageNo":1,"numOfRows":50,"_type":"json"},timeout=5)
            if res.status_code==200:
                data=res.json()
                if str(data.get('response',{}).get('msgHeader',{}).get('resultCode',99))=='0':
                    items=data.get('response',{}).get('msgBody',{}).get('busStationList',[])
                    for item in (items if isinstance(items,list) else [items]):
                        results.append({'id':str(item.get('stationId','')),'name':item.get('stationName',''),
                                        'lat':float(item.get('y',0)),'lon':float(item.get('x',0)),'ars':str(item.get('mobileNo',''))})
        except: pass
    if not results and not q.isdigit():
        geo=Nominatim(user_agent="bus_app",timeout=10)
        for qq in [f"{q} 파주시 경기도",f"{q} 경기도",q]:
            try:
                loc=geo.geocode(qq,language='ko')
                if loc: return [{'id':'ADDR','name':qq,'lat':loc.latitude,'lon':loc.longitude,'ars':'','is_addr':True}],db_status
            except: pass
    seen, out = set(), []
    for r in results:
        k = (round(r['lat'],5), round(r['lon'],5))
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out, db_status

def run_search_around(lat, lon, mode, place_name=""):
    for k,v in [('map_center',[lat,lon]),('search_mode',mode),('last_place_name',place_name),
                ('view_mode','search'),('selected_stop',None),('selected_bus_id',None),('search_matches',None)]:
        st.session_state[k]=v
    with st.spinner("주변 정류소 검색 중..."):
        st.session_state.stops = fetch_bus_stops_around(lat, lon)

# ══════════════════════════════════════════
#  헤더
# ══════════════════════════════════════════
st.markdown("""
<div style="text-align:center; padding: 10px 0 24px;">
  <div style="font-size:3rem; margin-bottom:4px;">🚌</div>
  <div style="font-size:2rem; font-weight:800; letter-spacing:-1px;
              background:linear-gradient(135deg,#7C3AED,#EC4899,#3B82F6);
              -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
    경기버스 실시간
  </div>
  <div style="font-size:0.78rem; color:#B09FD8; margin-top:6px; font-weight:400;">
    경기도 버스 도착 정보 · 실시간 위치 조회
  </div>
</div>
""", unsafe_allow_html=True)

df_check, db_status = load_gyeonggi_stops_csv()
st.caption(f"🗄️ {db_status}")

# ══════════════════════════════════════════
#  검색 폼
# ══════════════════════════════════════════
with st.form(key='search_form'):
    c1, c2, c3 = st.columns([5, 1, 1])
    with c1:
        place = st.text_input("", key="search_input", placeholder="🔍  정류장명 또는 5자리 번호")
    with c2:
        submit = st.form_submit_button("검색")
    with c3:
        gps_click = st.form_submit_button("📍 내 위치")

    if submit and st.session_state.search_input:
        with st.spinner("🔍 검색 중..."):
            matches, _ = smart_search_stops(st.session_state.search_input)
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

    if gps_click:
        with st.spinner("📍 위치 확인 중..."):
            loc = get_geolocation()
        if loc and 'coords' in loc:
            run_search_around(loc['coords']['latitude'],loc['coords']['longitude'],"gps","내 위치")
        else:
            st.error("위치 권한을 허용해주세요.")

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════
#  검색 결과 목록
# ══════════════════════════════════════════
if st.session_state.view_mode=='matches' and st.session_state.search_matches:
    st.markdown(f"""
    <div style="font-size:0.95rem; font-weight:700; color:#5B21B6; margin-bottom:12px;">
      🔍 검색 결과 {len(st.session_state.search_matches)}개
    </div>""", unsafe_allow_html=True)
    cols = st.columns(min(len(st.session_state.search_matches),2))
    for i,s in enumerate(st.session_state.search_matches):
        with cols[i%2]:
            ars = f"  ·  {s['ars']}번" if s['ars'] and s['ars']!='0' else ""
            if st.button(f"🚏  {s['name']}{ars}", key=f"m{i}"):
                if s.get('is_addr'): run_search_around(s['lat'],s['lon'],"place",s['name'])
                else:
                    st.session_state.selected_stop={"id":s['id'],"name":s['name'],"lat":s['lat'],"lon":s['lon']}
                    st.session_state.map_center=[s['lat'],s['lon']]
                    st.session_state.view_mode='detail'
                st.rerun()

elif st.session_state.view_mode=='no_matches':
    st.markdown("""
    <div style="text-align:center; padding:40px 20px; background:rgba(255,255,255,0.5);
                border-radius:20px; border:1.5px solid rgba(236,72,153,0.15);">
      <div style="font-size:2.5rem;">😔</div>
      <div style="font-size:0.95rem; color:#9CA3AF; margin-top:8px;">검색 결과가 없습니다</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
#  주변 정류소 목록
# ══════════════════════════════════════════
elif st.session_state.view_mode=='search':
    if st.session_state.favorites:
        st.markdown("""<div style="font-size:0.88rem; font-weight:700; color:#7C3AED; margin-bottom:10px;">⭐ 즐겨찾기</div>""", unsafe_allow_html=True)
        cols = st.columns(min(len(st.session_state.favorites),3))
        for i,fav in enumerate(st.session_state.favorites):
            with cols[i%3]:
                if st.button(f"⭐  {fav['name']}", key=f"fav{i}"):
                    st.session_state.selected_stop=fav
                    st.session_state.view_mode='detail'
                    st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    if not st.session_state.stops:
        st.markdown("""
        <div style="text-align:center; padding:64px 20px;">
          <div style="font-size:4rem; margin-bottom:16px;">🚏</div>
          <div style="font-size:1.1rem; font-weight:700; color:#7C3AED; margin-bottom:6px;">정류장을 검색해보세요</div>
          <div style="font-size:0.85rem; color:#B09FD8;">정류장명, 번호 검색 또는 내 위치 버튼을 눌러주세요</div>
        </div>""", unsafe_allow_html=True)
    else:
        cnt = len(st.session_state.stops)
        st.markdown(f"""<div style="font-size:0.88rem; font-weight:700; color:#7C3AED; margin-bottom:12px;">
          🚏 주변 정류소 <span style="color:#C084FC;">{cnt}개</span></div>""", unsafe_allow_html=True)
        sorted_stops = sorted(st.session_state.stops,
            key=lambda x: float(x.get('distance',9999)) if st.session_state.search_mode=="gps" else x.get('stationName',''))
        cols = st.columns(3)
        for i,s in enumerate(sorted_stops):
            with cols[i%3]:
                name=s.get('stationName','이름없음')
                sid=str(s.get('stationId',''))
                dist=s.get('distance','')
                mobile=s.get('mobileNo','')
                m_str=f"\n📟 {mobile}번" if mobile and mobile!='0' else ""
                d_str=f"\n📏 {int(dist)}m" if dist else ""
                if st.button(f"🚏  {name}{m_str}{d_str}", key=f"s{sid}{i}"):
                    st.session_state.selected_stop={"id":sid,"name":name,"lat":float(s.get('y',0)),"lon":float(s.get('x',0))}
                    st.session_state.map_center=[float(s.get('y',0)),float(s.get('x',0))]
                    st.session_state.view_mode='detail'
                    st.rerun()

# ══════════════════════════════════════════
#  정류소 상세
# ══════════════════════════════════════════
elif st.session_state.view_mode=='detail' and st.session_state.selected_stop:
    sel = st.session_state.selected_stop
    if time.time()-st.session_state.last_update>60:
        st.session_state.last_update=time.time(); st.rerun()

    # 뒤로 / 즐겨찾기
    cb, cf = st.columns([4,1])
    with cb:
        if st.button("← 목록으로", key="back"):
            st.session_state.view_mode='search'
            st.session_state.selected_bus_id=None
            st.rerun()
    with cf:
        is_fav = any(f['id']==sel['id'] for f in st.session_state.favorites)
        lbl = "⭐ 해제" if is_fav else "☆ 저장"
        if st.button(lbl, key="fav_toggle"):
            if is_fav: st.session_state.favorites=[f for f in st.session_state.favorites if f['id']!=sel['id']]
            else: st.session_state.favorites.append(sel)
            st.rerun()

    # 정류소 카드
    upd = time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update))
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(167,139,250,0.15),rgba(236,72,153,0.08));
                border:1.5px solid rgba(167,139,250,0.3); border-radius:24px;
                padding:22px 26px; margin:12px 0 20px; backdrop-filter:blur(10px);">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:48px;height:48px;border-radius:50%;
                    background:linear-gradient(135deg,#A78BFA,#EC4899);
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.4rem; flex-shrink:0;">📍</div>
        <div>
          <div style="font-size:1.2rem;font-weight:800;color:#2D1B69;">{sel['name']}</div>
          <div style="font-size:0.73rem;color:#A89BC2;margin-top:3px;">ID: {sel['id']} &nbsp;·&nbsp; {upd} 업데이트</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 노선 목록
    st.markdown("""<div style="font-size:0.88rem;font-weight:700;color:#7C3AED;margin-bottom:12px;">🚌 운행 노선</div>""", unsafe_allow_html=True)
    with st.spinner("노선 정보 불러오는 중..."):
        arrivals = fetch_bus_arrival(sel['id'])

    if not arrivals:
        st.markdown("""
        <div style="text-align:center;padding:30px;background:rgba(255,255,255,0.5);
                    border-radius:18px;border:1.5px solid rgba(167,139,250,0.15);">
          <div style="font-size:1.8rem;">🚌</div>
          <div style="font-size:0.88rem;color:#B09FD8;margin-top:6px;">현재 운행 중인 버스가 없습니다</div>
        </div>""", unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i,bus in enumerate(arrivals):
            with cols[i%3]:
                route_name=bus.get('routeName','미상')
                route_id=bus.get('routeId','')
                t1,t2=bus.get('predictTime1'),bus.get('predictTime2')
                txt1,bg1,fg1=arrival_badge(t1)
                txt2,bg2,fg2=arrival_badge(t2)
                badge1=f'<span style="background:{bg1};color:{fg1};padding:2px 9px;border-radius:20px;font-size:0.78rem;font-weight:700;">{txt1}</span>'
                badge2=f'<span style="background:{bg2};color:{fg2};padding:2px 9px;border-radius:20px;font-size:0.78rem;font-weight:700;">{txt2}</span>'
                # 클릭용 버튼 (라벨 텍스트만)
                label=f"🚌  {route_name}번\n첫번째 {txt1}  /  두번째 {txt2}"
                if st.button(label, key=f"b{route_id}{i}", use_container_width=True):
                    st.session_state.selected_bus_id=route_id

    # ── 지도 시뮬레이션 ──
    if st.session_state.selected_bus_id and arrivals:
        bus_info = next((b for b in arrivals if b.get('routeId')==st.session_state.selected_bus_id), None)
        if bus_info:
            route_name=bus_info.get('routeName','미상')
            route_id=bus_info.get('routeId','')
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"""<div style="font-size:0.88rem;font-weight:700;color:#7C3AED;margin-bottom:12px;">
              🗺️ {route_name}번 실시간 경로</div>""", unsafe_allow_html=True)

            with st.spinner("경로 분석 중..."):
                buses=fetch_bus_locations(route_id)
                route_stops_list=fetch_route_stops(route_id)

            if not buses or not route_stops_list:
                st.warning("실시간 정보를 가져올 수 없습니다.")
            else:
                target_stop=next((s for s in route_stops_list if str(s.get('stationId'))==str(sel['id'])),None)
                if not target_stop:
                    st.error("정류소 정보를 찾을 수 없습니다.")
                else:
                    target_seq=int(target_stop.get('stationSeq',0))
                    target_lat=float(target_stop.get('stationY',target_stop.get('y',0)))
                    target_lon=float(target_stop.get('stationX',target_stop.get('x',0)))

                    candidates=[]
                    for bus in buses:
                        bsd=next((s for s in route_stops_list if str(s.get('stationId'))==str(bus.get('stationId'))),None)
                        if bsd:
                            bseq=int(bsd.get('stationSeq',0))
                            diff=target_seq-bseq
                            if diff>0:
                                candidates.append({'seq':bseq,'diff':diff,
                                    'lat':float(bsd.get('stationY',bsd.get('y',0))),
                                    'lon':float(bsd.get('stationX',bsd.get('x',0)))})
                    candidates.sort(key=lambda x:x['diff'])
                    bus1=candidates[0] if candidates else None
                    bus2=candidates[1] if len(candidates)>1 else None

                    if bus1:
                        sim1,dist1,n1,seg1=simulate_eta_route_based(route_stops_list,bus1['seq'],target_seq)
                        sim2,dist2,n2,seg2=(None,None,None,[])
                        if bus2:
                            sim2,dist2,n2,seg2=simulate_eta_route_based(route_stops_list,bus2['seq'],target_seq)

                        if dist1>150000 or n1>50 or sim1>120:
                            st.info("🚌 먼 거리 운행 중이거나 위치 정보가 불안정합니다.")
                        else:
                            all_lats=[bus1['lat'],target_lat]+([bus2['lat']] if bus2 else [])
                            all_lons=[bus1['lon'],target_lon]+([bus2['lon']] if bus2 else [])
                            ctr_lat=(min(all_lats)+max(all_lats))/2
                            ctr_lon=(min(all_lons)+max(all_lons))/2

                            m=folium.Map(location=[ctr_lat,ctr_lon],zoom_start=14,tiles='CartoDB positron')
                            route_coords=[(float(s.get('y',s.get('stationY',0))),float(s.get('x',s.get('stationX',0)))) for s in route_stops_list]
                            folium.PolyLine(route_coords,color='#DDD6FE',weight=3,opacity=0.6,dash_array='6,5').add_to(m)
                            if seg1: folium.PolyLine(seg1,color='#7C3AED',weight=6,opacity=0.9).add_to(m)
                            if seg2: folium.PolyLine(seg2,color='#F472B6',weight=5,opacity=0.7).add_to(m)

                            # 1번차 마커 (보라)
                            folium.Marker([bus1['lat'],bus1['lon']],
                                popup=folium.Popup(f"<b>🚌 1번차 · {route_name}번</b><br>약 {sim1}분 후 도착",max_width=200),
                                tooltip=f"1번차 {sim1}분",
                                icon=folium.Icon(color='purple',icon='bus',prefix='fa')).add_to(m)

                            # 2번차 마커 (핑크 뱃지)
                            if bus2 and sim2:
                                folium.Marker([bus2['lat'],bus2['lon']],
                                    popup=folium.Popup(f"<b>🚌 2번차 · {route_name}번</b><br>약 {sim2}분 후 도착",max_width=200),
                                    tooltip=f"2번차 {sim2}분",
                                    icon=folium.DivIcon(
                                        html=f'''<div style="background:linear-gradient(135deg,#EC4899,#F472B6);
                                            color:white;font-weight:700;font-size:11px;
                                            padding:5px 10px;border-radius:20px;white-space:nowrap;
                                            box-shadow:0 3px 10px rgba(236,72,153,0.4);">🚌 2번차</div>''',
                                        icon_size=(72,28),icon_anchor=(36,14))).add_to(m)

                            # 내 정류소 (별)
                            folium.Marker([target_lat,target_lon],
                                popup=folium.Popup(f"<b>📍 {sel['name']}</b>",max_width=200),
                                tooltip=sel['name'],
                                icon=folium.Icon(color='pink',icon='star',prefix='fa')).add_to(m)

                            st_folium(m, width=None, height=440)
                            st.markdown("<hr>", unsafe_allow_html=True)

                            if bus2 and sim2:
                                c1,c2,c3,c4=st.columns(4)
                                with c1: st.metric("노선",f"{route_name}번")
                                with c2: st.metric("🟣 1번차",f"{sim1}분 후")
                                with c3: st.metric("🩷 2번차",f"{sim2}분 후")
                                with c4: st.metric("남은 정류소",f"{n1}개")
                            else:
                                c1,c2,c3=st.columns(3)
                                with c1: st.metric("노선",f"{route_name}번")
                                with c2: st.metric("남은 정류소",f"{n1}개")
                                with c3: st.metric("예상 도착",f"{sim1}분 후")
                    else:
                        st.info("🚌 해당 방향 버스가 운행 중이 아닙니다.")

# ── 푸터 ──
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:8px 0;">
  <span style="font-size:0.75rem; color:#C4B3E8; font-weight:400;">
    경기버스 실시간 도착 정보 &nbsp;·&nbsp; Made with 💜
  </span>
</div>
""", unsafe_allow_html=True)
