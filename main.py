from binance.client import Client
import secrets
import websocket
import json
import numpy as np
import talib
from datetime import datetime  
import telegramBot as tlg

# Insere a criptomeda e seu intervalo de tempo gráfico
TRADE_SYMBOL = 'BTCUSDT'
TIME_INTERVAL = Client.KLINE_INTERVAL_1MINUTE
closes = []

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes

    json_message = json.loads(message)
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        
        closes.append(float(close))
        np_closes = np.array(closes)

        # Bandas de Bollinger
        if len(closes) > 21:
            upper, middle, lower = talib.BBANDS(np_closes, 21, 2, 2)
            last_BBupper = upper[-1]
            last_BBlower = lower[-1]

        # Estocástico lento RSI
        if len(closes) > 21:
           fastk, fastd = talib.STOCHRSI(np_closes,timeperiod=21, fastk_period=21, fastd_period=3, fastd_matype=3) 
           last_SRSIk = fastk[-1]
           last_SRSId = fastd[-1]
           
        # Estocástico lento tradicional
        if len(closes) > 7:
           rsi = talib.RSI(np_closes, 8)
           last_RSI = rsi[-1]   

        data_e_hora_atuais = datetime.now()
        data_e_hora_em_texto = data_e_hora_atuais.strftime('%d/%m/%Y %H:%M')   
        
        # Verifica se o estocástico lento está sobrevendido 
        if (last_RSI > 80 and last_SRSIk > 80 and last_SRSId > 80):
            telegramBot.send_msg("⚠️ESTOCÁTISCO SOBREVENDIDO⚠️ \n⬆️OPORTUNIDADE DE COMPRA⬆️" +
            "\nCriptomoeda:" " " + TRADE_SYMBOL +
            "\nData e Hora:" " " + data_e_hora_em_texto +
            "\nPreço atual:" " " + format(float(close),'.6f') +
            "\nEstocástico RSI:" " " + format(last_SRSIk,'.2f') + format(last_SRSId,'.2f') + 
            "\nEstocástico:" " "+ format(float(last_RSI),'.4f'))

            # Verifica se as bandas de bollinger foram rompidas para cima
            if float(close) >= last_BBupper:
                    telegramBot.send_msg("⚠️ROMPEU BOLLINGER PARA CIMA⚠️ \n⬆️OPORTUNIDADE DE VENDA⬆️")

        # Verifica se o estocástico lento está sobrecomprado       
        elif (last_RSI < 20 and last_SRSIk < 20 and last_SRSId < 20):
            telegramBot.send_msg("⚠️ESTOCÁTISCO SOBRECOMPRADO⚠️ \n⬇️OPORTUNIDADE DE VENDA⬇️" +
            "\nCriptomoeda:" " " + TRADE_SYMBOL +
            "\nData e Hora:" " " + data_e_hora_em_texto +
            "\nPreço atual:" " " + format(float(close),'.6f') +
            "\nEstocástico RSI:" " " + format(last_SRSIk,'.2f') + format(last_SRSId,'.2f') + 
            "\nEstocástico:" " "+ format(float(last_RSI),'.4f'))

            # Verifica se as bandas de bollinger foram rompidas para baixo
            if float(close) <= last_BBupper:
                    telegramBot.send_msg("⚠️ROMPEU BOLLINGER PARA BAIXO⚠️ \n⬆️OPORTUNIDADE DE COMPRA⬆️")
            
# Acessa a conta da Binance via API
if __name__== "__main__":
    client = Client(secrets.API_KEY, secrets.API_SECRET)

    telegramBot = tlg.BotTelegram(secrets.TOKEN,secrets.CHAT_ID)
    
    # Mostra status da conta
    status = client.get_account_status()
    telegramBot.send_msg("Status da conta:" + " " + str(status).replace("'data': ",""))

    klines = client.get_historical_klines(TRADE_SYMBOL,TIME_INTERVAL,"1 day ago UTC")

    for candles in range (len(klines) -1 ):
        closes.append(float(klines[candles][4]))
        
    SOCKET = "wss://stream.binance.com:9443/ws/"+TRADE_SYMBOL.lower()+"@kline_"+TIME_INTERVAL
    ws = websocket.WebSocketApp(SOCKET,on_open=on_open,on_close=on_close,on_message=on_message)
    ws.run_forever()
