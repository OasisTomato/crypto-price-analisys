import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import yfinance as yf
from datetime import date, timedelta
import plotly.graph_objs as go
from PIL import Image
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
from matplotlib import cycler
import numpy as np

dic = {}
url = 'https://finance.yahoo.com/crypto/?offset=0&count=50'

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

symbol_list = []
name_list = []
price_list = []
chgn_price_list = []
chgn_percent_list = []
change_list = []
mcap_list = []

# Store values in separate lists and create a Dictionary list after
for item in soup.select('.simpTblRow'):
    symbol_list.append(item.select('[aria-label=Symbol]')[0].get_text())
    name_list.append(item.select('[aria-label=Name]')[0].get_text())
    price_list.append(item.select('[aria-label*=Price]')[0].get_text())
    #chgn_price_list.append(item.select('[aria-label=Change]')[0].get_text())
    chgn_percent_list.append(item.select('[aria-label="% Change"]')[0].get_text())
    mcap_list.append(item.select('[aria-label="Market Cap"]')[0].get_text())

    # print(item.select('[aria-label="Market cap"]')[0].get_text())
	# print(item.select('[aria-label*="Volume in currency (since"]')[0].get_text())
	# print(item.select('[aria-label*="Volume in currency (24 hrs)"]')[0].get_text())
	# print(item.select('[aria-label*="Total volume all currencies (24 hrs)"]')[0].get_text())
	# print(item.select('[aria-label*="Circulating supply"]')[0].get_text())
	# print(item.select('[aria-label*="52-week range"]')[0].get_text())

dic['Symbol'] = symbol_list
dic['Name'] = name_list
dic['Price'] = price_list
dic['% Change'] = chgn_percent_list
dic['Market Cap'] = mcap_list

# Forge DataFrame from Dictionary and perform a couple of substitution
df_forge = pd.DataFrame(dic)
df_forge.Symbol = df_forge.Symbol.str.replace('-USD', '')
df_forge.Name = df_forge.Name.str.replace(' USD', '')
dic = dict(zip(df_forge.Symbol,df_forge.Name))

# Streamlit Dashboard
st.set_page_config(layout='wide')

# Streamlit Sidebar
fiat = ['USD', 'EUR', 'GBP']
tokens = df_forge.Symbol.values

def by_dates():
    if int_selection == '1m':
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        df = yf.download(tickers=f'{token_selection}-{fiat_selection}', start=str(start_date), end=str(end_date), interval=int_selection)
    elif int_selection != '3mo' or int_selection != '1mo' or int_selection != '1wk' or int_selection != '5d' or int_selection != '1d':
        end_date = date.today()
        start_date = end_date - timedelta(days=59)
        df = yf.download(tickers=f'{token_selection}-{fiat_selection}', start=str(start_date), end=str(end_date), interval=int_selection)

