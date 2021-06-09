  
import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet

access = ""
secret = ""

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute1")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=30, freq='min')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(minute=30)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(minute=0)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
predict_price("KRW-VET")
schedule.every().minutes.do(lambda: predict_price("KRW-VET"))

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.today()
        start_time = get_start_time("KRW-VET")
        end_time = start_time + datetime.timedelta(minutes=30)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-VET", 0.5)
            current_price = get_current_price("KRW-VET")
            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-VET", krw*0.9995)
        else:
            btc = get_balance("VET")
            btc_current = btc*get_current_price("KRW-VET")
            if btc_current > 5000:
                upbit.sell_market_order("KRW-VET", btc)
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
