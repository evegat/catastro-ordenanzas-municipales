import json
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

session = requests.Session()
session.headers.update(headers)

tier2_targets = [
    ("Yerbas Buenas", "MU342", "https://www.muniyerbasbuenas.cl"),
    ("Olmué", "MU190", "https://www.muniolmue.cl"),
    ("Cunco", "MU071", "https://www.municunco.cl"),
    ("Coelemu", "MU052", "https://www.municoelemu.cl"),
    ("San Ignacio", "MU289", "https://www.munisanignacio.cl"),
    ("Futrono", "MU096", "https://www.munifutrono.cl"),
    ("Tucapel", "MU329", "https://www.munitucapel.cl"),
    ("Catemu", "MU032", "https://www.municatemu.cl"),
    ("Fresia", "MU093", "https://www.munifresia.cl"),
    ("Punitaqui", "MU238", "https://www.munipunitaqui.cl"),
    ("Cholchol", "MU045", "https://www.municholchol.cl"),
    ("Rauco", "MU262", "https://www.munirauco.cl"),
    ("Petorca", "MU215", "https://www.munipetorca.cl"),
]

results = []

for name, mu, web in tier2_targets:
    res = {
        "comuna": name,
        "mu": mu,
        "web": web,
        "web_status": None,
        "cplt_mn_links": [],
        "web_links": [],
    }

    # 1. Web municipal
    try:
        rw = requests.get(web, headers=headers, verify=False, timeout=8)
        res["web_status"] = rw.status_code
        res["web_resolved"] = rw.url
        soup_w = BeautifulSoup(rw.text, "html.parser")
        for a in soup_w.find_all("a"):
            h = a.get("href", "")
            t = a.get_text(" ", strip=True)
            if any(k in (t + " " + h).lower() for k in ["ordenanza", "decreto", "normativa"]):
                res["web_links"].append({"text": t[:50], "href": h})
    except Exception as e:
        res["web_error"] = str(e)[:80]

    # 2. Marco Normativo CPLT
    cplt_url = f"https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/{mu}/PMN/MN"
    try:
        rc = session.get(cplt_url, verify=False, timeout=10)
        res["cplt_status"] = rc.status_code
        if rc.status_code == 200:
            soup_c = BeautifulSoup(rc.text, "html.parser")
            for a in soup_c.find_all("a"):
                h = a.get("href", "")
                t = a.get_text(" ", strip=True)
                if "pdf" in h.lower() or any(w in (t + " " + h).lower() for w in ["ordenanza", "decreto", "reglamento"]):
                    res["cplt_mn_links"].append({"text": t[:50], "href": h})
    except Exception as e:
        res["cplt_error"] = str(e)[:80]

    w_stat = res.get("web_status")
    w_err = res.get("web_error", "")
    c_links_cnt = len(res["cplt_mn_links"])
    w_links_cnt = len(res["web_links"])
    print(f"[{name:14} - {mu}] Web: {w_stat} ({w_err if w_err else 'OK'}) | WebMatches: {w_links_cnt} | CPLTMatches: {c_links_cnt}")
    results.append(res)

with open("data/tier2_probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nSaved probe results to data/tier2_probe_results.json")
