import MA_strategy
import yF_Kbar
if __name__ == '__main__':
    stock_id= 1432
    df = MA_strategy.get_MA(stock_id)
    MA_strategy.trade(df)
    df.to_excel(str(stock_id)+".xlsx")
