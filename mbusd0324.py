import ccxt

import time
import pandas as pd
import pprint
       
import myBinance
import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키

import line_alert #라인 메세지를 보내기 위함!

simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)


access = simpleEnDecrypt.decrypt(my_key.access)
secret = simpleEnDecrypt.decrypt(my_key.secret)
#2023.02.21 : 헤지모드 물타기를 9-10에서 10으로 수정
#binance
binanceX = ccxt.binance(config={
    'apiKey': access, 
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    } })

#Get Market All Coin
Tickers = binanceX.fetch_tickers()


#Invest 1.0 == 100%
Invest_Rate = 1.0 


LovelyCoinList = ['BNB/BUSD','BTC/BUSD']

CoinCnt = len(LovelyCoinList)
print("#####SHORT Coin Cnt:", CoinCnt,"--->", "List:", LovelyCoinList)
danger_rate = -100.0 
rsiShort = 70
rsiLong = 30
print("[[rsiShort]", rsiShort, "[rsiLong]",rsiLong)


rsi15Short = 0 
rsi15Long = 100 
print("[[rsi15Short]", rsi15Short, "[rsi15Long]",rsi15Long)

#st_water_gap_rate = 0.005 #0.5% --> 몇 퍼센트씩 아래에 물타기를 넣을건지,.  0.005이면 0.5%로 -0.5%, -1.0%, -1.5%, 이렇게 물타기 라인을 긋는다.



#선물 테더(BUSD) 마켓에서 거래중인 코인을 거래대금이 많은 순서로 가져옵니다. 여기선 Top 25
#TopCoinList = myBinance.GetTopCoinList(binanceX,25)
#line_alert.SendMessage("Server alive Check!")

