import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from itertools import combinations
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import os
import time

# === CONFIGURACIÓN ===
symbols = [
    "GLEN_CFD.UK", "DTE_CFD.DE", "ORA_CFD.FR", "TEF_CFD.ES", "VOD_CFD.UK",
    "BMW_CFD.DE", "MBG_CFD.DE", "RNO_CFD.FR", "VOW_CFD.DE", "ML_CFD.FR",
    "ADS_CFD.DE", "PUM_CFD.DE", "GAW_CFD.UK", "MC_CFD.FR", "BTRW_CFD.UK",
    "HEIA_CFD.NL", "KWS_CFD.DE", "TSCO_CFD.UK", "OR_CFD.FR", "BATS_CFD.UK",
    "BP_CFD.UK", "CORN", "INDU_A_CFD.SE", "LGEN_CFD.UK", "BAYN_CFD.DE",
    "BARC_CFD.UK", "BBVA_CFD.ES", "CBK_CFD.DE", "DANSKE_CFD.DK", "LLOY_CFD.UK",
    "NDA_CFD.DK", "SEBa_CFD.SE", "PHIA_CFD.NL", "AIR_CFD.DE", "RR_CFD.UK",
    "AF_CFD.FR", "BBY_CFD.UK", "MAERSKa_CFD.DK", "COL_CFD.ES", "NOKIA_CFD.FI",
    "SAP_CFD.DE", "IBE_CFD.ES", "XAGUSD", "XAUUSD.sml", "AUDCAD", "AUDCHF",
    "AUDJPY", "AUDNZD", "AUDUSD.sml", "CADCHF", "CADJPY", "CHFJPY", "EURAUD",
    "EURCAD", "EURCHF", "EURCZK", "EURDKK", "EURGBP.sml", "EURHUF", "EURJPY",
    "EURNOK", "EURNZD", "EURPLN", "EURTRY", "EURUSD.sml", "GBPAUD", "GBPCAD",
    "GBPCHF", "GBPJPY.sml", "GBPNZD", "GBPUSD.sml", "NZDCAD", "NZDCHF", "NZDJPY",
    "NZDUSD", "SGDJPY", "TRYJPY", "USDCAD", "USDCHF", "USDCNH", "USDCZK",
    "USDDKK", "USDHKD", "USDHUF", "USDJPY.sml", "USDMXN", "USDNOK", "USDPLN",
    "USDSEK", "USDSGD", "USDTRY", "USDZAR", "ZARJPY", "ADAUSD", "AVAXUSD",
    "BCHUSD", "BNBUSD", "BTCUSD", "DOGEUSD", "DOTUSD", "EOSUSD", "ETHUSD",
    "GLMRUSD", "KSMUSD", "LINKUSD", "LTCUSD", "MATICUSD", "SOLUSD", "XLMUSD",
    "XTZUSD", "AU200", "CH20", "CHINAH", "CN50", "DE40", "ES35", "EU50", "FR40",
    "HK50", "JP225", "NL25", "SG30", "UK100", "US100", "US2000",
    "US30", "US500", "COPPER", "NATGAS", "SOYBN", "SUGAR", "UKOIL.sml",
    "USOIL.sml", "WHEAT", "AAPL_CFD.US", "AMZN_CFD.US", "BABA_CFD.US",
    "DIS_CFD.US", "F_CFD.US", "GE_CFD.US", "GOOGL_CFD.US", "META_CFD.US"
]
n_candles = 1000
lot = 0.1

# === FUNCIONES ===

def init_mt5():
    if not mt5.initialize():
        print("MT5 no se pudo iniciar:", mt5.last_error())
        quit()

def shutdown_mt5():
    mt5.shutdown()

def fetch_price_data(symbols, n_candles):
    symbol_data = {}
    for symbol in symbols:
        print("importando", symbol)
        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, n_candles)
        if rates is not None and len(rates) > 0:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            symbol_data[symbol] = df['close']
        else:
            print(f"⚠️ No se pudo obtener datos de {symbol}")
    return symbol_data

def test_cointegration(sym1, sym2, s1, s2):
    df_pair = pd.concat([s1, s2], axis=1, join='inner').dropna()
    df_pair.columns = ['y', 'x']
    if len(df_pair) < 200:
        return None

    X = add_constant(df_pair['x'])
    model = OLS(df_pair['y'], X).fit()
    hedge_ratio = model.params['x']
    spread = df_pair['y'] - hedge_ratio * df_pair['x']
    adf_pvalue = adfuller(spread)[1]

    if adf_pvalue < 0.05:
        return {
            'sym1': sym1,
            'sym2': sym2,
            'hedge_ratio': hedge_ratio,
            'pvalue': adf_pvalue,
            'spread': spread
        }
    return None
