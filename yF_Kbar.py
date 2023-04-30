import yfinance as yf
import mplfinance as fplt
import warnings


def get_data(stock_id, period=1):
    stock_id = str(stock_id) + ".TW"
    data = yf.Ticker(stock_id)
    period = str(period) + "mo"
    ohlc = data.history(period=period)

    ohlc = ohlc.loc[:, ["Open", "High", "Low", "Close", "Volume"]]
    ohlc.index = ohlc.index.tz_localize(None)
    ohlc.to_excel("excel/stock_Kbar.xlsx")

    return ohlc


def draw_candle_chart(stock_id, df):
    warnings.filterwarnings('ignore')
    # 更改欄位名稱
    df.rename(columns={"開盤價": "Open",
                       "最高價": "High",
                       "最低價": "Low",
                       "收盤價": "Close",
                       "交易量": "Volume"}
              , inplace=True)

    mc = fplt.make_marketcolors(
        up='tab:red', down='tab:green',  # 上漲為紅，下跌為綠
        wick={'up': 'red', 'down': 'green'},  # 影線上漲為紅，下跌為綠
        volume='tab:blue',  # 交易量顏色
    )

    s = fplt.make_mpf_style(marketcolors=mc)  # 定義圖表風格

    fplt.plot(
        df,
        type='candle',
        style=s,
        title=str(stock_id),
        ylabel='Price ($)',
        volume=True,
        savefig='img/stock_Kbar.png',
    )


def get_pic(stock_id, period=6):
    df = get_data(stock_id, period)
    draw_candle_chart(stock_id, df)
    return df