#모든 선물 거래가능한 코인을 가져온다.
#for ticker in Tickers:
for ticker in LovelyCoinList:
    try: 
        #하지만 여기서는 BUSD 테더로 살수 있는 모든 선물 거래 코인들을 대상으로 돌려봅니다.
        if "/BUSD" in ticker:
            Target_Coin_Ticker = ticker
            
            #if myBinance.CheckCoinInList(LovelyCoinList,ticker) == False:
            #    continue
       
            
            Target_Coin_Symbol = ticker.replace("/", "")

            print("##### Start Target_Coin_Ticker:", Target_Coin_Ticker)
            
            #캔들 정보 가져온다
            df_1 = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, '1m')
            df_15 = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, '15m')

            sga = df_1['open'][-2]
            jga = df_1['close'][-2]
            #sga15 = df_15['open'][-2]
            #jga15 = df_15['close'][-2]
            print("[Open]", sga)
            print("[Close]",jga)

            rsi1m0 = myBinance.GetRSI(df_1, 9, -1) #CDJ
            rsi1m1 = myBinance.GetRSI(df_1, 9, -2) #CDJ
            rsi15m0 = myBinance.GetRSI(df_15, 9, -1) #CDJ
            rsi15m1 = myBinance.GetRSI(df_15, 9, -2) #CDJ

            print("[rsi1m0]",rsi1m0,"[rsi1m1]", rsi1m1)
            print("[rsi15m0]",rsi15m0,"[rsi15m1]", rsi15m1)

            #잔고 데이타 가져오기 rsi15m0
            balance = binanceX.fetch_balance(params={"type": "future"})

            time.sleep(0.1)
            #pprint.pprint(balance)
            #print(balance['BUSD'])
            print("[Total Money]",float(balance['BUSD']['total']))
            print("[emain Money]",float(balance['BUSD']['free']))


            amt_s = 0
            amt_b = 0
            abs_amt_s = 0
            abs_amt_b = 0
            entryPrice_s = 0
            entryPrice_b = 0
            unrealizedProfit_s = 0
            unrealizedProfit_b = 0


            for posi in balance['info']['positions']:
                if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == "SHORT":
                    amt_s = float(posi['positionAmt'])
                    entryPrice_s = float(posi['entryPrice'])
                    leverage = float(posi['leverage'])
                    unrealizedProfit_s = float(posi['unrealizedProfit'])
                    break
            time.sleep(0.1)
            for posi in balance['info']['positions']:
                if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == "LONG":
                    amt_b = float(posi['positionAmt'])
                    entryPrice_b = float(posi['entryPrice'])
                    leverage = float(posi['leverage'])
                    unrealizedProfit_b = float(posi['unrealizedProfit'])
                    break
            abs_amt_s = abs(amt_s)
            abs_amt_b = abs(amt_b)

            print("[amt_s]",amt_s)
            print("[amt_b]",amt_b)
            print("[abs_amt_s]",abs_amt_s)
            print("[abs_amt_b]",abs_amt_b)
            print("[entryPrice_s]",entryPrice_s)
            print("[entryPrice_b]",entryPrice_b)
            print("[unrealizedProfit_s]" + str(unrealizedProfit_s))
            print("[unrealizedProfit_b]" + str(unrealizedProfit_b))
            
            target_rate = 0.005   #0.005 == 0.5%
            target_revenue_rate = target_rate * 100.0 #0.5
            print("[target_revenue_rate]", target_revenue_rate, "[real_target_revenue_rate]", target_revenue_rate * leverage)

            coin_price = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)
            print("[price]", coin_price)

            #Max_Amount = float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(float(balance['BUSD']['total']),coin_price,0.2)))  * leverage
            Max_Amount = float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(float(balance['BUSD']['total']),coin_price,Invest_Rate / CoinCnt)))  * leverage 
            one_percent_amount = Max_Amount / 100
            first_amount = one_percent_amount * 0.1
            

            #최소 주문 수량을 가져온다 
            minimun_amount = myBinance.GetMinimumAmount(binanceX,Target_Coin_Ticker)
            print("[minimun_amount]", minimun_amount)
            if minimun_amount > first_amount:
                first_amount = minimun_amount

            print("[Max_Amount]",Max_Amount)
            print("[one_percent_amount]", one_percent_amount) 
            print("[first_amount]", first_amount) 
            print("[usdt]",first_amount * coin_price)


           
            if entryPrice_s > 0:
                revenue_rate_s = (entryPrice_s - coin_price) / entryPrice_s * 100.0
            else:
                revenue_rate_s = 0
            
            if entryPrice_b > 0:
                revenue_rate_b = (coin_price - entryPrice_b) / entryPrice_b * 100.0
            else:
                revenue_rate_b = 0

            leverage_revenu_rate_s = revenue_rate_s * leverage
            leverage_revenu_rate_b = revenue_rate_b * leverage
            
            buy_percent_s = abs_amt_s / one_percent_amount
            buy_percent_b = abs_amt_b / one_percent_amount
            
            total_profit = unrealizedProfit_s + unrealizedProfit_b
            #revenue_rate_sum = revenue_rate_s + revenue_rate_b
        
            market = 1.001
            print("[revenue_rate_s]",revenue_rate_s ,"[leverage_revenu_rate_s]",leverage_revenu_rate_s)
            print("[revenue_rate_b]",revenue_rate_b, "[leverage_revenu_rate_b]",leverage_revenu_rate_b)

            print("[buy_percent_s]", buy_percent_s)
            print("[buy_percent_b]", buy_percent_b)

            print("[total_profit]", total_profit)

            if abs_amt_s == 0 and rsi1m0 > rsiShort and sga > jga and rsi15m0 > rsi15Short:

                print("#First Short Position")

                binanceX.cancel_all_orders(Target_Coin_Ticker)
                time.sleep(0.1)

                params = {'positionSide': 'SHORT'}
                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'sell', first_amount, sga / market, params))
                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', first_amount, None , params))
                line_alert.SendMessage(Target_Coin_Ticker + '\n' +
                                       'First SELL' + '\n' +
                                       'VOL@'  + str(round(first_amount ,2)) + '\n' +
                                       'BUSD@' + str(round(first_amount * coin_price,2)) + '\n' +
                                       'Profit@' + str(round(unrealizedProfit_s,2)) + '\n' +
                                       'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')
                continue 

            if abs_amt_b == 0 and rsi1m0 < rsiLong and sga < jga and rsi15m0 < rsi15Long: 

                print("#First Long Position")

                binanceX.cancel_all_orders(Target_Coin_Ticker)
                time.sleep(0.1)

                params = {'positionSide': 'LONG'}
                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'buy', first_amount, sga *  market, params))
                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', first_amount, None, params))
                line_alert.SendMessage(Target_Coin_Ticker + '\n' +
                                       'First BUY' + '\n' +
                                       'VOL@'  + str(round(first_amount,2)) + '\n' +
                                       'BUSD@' + str(round(first_amount * coin_price,2)) + '\n' +
                                       'Profit@' + str(round(unrealizedProfit_b,2)) + '\n' +
                                       'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')
                continue

            if (abs_amt_s > 0) or (abs_amt_b > 0):
                if buy_percent_s <= 0.0:
                    water_rate_s = 0.0
                    profit_rate_s = 0.0
                    bcnt_s = 0
                elif buy_percent_s <= 0.1:
                    water_rate_s = -0.1
                    profit_rate_s = 0.5
                    bcnt_s = 1
                elif buy_percent_s <= 0.3:#0.2
                    water_rate_s = -0.2
                    profit_rate_s = 0.6
                    bcnt_s = 2
                elif buy_percent_s <= 0.5:#0.4
                    water_rate_s = -0.3
                    profit_rate_s = 0.7
                    bcnt_s = 3
                elif buy_percent_s <= 0.9:#0.8
                    water_rate_s = -0.4
                    profit_rate_s = 0.8
                    bcnt_s = 4
                elif buy_percent_s <= 2.6:#1.6
                    water_rate_s = -0.5
                    profit_rate_s = 0.9
                    bcnt_s = 5
                elif buy_percent_s <= 4.2:#3.2
                    water_rate_s = -0.6
                    profit_rate_s = 1.0
                    bcnt_s = 6
                elif buy_percent_s <= 9.4:#6.4
                    water_rate_s = -0.7
                    profit_rate_s = 1.1
                    bcnt_s = 7
                elif buy_percent_s <= 19.8:#12.8
                    water_rate_s = -0.8
                    profit_rate_s = 1.2
                    bcnt_s = 8
                elif buy_percent_s <= 29.6:#25.6
                    water_rate_s = -1.0
                    profit_rate_s = 1.3
                    bcnt_s = 9
                elif buy_percent_s <= 59.2:#51.2
                    water_rate_s = -1.5
                    profit_rate_s = 1.4
                    bcnt_s = 10
                else:
                    water_rate_s = -2.0
                    profit_rate_s = 1.5
                    bcnt_s = 11

                if buy_percent_b <= 0.0:
                    water_rate_b = 0.0
                    profit_rate_b = 0.0
                    bcnt_b = 0
                elif buy_percent_b <= 0.1:
                    water_rate_b = -0.1
                    profit_rate_b = 0.5
                    bcnt_b = 1
                elif buy_percent_b <= 0.3:#0.2
                    water_rate_b = -0.2
                    profit_rate_b = 0.6
                    bcnt_b = 2
                elif buy_percent_b <= 0.5:#0.4
                    water_rate_b = -0.3
                    profit_rate_b = 0.7
                    bcnt_b = 3
                elif buy_percent_b <= 0.9:#0.8
                    water_rate_b = -0.4
                    profit_rate_b = 0.8
                    bcnt_b = 4
                elif buy_percent_b <= 2.6:#1.6
                    water_rate_b = -0.5
                    profit_rate_b = 0.9
                    bcnt_b = 5
                elif buy_percent_b <= 4.2:#3.2
                    water_rate_b = -0.6
                    profit_rate_b = 1.0
                    bcnt_b = 6
                elif buy_percent_b <= 9.4:#6.4
                    water_rate_b = -0.7
                    profit_rate_b = 1.1
                    bcnt_b = 7
                elif buy_percent_b <= 19.8:#12.8
                    water_rate_b = -0.8
                    profit_rate_b = 1.2
                    bcnt_b = 8
                elif buy_percent_b <= 29.6:#25.6
                    water_rate_b = -1.0
                    profit_rate_b = 1.3
                    bcnt_b = 9
                elif buy_percent_b <= 59.2:#51.2
                    water_rate_b = -1.5
                    profit_rate_b = 1.4
                    bcnt_b = 10
                else:
                    water_rate_b = -2.0
                    profit_rate_b = 1.5
                    bcnt_b = 11

                print("[water_rate_s]", water_rate_s, "leverage water_rate_s",water_rate_s * leverage )
                print("[profit_rate_s]", profit_rate_s, "leverage Profit Rate",profit_rate_s * leverage )
                print("[bcnt_s]", bcnt_s)

                print("[water_rate_b]", water_rate_b, "leverage water_rate Rate",water_rate_b * leverage )
                print("[profit_rate_b]", profit_rate_b, "leverage Profit Rate",profit_rate_b * leverage )
                print("[bcnt_b]", bcnt_b)

                #if abs_amt_s > abs_amt_b:#init short
                #    revenue_rate_sum = revenue_rate_s
                #elif abs_amt_s < abs_amt_b:#init long
                #    revenue_rate_sum = revenue_rate_b

                #Get Profit
                if bcnt_s <= 9:
                    if revenue_rate_s > profit_rate_s: #and buy_percent > 50.0:
                        print("#short Get Profit")

                        binanceX.cancel_all_orders(Target_Coin_Ticker)
                        time.sleep(0.1)

                        params = {'positionSide': 'SHORT'}
                        #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'buy', abs_amt_s, sga * market, params))
                        print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs_amt_s, None, params))
                        line_alert.SendMessage(Target_Coin_Ticker + '@PROFIT' + '\n' +
                                            'BUY@' + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                            'VOL@'  + str(round(abs_amt_s,2)) + '\n' +
                                            'BUSD@' + str(round(abs_amt_s * entryPrice_s,2)) + '\n'
                                            'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                            'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')
                if bcnt_b <= 9:
                    if revenue_rate_b > profit_rate_b: #and buy_percent > 50.0:
                        print("#long Get Profit")

                        binanceX.cancel_all_orders(Target_Coin_Ticker)
                        time.sleep(0.1)

                        params = {'positionSide': 'LONG'}
                        #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'sell', abs_amt_b, sga / market, params))
                        print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs_amt_b, None, params))
                        line_alert.SendMessage(Target_Coin_Ticker + '@PROFIT' + '\n' +
                                            'SELL@' + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                            'VOL@'  + str(round(abs_amt_b,2)) + '\n' +
                                            'BUSD@' + str(round(abs_amt_b * entryPrice_b,2)) + '\n'
                                            'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                            'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')

                print("############TP : ",total_profit)
                if (bcnt_b >= 10) or (bcnt_s >= 10):
                    if total_profit > 0 and ((abs_amt_s >= abs_amt_b and revenue_rate_s > profit_rate_s) or (abs_amt_s <= abs_amt_b and revenue_rate_b > profit_rate_b)):

                        if abs_amt_s > 0:
                            print("#hedge buy Get Profit")

                            binanceX.cancel_all_orders(Target_Coin_Ticker)
                            time.sleep(0.1)

                            params = {'positionSide': 'SHORT'}
                            #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'buy', abs_amt_s, sga * market, params))
                            print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs_amt_s, None, params))
                            line_alert.SendMessage(Target_Coin_Ticker + '@PROFIT' + '\n' +
                                            'BUY@' + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                            'VOL@'  + str(round(abs_amt_s,2)) + '\n' +
                                            'BUSD@' + str(round(abs_amt_s * entryPrice_s,2)) + '\n'
                                            'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                            'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')
                        time.sleep(0.1) 

                        if abs_amt_b > 0:
                            print("#hedge sell Get Profit")

                            params = {'positionSide': 'LONG'}
                            #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'sell', abs_amt_b, sga / market, params))
                            print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs_amt_b, None, params))
                            line_alert.SendMessage(Target_Coin_Ticker + '@PROFIT' + '\n' +
                                            'SELL@' + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                            'VOL@'  + str(round(abs_amt_b,2)) + '\n' +
                                            'BUSD@' + str(round(abs_amt_b * entryPrice_b,2)) + '\n'
                                            'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                            'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')
          
                #short water
                print('#####Max_Amount : ', Max_Amount,"bcnt_b : ", bcnt_b , "bcnt_s : ", bcnt_s,"[TCT]", Target_Coin_Ticker)
                print('#####(abs_amt_s/2) :', abs_amt_s / 2,"abs_amt_b : ", abs_amt_b,"[TCT]", Target_Coin_Ticker)
                if rsi1m0 >= rsiShort and sga > jga and abs_amt_s > 0:
                    water_amount = abs_amt_s
                    if revenue_rate_s <= water_rate_s: 
                        if Max_Amount > abs_amt_s + water_amount:

                            if bcnt_s <= 9: #go water
                                print("####### <= 9 short water")

                                binanceX.cancel_all_orders(Target_Coin_Ticker)
                                time.sleep(0.1)

                                params = {'positionSide': 'SHORT'}
                                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'sell', water_amount, sga / market, params))
                                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', water_amount, None, params))
                                line_alert.SendMessage(Target_Coin_Ticker + '@LOSS\n' +
                                                    'SELL@' + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                                    'VOL@'  + str(round(water_amount,2)) + '\n' +
                                                    'BUSD@' + str(round(water_amount * entryPrice_s,2)) + '\n'
                                                    'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                                    'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')

                            if bcnt_s == 10 and total_profit < 0: #and (abs_amt_s / 2) >  abs_amt_b: #stop water


                                binanceX.cancel_all_orders(Target_Coin_Ticker)
                                time.sleep(0.1)

                                print("####### == 10 short water")
                                params = {'positionSide': 'SHORT'}
                                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'sell', water_amount, jga / market, params))
                                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', water_amount, None, params))
                                line_alert.SendMessage(Target_Coin_Ticker + '@9_10_Loss\n' +
                                                    'SELL@' + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                                    'VOL@'  + str(round(water_amount,2)) + '\n' +
                                                    'BUSD@' + str(round(water_amount * entryPrice_s,2)) + '\n'
                                                    'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                                    'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')
                                time.sleep(0.1)

                                print("####### == 10 long water")
                                params = {'positionSide': 'LONG'}
                                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'buy', water_amount - abs_amt_b + abs_amt_b, jga * market, params))
                                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', water_amount - abs_amt_b + abs_amt_b, None, params))
                                line_alert.SendMessage(Target_Coin_Ticker + '@9_10_Hedge\n' +
                                                'BUY@' + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                                'VOL@'  + str(round(water_amount - abs_amt_b + abs_amt_b,2)) + '\n' +
                                                'BUSD@' + str(round((water_amount - abs_amt_b + abs_amt_b) * entryPrice_s,2)) + '\n'
                                                'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                                'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')

                            if bcnt_s >= 11: #stop water msg
                                line_alert.SendMessage(Target_Coin_Ticker + '@11\n' +
                                                'BUY@' + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                                'VOL@'  + str(round(abs_amt_s,2)) + '\n' +
                                                'BUSD@' + str(round(abs_amt_s * entryPrice_s,2)) + '\n'
                                                'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                                'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')

                        else:
                            line_alert.SendMessage(Target_Coin_Ticker + '@Full\n' +
                                                'SELL@' + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                                'VOL@'  + str(round(water_amount,2)) + '\n' +
                                                'BUSD@' + str(round(water_amount * entryPrice_s,2)) + '\n'
                                                'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                                'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')
                #long water
                if rsi1m0 <= rsiLong and sga < jga and abs_amt_b > 0:
                    water_amount = abs_amt_b
                    if revenue_rate_b <= water_rate_b: 
                        if Max_Amount > abs_amt_s + water_amount:

                            if bcnt_b <= 9:         
                                print("####### <= 9 long water")

                                binanceX.cancel_all_orders(Target_Coin_Ticker)
                                time.sleep(0.1)

                                params = {'positionSide': 'LONG'}
                                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'buy', water_amount, sga * market, params))
                                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', water_amount, None, params))
                                #time.sleep(0.1)
                                line_alert.SendMessage(Target_Coin_Ticker + '@LOSS\n' +
                                                    'BUY@'  + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                                    'VOL@'  + str(round(water_amount,2)) + '\n' +
                                                    'BUSD@' + str(round(water_amount * entryPrice_b,2)) + '\n'
                                                    'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                                    'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')

                            if bcnt_b == 10 and total_profit < 0:


                                binanceX.cancel_all_orders(Target_Coin_Ticker)
                                time.sleep(0.1)

                                print("####### == 10 long water")
                                params = {'positionSide': 'LONG'}
                                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'buy', water_amount, jga *  market, params))
                                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', water_amount, None, params))
                                line_alert.SendMessage(Target_Coin_Ticker + '@9_10_Loss\n' +
                                                    'BUY@'  + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                                    'VOL@'  + str(round(water_amount,2)) + '\n' +
                                                    'BUSD@' + str(round(water_amount * entryPrice_b,2)) + '\n'
                                                    'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                                    'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')
                                time.sleep(0.1)

                                print("####### == 10 short water")
                                params = {'positionSide': 'SHORT'}
                                #print(binanceX.create_order(Target_Coin_Ticker, 'limit', 'sell', water_amount - abs_amt_s + abs_amt_s, jga / market, params))
                                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', water_amount - abs_amt_s + abs_amt_s, None, params))
                                line_alert.SendMessage(Target_Coin_Ticker + '@9_10_Hedge\n' +
                                                'SELL@'  + str(round(buy_percent_s,2)) + '%(' + str(bcnt_s) + ')' + '\n' +
                                                'VOL@'  + str(round(water_amount - abs_amt_s + abs_amt_s, 2)) + '\n' +
                                                'BUSD@' + str(round((water_amount - abs_amt_s + abs_amt_s) * entryPrice_b,2)) + '\n'
                                                'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                                'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')

                            if bcnt_b >= 11:
                                line_alert.SendMessage(Target_Coin_Ticker + '@==11\n' +
                                                'BUY@'  + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                                'VOL@'  + str(round(abs_amt_b, 2)) + '\n' +
                                                'BUSD@' + str(round(abs_amt_b * entryPrice_b,2)) + '\n'
                                                'Profit@' + str(round(unrealizedProfit_s,2)) + '\n'
                                                'ROE@'  + str(round(leverage_revenu_rate_s,2)) + '%')
                        else:
                            line_alert.SendMessage(Target_Coin_Ticker + '@FULL\n' +
                                                'BUY@' + str(round(buy_percent_b,2)) + '%(' + str(bcnt_b) + ')' + '\n' +
                                                'VOL@'  + str(round(water_amount,2)) + '\n' +
                                                'BUSD@' + str(round(water_amount * entryPrice_b,2)) + '\n'
                                                'Profit@' + str(round(unrealizedProfit_b,2)) + '\n'
                                                'ROE@'  + str(round(leverage_revenu_rate_b,2)) + '%')
            print('sga', sga)
            print('sga open sell', sga / market)
            print('sga open buy' , sga * market)
            print('sga close sell', sga * market)
            print('sga close buy', sga / market)
    except Exception as e:
        print("[#Exception] => ", e)