# Streamlit Sidebar
st.sidebar.title("Filters")
token_selection = st.sidebar.selectbox('Tokens', tokens)
fiat_selection = st.sidebar.selectbox('Fiat', fiat)
int_selection = st.sidebar.selectbox('Interval', ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'))
period_selection = st.sidebar.selectbox('Period', ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'))
start_date = st.sidebar.date_input('Start Date', on_change=by_dates)
end_date = st.sidebar.date_input('End Date', on_change=by_dates)

# Streamlit Sidebar Help
st.sidebar.markdown('***')
with st.sidebar.expander('Help'):
    st.markdown('''
                    - Select token and fiat of your choice.
                    - Select Date Range or Period.
                    - Interval 1m, only 7 days data availability
                    - Intraday interval, max 60 days data availability
                    - Interactive plots can be zoomed or hovered to retrieve more info.
                    - Plots can be downloaded using Plotly tools.''')

try:
    df = yf.download(tickers=f'{token_selection}-{fiat_selection}', period=period_selection, interval=int_selection)
except:
    print('This go to nowhere, thanks yfinance')

# Streamlit today price table and historical price plot
icon_name = str.lower(token_selection)
icon_path = f'logos/{icon_name}.png'
st.title("Cryptocurrency Price")
st.info("Please have a look at the Help section before start")
try:
    st.image(icon_path, caption=f'{token_selection} Today')
except:
    st.header(token_selection)

tickerData = yf.Ticker(f'{token_selection}-{fiat_selection}')
df_current_price = tickerData.history(period='1d')
df_price_chart = tickerData.history(period='max')

st.table(df_current_price)
st.bar_chart(df_price_chart.Close)



#  Streamlit historical candlestick chart plot
df['MA100'] = df.Close.rolling(100).mean()
df['MA50'] = df.Close.rolling(50).mean()
df['MA20'] = df.Close.rolling(20).mean()

fig = go.Figure(data=
                [go.Candlestick(x=df.index,
                                open=df.Open, 
                                high=df.High,
                                low=df.Low,
                                close=df.Close,
                                name=f'{token_selection}'), 
                go.Scatter(x=df.index, y=df.MA20, 
                            line=dict(color='yellow',width=2),name='MA20'),
                go.Scatter(x=df.index, y=df.MA50, 
                            line=dict(color='green',width=2),name='MA50'),
                go.Scatter(x=df.index, y=df.MA100, 
                            line=dict(color='red',width=2),name='MA100')])
    
fig.update_layout(go.Layout(xaxis = {'showgrid': True},
                    yaxis = {'showgrid': True}),
                    title=f'{dic[token_selection]} Price Fluctuation with Moving Averages',
                    yaxis_title=f'Price ({fiat_selection})', 
                    xaxis_rangeslider_visible=True)

st.plotly_chart(fig, use_container_width=True)


# Streamlit daily trends plot
st.markdown('## Daily Trends')
st.markdown(f'''
- Line graph below shows the price fluctuation of {token_selection} every minute for today's date ({str(date.today())}).
- The data is automatically updated for the current day.
- The horizontal line shows the current day's open price.
- Green portion indicates the price greater than open price and red for lower.
''')

df_daily = yf.download(tickers=f'{token_selection}-{fiat_selection}', period = '1d', interval = '1m')

fig = go.Figure()
fig.add_scattergl(x=df.index, y=df.Close, 
                    line={'color': 'green'},name='Up trend')
fig.add_scattergl(x=df.index, y=df.Close.where(df.Close <= df.Open[0]), 
                    line={'color': 'red'},name='Down trend')
fig.add_hline(y=df.Open[0])
fig.update_layout(go.Layout(xaxis = {'showgrid': False},
                    yaxis = {'showgrid': False}),
                    title=f'{dic[token_selection]} Daily Trends in Comparison to Open Price',
                    yaxis_title=f'Price ({fiat_selection})',template='plotly_dark',
                    xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# Streamlit top 25 crypto table

st.markdown('## Top 25 Cryptocurrency Prices and Stats')
st.markdown('''
- Realtime price changes (in USD).
- Values updated every few minutes.
- Colour coded column indicates the increase or decrease in price.
''')

# create table from webscraped data
df_forge = df_forge.rename(columns={'Symbol':'Token'})
df_forge['% Change'] = df_forge['% Change'].str.replace('%','').astype(float)

df_forge["color"] = df_forge["% Change"].map(lambda x:'red' if x<0 else 'green')
cols_to_show = ['Name','Token', 'Price', '% Change', 'Market Cap']

# to change color of "% change" column
fill_color = []
n = len(df_forge)
for col in cols_to_show:
    if col!='% Change':
        fill_color.append(['black']*n)
    else:
        fill_color.append(df_forge["color"].to_list())

# Plotly Table
data=[go.Table(columnwidth = [20,15,15,15,15],
                header=dict(values=[f"<b>{col}</b>" for col in cols_to_show],
                font=dict(color='white', size=20),
                height=30,
                line_color='black',
                fill_color='dimgrey',
                align=['left','left', 'right','right','right']),
                cells=dict(values=df_forge[cols_to_show].values.T,
                fill_color=fill_color,
                font=dict(color='white', size=20),
                height=30,
                line_color='black',
                align=['left','left', 'right','right','right']))]

fig = go.Figure(data=data)
fig.update_layout(go.Layout(xaxis = {'showgrid': False},
                    yaxis = {'showgrid': False}))
st.plotly_chart(fig, use_container_width=True)


# Streamlit Sidebar
st.sidebar.title("Support & Resistance")
l_term = st.sidebar.checkbox('Long Term (1y Period)')
s_term = st.sidebar.checkbox('Short Term (6m Period)')
st.write(f'{token_selection} Support and Resistence Lines (5 consecutive candles have been calculated)')


# Long Terms
if l_term:
    df_long = yf.download(tickers=f'{token_selection}-{fiat_selection}', period='1y', interval='1d')
    #df_long.reset_index(inplace=True)
    df_long["Date"] = pd.to_datetime(df_long.index)
    df_long["Date"] = df_long["Date"].apply(mpl_dates.date2num)
    df_long.columns =  ["open", "high", "low", "close", "adj close", "volume", "date"]
    df_long.index.name = "time"
    

    # Create Empty Columns
    df_long['support'] = np.nan
    df_long['resistence'] = np.nan


    # After 5 consecutive decrease of the low, we note this price as support
    df_long.loc[(df_long["low"].shift(5) > df_long["low"].shift(4))&
            (df_long["low"].shift(4) > df_long["low"].shift(3))&
            (df_long["low"].shift(3) > df_long["low"].shift(2))&
            (df_long["low"].shift(2) > df_long["low"].shift(1))&
            (df_long["low"].shift(1) > df_long["low"].shift(0)), "support"] = df_long["low"]

    # After 5 consecutive decrease of the low, we note this price as support
    df_long.loc[(df_long["high"].shift(5) < df_long["high"].shift(4))&
            (df_long["high"].shift(4) < df_long["high"].shift(3))&
            (df_long["high"].shift(3) < df_long["high"].shift(2))&
            (df_long["high"].shift(2) < df_long["high"].shift(1))&
            (df_long["high"].shift(1) < df_long["high"].shift(0)), "resistence"] = df_long["high"]

    # Colors and Settings
    colors = cycler('color', ['#669FEE', '#66EE91', '#9988DD', '#EECC55', '#88BB44', '#FFBBBB'])
    plt.rc('figure', facecolor='#313233')
    plt.rc('axes', facecolor='#313233', edgecolor='none',
        axisbelow=True, grid=True, prop_cycle=colors, labelcolor='gray')
    plt.rc('grid', color='474A4A', linestyle='solid')
    plt.rc('xtick', color='gray')
    plt.rc('ytick', direction='out', color='gray')
    plt.rc('legend', facecolor="#313233", edgecolor='#313233')
    plt.rc('text', color="#C9C9C9")
    plt.rcParams['figure.figsize'] = [20, 8]
    
    
    fig, ax = plt.subplots()
    candlestick_ohlc(ax,df_long[["date", "open", "high", "low", "close"]].values,width=0.6, 
                colorup='#57CE95', colordown='#CE5757', alpha=0.8)
    
    date_format = mpl_dates.DateFormatter('%d %b %Y')
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    fig.tight_layout()

    for resistence, date in zip(df_long["resistence"].dropna(), df_long['resistence'].dropna().index):
        plt.hlines(resistence, xmin=date, xmax=df_long.index[-1], colors='#57CE95', linestyles=':', linewidth=3)

    for resistence, date in zip(df_long["support"].dropna(), df_long['support'].dropna().index):
        plt.hlines(resistence, xmin=date, xmax=df_long.index[-1], colors='#CE5757', linestyles=':', linewidth=3)
    
    plt.savefig('df_long.png')
    st.image('df_long.png', caption=f'{token_selection} Support And Resistence 1y Period')
    

# Shot Terms
if s_term:
    df_short = yf.download(tickers=f'{token_selection}-{fiat_selection}', period='6mo', interval='1d')
    #df_short.reset_index(inplace=True)
    df_short["Date"] = pd.to_datetime(df_short.index)
    df_short["Date"] = df_short["Date"].apply(mpl_dates.date2num)
    df_short.columns =  ["open", "high", "low", "close", "adj close", "volume", "date"]
    df_short.index.name = "time"
    

    # Create Empty Columns
    df_short['support'] = np.nan
    df_short['resistence'] = np.nan


    # After 5 consecutive decrease of the low, we note this price as support
    df_short.loc[(df_short["low"].shift(5) > df_short["low"].shift(4))&
            (df_short["low"].shift(4) > df_short["low"].shift(3))&
            (df_short["low"].shift(3) > df_short["low"].shift(2))&
            (df_short["low"].shift(2) > df_short["low"].shift(1))&
            (df_short["low"].shift(1) > df_short["low"].shift(0)), "support"] = df_short["low"]

    # After 5 consecutive decrease of the low, we note this price as support
    df_short.loc[(df_short["high"].shift(5) < df_short["high"].shift(4))&
            (df_short["high"].shift(4) < df_short["high"].shift(3))&
            (df_short["high"].shift(3) < df_short["high"].shift(2))&
            (df_short["high"].shift(2) < df_short["high"].shift(1))&
            (df_short["high"].shift(1) < df_short["high"].shift(0)), "resistence"] = df_short["high"]

    # Colors and Settings
    colors = cycler('color', ['#669FEE', '#66EE91', '#9988DD', '#EECC55', '#88BB44', '#FFBBBB'])
    plt.rc('figure', facecolor='#313233')
    plt.rc('axes', facecolor='#313233', edgecolor='none',
        axisbelow=True, grid=True, prop_cycle=colors, labelcolor='gray')
    plt.rc('grid', color='474A4A', linestyle='solid')
    plt.rc('xtick', color='gray')
    plt.rc('ytick', direction='out', color='gray')
    plt.rc('legend', facecolor="#313233", edgecolor='#313233')
    plt.rc('text', color="#C9C9C9")
    plt.rcParams['figure.figsize'] = [20, 8]
    
    
    fig, ax = plt.subplots()
    candlestick_ohlc(ax,df_short[["date", "open", "high", "low", "close"]].values,width=0.6, 
                colorup='#57CE95', colordown='#CE5757', alpha=0.8)
    
    date_format = mpl_dates.DateFormatter('%d %b %Y')
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    fig.tight_layout()

    for resistence, date in zip(df_short["resistence"].dropna(), df_short['resistence'].dropna().index):
        plt.hlines(resistence, xmin=date, xmax=df_short.index[-1], colors='#57CE95', linestyles=':', linewidth=3)

    for resistence, date in zip(df_short["support"].dropna(), df_short['support'].dropna().index):
        plt.hlines(resistence, xmin=date, xmax=df_short.index[-1], colors='#CE5757', linestyles=':', linewidth=3)
    
    st.write(f'{token_selection} Support and Resistence Lines (5 consecutive candles have been calculated)')
    plt.savefig('df_short.png')
    st.image('df_short.png', caption=f'{token_selection} Support And Resistence 6m Period')


