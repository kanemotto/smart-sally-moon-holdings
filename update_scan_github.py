from datetime import datetime
from pathlib import Path
from statistics import fmean
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import json, math, ssl, time

OUT=Path(__file__).parent/"github-pages"/"scan.json"

# Broad but curated US universe for Smart Sally: Mag 8, semiconductors,
# AI/cloud, fintech/crypto, space/momentum, insurance and liquid index ETFs.
SYMBOLS=[
 "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AVGO",
 "AMD","MU","TSM","ARM","INTC","QCOM","ASML","AMAT","LRCX","KLAC",
 "MRVL","SMCI","TXN","NXPI","ON","SOXL","SMH","SOXX",
 "PLTR","CRWV","CRCL","ORCL","CRM","SNOW","CRWD","DDOG","NET","AI",
 "HOOD","COIN","SOFI","AFRM","PYPL","XYZ","MSTR","MARA","RIOT",
 "OPEN","UBER","NFLX","SHOP","RIVN","LCID","LIDR",
 "SPCX","RKLB","ASTS","LUNR","IONQ","QUBT",
 "CB","SPY","QQQ","IWM","TQQQ"
]

NAMES={
 "AAPL":"Apple","MSFT":"Microsoft","GOOGL":"Alphabet","AMZN":"Amazon",
 "NVDA":"NVIDIA","META":"Meta","TSLA":"Tesla","AVGO":"Broadcom",
 "AMD":"Advanced Micro Devices","MU":"Micron","TSM":"TSMC","ARM":"Arm",
 "INTC":"Intel","QCOM":"Qualcomm","ASML":"ASML","AMAT":"Applied Materials",
 "LRCX":"Lam Research","KLAC":"KLA","MRVL":"Marvell","SMCI":"Super Micro",
 "PLTR":"Palantir","CRWV":"CoreWeave","CRCL":"Circle","HOOD":"Robinhood",
 "OPEN":"Opendoor","UBER":"Uber","LIDR":"AEye","SPCX":"SpaceX",
 "CB":"Chubb","RKLB":"Rocket Lab","ASTS":"AST SpaceMobile",
 "IONQ":"IonQ","QUBT":"Quantum Computing"
}

def fetch(s):
 u=f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(s)}?interval=5m&range=5d&includePrePost=true";req=Request(u,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
 with urlopen(req,timeout=20,context=ssl.create_default_context()) as r:data=json.load(r)["chart"]["result"][0]
 q=data["indicators"]["quote"][0];rows=[{"t":t,"c":q["close"][i],"h":q["high"][i],"l":q["low"][i],"v":q["volume"][i] or 0} for i,t in enumerate(data["timestamp"]) if q["close"][i] is not None and q["high"][i] is not None and q["low"][i] is not None]
 return rows,data.get("meta",{})

def ema(v,p):
 k=2/(p+1);a=v[0]
 for x in v[1:]:a=x*k+a*(1-k)
 return a

def rsi(v,p=14):
 d=[v[i]-v[i-1] for i in range(len(v)-p,len(v))];g=fmean(max(x,0) for x in d);l=fmean(max(-x,0) for x in d);return 75 if l==0 else 100-100/(1+g/l)

def calc(s):
 rows,meta=fetch(s);cl=[x["c"] for x in rows];recent=rows[-78:];last=cl[-1];prev=meta.get("chartPreviousClose") or meta.get("previousClose") or cl[0];support=min(x["l"] for x in recent);resistance=max(x["h"] for x in recent);strength=rsi(cl);vols=[x["v"] for x in recent];vr=vols[-1]/(fmean(vols[:-1]) or 1);e9,e20=ema(cl[-60:],9),ema(cl[-60:],20);trend="Bullish" if e9>e20*1.001 else "Bearish" if e9<e20*.999 else "Neutral";mid=min(last,support+(resistance-support)*.28);lo,hi=mid*.997,mid*1.003;verdict="WAIT"
 if strength>74 or last>=resistance*.998:verdict="TAKE PROFIT"
 elif trend=="Bullish" and 45<=strength<=68 and last<=hi*1.005:verdict="ENTER"
 elif trend=="Bearish" and strength<42:verdict="AVOID"
 return {"symbol":s,"name":NAMES.get(s) or meta.get("shortName") or s,"price":round(last,2),"changePercent":round((last/prev-1)*100,2),"entryLow":round(lo,2),"entryHigh":round(hi,2),"target2":round(hi*1.02,2),"target3":round(hi*1.03,2),"stop":round(min(lo*.985,support*.997),2),"support":round(support,2),"resistance":round(resistance,2),"rsi":round(strength,2),"volumeRatio":round(vr,2),"verdict":verdict,"trend":trend,"sparkline":[round(x,2) for x in cl[-28:]]}

def main():
 old=json.loads(OUT.read_text()) if OUT.exists() else {"quotes":[]};cache={q["symbol"]:q for q in old.get("quotes",[])};quotes=[];errors=[]
 for s in SYMBOLS:
  try:quotes.append(calc(s))
  except Exception:
   errors.append(s)
   if s in cache:quotes.append(cache[s])
  time.sleep(.15)
 now=datetime.now(ZoneInfo("Asia/Singapore"));OUT.write_text(json.dumps({"updated":now.isoformat(),"updatedShort":now.strftime("%-I:%M %p"),"quotes":quotes,"errors":errors},indent=2)+"\n")

if __name__=="__main__":main()
