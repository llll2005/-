import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 設定要生成的檔案名稱
FILE_NAME = 'history_data.csv'

def generate_mock_data(start_date_str, days=90):
    """
    生成指定天數的模擬經營數據
    start_date_str: '2023-10-01'
    days: 要生成幾天
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    dates = [start_date + timedelta(days=x) for x in range(days)]

    data = []
    for d in dates:
        is_weekend = d.weekday() >= 5 # 5=週六, 6=週日

        # --- 模擬金門淡旺季與週末邏輯 ---

        # 基礎營收 (週末加成)
        base_rev = 3500 if not is_weekend else 9000
        # 加入波動 (Random noise)
        revenue = base_rev + np.random.randint(-800, 1500)

        # 住房率 (平日低，週末高)
        base_occ = 0.35 if not is_weekend else 0.90
        occupancy = base_occ + np.random.uniform(-0.1, 0.05)
        occupancy = max(0, min(1, occupancy)) # 限制在 0~1 之間

        # 轉換率 (Conversion Rate)
        cvr = np.random.uniform(1.0, 3.5)
        if is_weekend: cvr += 0.8

        data.append([d.strftime("%Y-%m-%d"), int(revenue), round(occupancy, 2), round(cvr, 2)])

    new_df = pd.DataFrame(data, columns=['日期', '營收', '住房率', '轉換率'])
    return new_df

def save_to_csv(df):
    """將資料存入 CSV (如果檔案存在則附加，不存在則建立)"""
    if os.path.exists(FILE_NAME):
        # 讀取舊資料，避免重複日期 (這裡簡單做，直接往下疊加)
        df.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
        print(f"✅ 已成功新增 {len(df)} 筆資料到 {FILE_NAME}")
    else:
        df.to_csv(FILE_NAME, mode='w', header=True, index=False, encoding='utf-8-sig')
        print(f"🎉 已建立新檔案 {FILE_NAME} 並寫入 {len(df)} 筆資料")

if __name__ == "__main__":
    print("--- 🛠️ 測試資料產生器 ---")
    start = input("請輸入開始日期 (格式 YYYY-MM-DD，預設 2023-10-01): ") or "2023-10-01"
    days = input("要生成幾天的資料? (預設 90): ") or "90"

    df = generate_mock_data(start, int(days))
    save_to_csv(df)
    print("完成！現在你可以去執行 app.py 了。")