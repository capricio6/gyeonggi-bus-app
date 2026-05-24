import pandas as pd
import glob

# 폴더 내 가장 큰 CSV 파일 자동 탐색
csv_file = max(glob.glob('*.csv'), key=lambda f: os.path.getsize(f))
print(f"📂 {csv_file} 로딩 중...")

df = pd.read_csv(csv_file, header=None, dtype=str)
# 8번째 컬럼(인덱스 7)에 '경기도'가 포함된 행만 추출
gyeonggi_df = df[df[7].str.contains("경기도", na=False)]

gyeonggi_df.to_csv("gyeonggi_stops.csv", index=False, header=False)
print(f"✅ 경기도 정류소 {len(gyeonggi_df):,}개 추출 완료! (gyeonggi_stops.csv)")