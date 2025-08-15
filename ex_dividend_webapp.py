import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime

# 模擬瀏覽器 headers，避免 Goodinfo 擋爬
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    ),
    'Referer': 'https://goodinfo.tw/tw/index.asp'
}

# Goodinfo 除權息日程網址
DIVIDEND_SCHEDULE_URL = "https://goodinfo.tw/tw/StockDividendSchedule.asp"
DIVIDEND_POLICY_URL = "https://goodinfo.tw/tw/StockDividendPolicy.asp"

@st.cache_data(show_spinner=False)
def get_ex_dividend_by_date(target_date: str) -> pd.DataFrame:
    """
    擷取指定日期的除權息標的，依成交量排序
    """
    url = f"{DIVIDEND_SCHEDULE_URL}?DATE={quote(target_date)}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'
        dfs = pd.read_html(response.text)
    except Exception as e:
        st.error(f"❌ 無法讀取除權息資料：{e}")
        return pd.DataFrame()

    for df in dfs:
        if "股利發放年度" in df.columns:
            df = df[df["除權息日"] == target_date]
            if "成交股數" in df.columns:
                df["成交股數"] = (
                    df["成交股數"]
                    .astype(str)
                    .str.replace(",", "")
                    .str.replace("N/A", "0")
                    .astype(float)
                )
                df = df.sort_values("成交股數", ascending=False)
            return df

    st.warning("⚠️ 找不到當日除權息資料")
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def get_stock_dividend_info(stock_id: str) -> pd.DataFrame:
    """
    擷取指定股票代號的歷年股利政策資料
    """
    url = f"{DIVIDEND_POLICY_URL}?STOCK_ID={stock_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'
        dfs = pd.read_html(response.text)
    except Exception as e:
        st.error(f"❌ 無法讀取股票資訊：{e}")
        return pd.DataFrame()

    for df in dfs:
        if "股利所屬年" in df.columns:
            return df

    st.warning("⚠️ 查無股利資料，請確認股票代號正確")
    return pd.DataFrame()

# Streamlit 主介面
st.set_page_config(page_title="除權息查詢小網站", layout="wide")
st.title("📈 除權息查詢小網站")

mode = st.radio("請選擇查詢模式：", ["依日期查詢除權息股票", "輸入股票代號查詢股利政策"])

if mode == "依日期查詢除權息股票":
    date_input = st.date_input("📅 選擇查詢日期：", value=datetime.today())
    date_str = date_input.strftime("%Y-%m-%d")
    df = get_ex_dividend_by_date(date_str)
    if not df.empty:
        st.success(f"{date_str} 除權息股票（依成交量排序）：")
        st.dataframe(df[["代號", "名稱", "除權息日", "成交股數", "殖利率(%)"]], use_container_width=True)
    else:
        st.info("當日沒有除權息股票或資料無法取得")

elif mode == "輸入股票代號查詢股利政策":
    stock_id = st.text_input("🔍 輸入股票代號（例如 2330）")
    if stock_id:
        df = get_stock_dividend_info(stock_id)
        if not df.empty:
            st.success(f"📊 股票 {stock_id} 的股利政策：")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("查無資料或讀取失敗")
