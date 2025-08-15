import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/115.0 Safari/537.36'
}

dividend_url = "https://goodinfo.tw/tw/StockDividendSchedule.asp"

@st.cache_data(show_spinner=False)
def get_ex_dividend_by_date(target_date):
    url = f"{dividend_url}?DATE={quote(target_date)}"
    try:
        dfs = pd.read_html(url, encoding='utf-8')
    except Exception as e:
        st.error(f"讀取除權息資料失敗：{e}")
        return pd.DataFrame()

    for df in dfs:
        if "股利發放年度" in df.columns:
            df = df[df["除權息日"] == target_date]
            df["成交股數"] = df["成交股數"].astype(str).str.replace(",", "").astype(float)
            df = df.sort_values("成交股數", ascending=False)
            return df
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def get_stock_dividend_info(stock_id):
    url = f"https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID={stock_id}"
    try:
        dfs = pd.read_html(url, encoding='utf-8')
    except Exception as e:
        st.error(f"讀取股票資訊失敗：{e}")
        return pd.DataFrame()

    for df in dfs:
        if "股利所屬年" in df.columns:
            return df
    return pd.DataFrame()

# Streamlit 網站架構
st.set_page_config(page_title="除權息查詢工具", layout="wide")
st.title("📈 除權息查詢小網站")

mode = st.radio("請選擇查詢模式：", ["依日期查詢除權息股票", "輸入股票代號查詢股利政策"])

if mode == "依日期查詢除權息股票":
    date_input = st.date_input("請選擇日期：", value=datetime.today())
    date_str = date_input.strftime("%Y-%m-%d")
    df = get_ex_dividend_by_date(date_str)
    if not df.empty:
        st.success(f"{date_str} 除權息股票如下（依成交量排序）：")
        st.dataframe(df[["代號", "名稱", "除權息日", "成交股數", "殖利率(%)"]], use_container_width=True)
    else:
        st.warning("當天無除權息股票或資料無法讀取")

elif mode == "輸入股票代號查詢股利政策":
    stock_id = st.text_input("請輸入股票代號（如 2330）：")
    if stock_id:
        df = get_stock_dividend_info(stock_id)
        if not df.empty:
            st.success(f"股票 {stock_id} 的除權息資訊如下：")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("查無此股票資料或資料無法讀取")
