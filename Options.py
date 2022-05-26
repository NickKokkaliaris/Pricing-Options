import requests
import pandas as pd
import asyncio
import websockets
import json
import datetime
from datetime import datetime, timedelta

async def call_api(msg):
   async with websockets.connect('wss://test.deribit.com/ws/api/v2') as websocket:
       await websocket.send(msg)
       while websocket.open:
           response = await websocket.recv()
           # do something with the response...
           # print(response)
           return response


ETHmsg = \
{
  "jsonrpc" : "2.0",
  "method" : "public/get_book_summary_by_currency",
  "params" : {
    "currency" : "ETH",
    "kind" : "option"
  }
}

BTCmsg = \
{
  "jsonrpc" : "2.0",
  "method" : "public/get_book_summary_by_currency",
  "params" : {
    "currency" : "BTC",
    "kind" : "option"
  }
}

ETH_json_resp = asyncio.get_event_loop().run_until_complete(call_api(json.dumps(ETHmsg)))
BTC_json_resp = asyncio.get_event_loop().run_until_complete(call_api(json.dumps(BTCmsg)))

# Function used to exctract the desired fields from api's return json
def Field_Exctract(json_resp, field):
    res = json.loads(json_resp)
    df = pd.DataFrame(res["result"])
    Extract = df[field]
    return Extract

# This is a list of all ETH and BTC options in Deribit
ETH_options = Field_Exctract(ETH_json_resp,"instrument_name")
BTC_options = Field_Exctract(BTC_json_resp,"instrument_name")


# Function to exctract all the desired data from Deribit
def get_Data(option):
    msg2 = \
        {
            "jsonrpc" : "2.0",
            "method" : "public/ticker",
            "params" : {
                "instrument_name" : option
            }
        }
    json_resp = asyncio.get_event_loop().run_until_complete(call_api(json.dumps(msg2)))
    # print(json_resp)
    markIV = Field_Exctract(json_resp,"mark_iv")[0]
    bidIV = Field_Exctract(json_resp,"bid_iv")[0]
    askIV = Field_Exctract(json_resp,"ask_iv")[0]
    mark_price = Field_Exctract(json_resp,"mark_price")[0]
    underlying_price = Field_Exctract(json_resp, "underlying_price")[0]
    greeks = Field_Exctract(json_resp,"greeks")
    delta = greeks.loc["delta"]
    gamma = greeks.loc["gamma"]
    theta = greeks.loc["theta"]
    vega = greeks.loc["vega"]
    rho = greeks.loc["rho"]
    option_type_letter = option[len(option)-1]
    idx = option.find("-", option.find("-")+1)
    strike = int(option[idx+1:len(option)-2])
    mat = option[option.find("-")+1:idx]
    maturity = datetime.strptime(mat, "%d%b%y")
    if option_type_letter == 'C':
        option_type = 'Call'
        moneyness = underlying_price / strike
    elif option_type_letter == 'P':
        option_type = 'Put'
        moneyness = strike / underlying_price
    # print(mark_price,markIV,bidIV,askIV)
    # print(maturity)
    output = [option,mark_price,option_type,underlying_price,strike,moneyness,maturity,markIV,bidIV,askIV,delta,gamma,theta,vega,rho]
    return output

# Create empty Dataframe
dfColumns = ['Option','Mark Price','Option Type','Underlying Price','Strike','Moneyness','Maturity','Mark Price Implied Vol','Best Bid Implied Vol','Best Ask Implied Vol','Delta','Gamma','Theta','Vega','Rho']
df = pd.DataFrame(columns = dfColumns)

# Loop for each option in the ETH and BTC list and get the desired data into the dataframe
for i in ETH_options:
    new_row = get_Data(i)
    df = df.append(pd.DataFrame([new_row],columns=dfColumns))

for j in BTC_options:
    new_row = get_Data(j)
    df = df.append(pd.DataFrame([new_row],columns=dfColumns))




# df.to_csv('test.csv',header=True)
#
# print(df)

