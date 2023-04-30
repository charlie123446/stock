import yF_Kbar
import pandas as pd
import talib


def get_MA(stock_id):
    df = yF_Kbar.get_pic(stock_id, 6)

    df.rename(columns={"Open": "開盤價",
                       "High": "最高價",
                       "Low": "最低價",
                       "Close": "收盤價",
                       "Volume": "交易量"}
              , inplace=True)
    df["MA5"] = talib.SMA(df["收盤價"], 5)
    df["MA10"] = talib.SMA(df["收盤價"], 10)
    df["MA20"] = talib.SMA(df["收盤價"], 20)
    df["diff"] = df["MA5"] - df["MA20"]
    df["upper_Lower"] = df["diff"] > 0
    df["last_upper_Lower"] = df["upper_Lower"].shift(1)
    df["sign"] = df["upper_Lower"] != df["last_upper_Lower"]
    df["成交價"] = df["開盤價"].shift(-1)
    df["long_sign"] = (df["MA5"] > df["MA10"]) & (df["MA10"] > df["MA20"])
    df["long_sell_sign"] = df["MA5"] < df["MA10"]
    tmp = 0
    for i in range(1, 21):
        tmp += df["交易量"].shift(i)
    df["avg_volume"] = tmp/20
    df = df.iloc[20:]

    return df


def trade0(df):
    df["Buy"] = None
    df["Sell"] = None
    hold = 0  # 是否持有

    last_index = df.index[-1]
    for index, row in df.iterrows():
        # 最後一天不交易，並將部位平倉
        if index == last_index:
            if hold == 1:
                df.at[index, "Sell"] = row["收盤價"]
                hold = 0
            break

        # 與前一天的狀態不一樣，今天的MA5比MA20高，沒有持有股票，符合以上條件買入
        if row["sign"] and row["upper_Lower"] and hold == 0:
            df.at[index, "Buy"] = row["成交價"]
            hold = 1
        # 與前一天的狀態不一樣，今天的MA5比MA20低，有持有股票，符合以上條件賣出
        elif row["sign"] and not (row["upper_Lower"]) and hold == 1:
            df.at[index, "Sell"] = row["成交價"]
            hold = 0
    return df


def trade1(df):
    # 買進:MA5>MA10>MA20 賣出: MA5<MA10
    df["Buy"] = None
    df["Sell"] = None
    hold = 0  # 是否持有

    last_index = df.index[-1]
    for index, row in df.iterrows():
        if index == last_index:
            if hold == 1:
                df.at[index, "Sell"] = row["收盤價"]
                hold = 0
            break

        if row["long_sign"] and hold == 0:
            df.at[index, "Buy"] = row["成交價"]
            hold = 1
        elif row["long_sell_sign"] and hold == 1:
            df.at[index, "Sell"] = row["成交價"]
            hold = 0
    return df


def trade2(df):
    # 買進:MA5>MA10>MA20 賣出: MA5<MA10 and 買進賣出時當日成交量大於過去20日平均的2倍
    df["Buy"] = None
    df["Sell"] = None
    hold = 0  # 是否持有

    last_index = df.index[-1]
    for index, row in df.iterrows():
        if index == last_index:
            if hold == 1:
                df.at[index, "Sell"] = row["收盤價"]
                hold = 0
            break

        if row["long_sign"] and (row["交易量"]>row["avg_volume"]*2) and hold == 0:
            df.at[index, "Buy"] = row["成交價"]
            hold = 1
        elif row["long_sell_sign"] and (row["交易量"]>row["avg_volume"]*2) and hold == 1:
            df.at[index, "Sell"] = row["成交價"]
            hold = 0
    return df


def get_KPI(df):
    record_df = pd.DataFrame()
    record_df["Buy"] = df["Buy"].dropna().to_list()
    record_df["Sell"] = df["Sell"].dropna().to_list()
    record_df["Buy_fee"] = record_df["Buy"] * 0.001425
    record_df["Sell_fee"] = record_df["Sell"] * 0.001425
    record_df["Sell_tax"] = record_df["Sell"] * 0.003

    # 交易次數
    trade_time = record_df.shape[0]

    # 總報酬
    record_df["profit"] = (record_df["Sell"] - record_df["Buy"] - record_df["Buy_fee"] - record_df["Sell_fee"] -
                           record_df["Sell_tax"]) * 1000
    total_profit = record_df["profit"].sum()

    # 成敗次數
    win_times = (record_df["profit"] >= 0).sum()
    loss_times = (record_df["profit"] < 0).sum()

    # 勝率
    if trade_time > 0:
        win_rate = win_times / trade_time
    else:
        win_rate = 0

    # 獲利金額
    win_profit = record_df[record_df["profit"] >= 0]["profit"].sum()
    loss_profit = record_df[record_df["profit"] < 0]["profit"].sum()

    # 獲利因子
    profit_factor = abs(win_profit / loss_profit)

    # 平均獲利金額
    if win_times > 0:
        avg_win_profit = win_profit / win_times
    else:
        avg_win_profit = 0

    # 平均虧損金額
    if loss_times > 0:
        avg_loss_profit = loss_profit / loss_times
    else:
        avg_loss_profit = 0

    # 賺賠比
    profit_rate = abs(avg_win_profit / avg_loss_profit)

    # 最大單筆獲利
    max_profit = record_df["profit"].max()

    # 最大單筆虧損
    max_loss = record_df["profit"].min()

    # 最大回落MDD
    record_df["acu_profit"] = record_df["profit"].cumsum()
    MDD = 0
    peak = 0
    for i in record_df["acu_profit"]:
        if i > peak:
            peak = i
        diff = peak - i
        if diff > MDD:
            MDD = diff

    # KPI result
    result_txt = f"\
    交易次數:{trade_time}\n\
    總報酬:{total_profit}\n\
    成功次數:{win_times}\n\
    虧損次數:{loss_times}\n\
    勝率:{win_rate}\n\
    獲利總金額:{win_profit}\n\
    虧損總金額:{loss_profit}\n\
    獲利因子:{profit_factor}\n\
    平均獲利金額:{avg_win_profit}\n\
    平均虧損金額:{avg_loss_profit}\n\
    賺賠比:{profit_rate}\n\
    最大單筆獲利:{max_profit}\n\
    最大單筆虧損:{max_loss}\n\
    MDD:{MDD}"

    record_df.to_excel("excel/final.xlsx")

    return result_txt


def main(stock_id, strategy=0):
    if strategy == 0:
        df = trade0(get_MA(stock_id))
    elif strategy == 1:
        df = trade1(get_MA(stock_id))
    else:
        df = trade2(get_MA(stock_id))
    df.to_excel("excel/middle.xlsx")
    return get_KPI(df)