def get_valid_volume(symbol, desired_volume):
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"❌ No se pudo obtener información del símbolo {symbol}")
        return None

    min_vol = info.volume_min
    max_vol = info.volume_max
    step = info.volume_step

    # Asegurar que el volumen esté en rango
    volume = max(min_vol, desired_volume)
    volume = min(volume, max_vol)

    # Redondear al múltiplo de step
    steps = round(volume / step)
    valid_volume = round(steps * step, 2)

    print(f"ℹ️ {symbol} - min_vol: {min_vol}, step: {step}, volumen final: {valid_volume}")
    return valid_volume

def place_trade(sym1, sym2, hedge_ratio, direction, entry_spread, mean, std, lot=0.1):
    """
    direction: 1 = long spread, -1 = short spread
    """
    print(f"📡 Enviando órdenes MT5: {'LONG' if direction == 1 else 'SHORT'} spread {sym1} - {sym2}...")
    lot1 = get_valid_volume(sym1, 0.1)
    lot2 = get_valid_volume(sym2, abs(hedge_ratio) * lot1)

    # Selección de símbolos
    if not mt5.symbol_select(sym1, True) or not mt5.symbol_select(sym2, True):
        print(f"❌ No se pudo seleccionar uno de los símbolos: {sym1}, {sym2}")
        return

    price1 = mt5.symbol_info_tick(sym1).ask if direction == 1 else mt5.symbol_info_tick(sym1).bid
    price2 = mt5.symbol_info_tick(sym2).bid if direction == 1 else mt5.symbol_info_tick(sym2).ask

    # Definir el tipo de orden
    type1 = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL
    type2 = mt5.ORDER_TYPE_SELL if direction == 1 else mt5.ORDER_TYPE_BUY

    # Orden 1
    order1 = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": sym1,
        "volume": lot,
        "type": type1,
        "price": price1,
        "deviation": 20,
        "magic": 123456,
        "comment": "Entrada Spread",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK
    }

    result1 = mt5.order_send(order1)
    if result1 is None:
        print(f"❌ Error al enviar orden para {sym1}. Retorno vacío.")
        return
    elif result1.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Orden {sym1} fallida. Código: {result1.retcode}")
        return
    else:
        print(f"✅ Orden {sym1} enviada correctamente.")

    time.sleep(1)  # ligera pausa entre órdenes

    # Orden 2
    order2 = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": sym2,
        "volume": lot * hedge_ratio,
        "type": type2,
        "price": price2,
        "deviation": 20,
        "magic": 123456,
        "comment": "Entrada Spread",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK
    }

    result2 = mt5.order_send(order2)
    if result2 is None:
        print(f"❌ Error al enviar orden para {sym2}. Retorno vacío.")
        return
    elif result2.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Orden {sym2} fallida. Código: {result2.retcode}")
        return
    else:
        print(f"✅ Orden {sym2} enviada correctamente.")

    # Mostrar info general
    print(f"🎯 Spread: {entry_spread:.2f} | TP: {mean:.2f} | SL: {entry_spread + direction * 1.5 * std:.2f}")


# === EJECUCIÓN PRINCIPAL ===

init_mt5()
symbol_data = fetch_price_data(symbols, n_candles)

cointegrated_pairs = []
for sym1, sym2 in combinations(symbol_data.keys(), 2):
    result = test_cointegration(sym1, sym2, symbol_data[sym1], symbol_data[sym2])
    if result:
        cointegrated_pairs.append(result)
        spread = result['spread']
        mean = spread.mean()
        std = spread.std()
        zscore = (spread - mean) / std
        current_z = zscore.iloc[-1]
        spread_entry = spread.iloc[-1]

        print(f"✅ {sym1}-{sym2} cointegrados | p={result['pvalue']:.4f} | β={result['hedge_ratio']:.4f} | z={current_z:.2f}")

        if 2 <= abs(current_z) < 3:
            direction = -1 if current_z > 0 else 1
            place_trade(sym1, sym2, result['hedge_ratio'], direction, spread_entry, mean, std)

shutdown_mt5()