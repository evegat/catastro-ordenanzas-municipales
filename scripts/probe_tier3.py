import json
import sys
import urllib3
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

session = requests.Session()
session.headers.update(headers)

tier3_targets = [
    ("Lumaco", "MU159", "https://www.munilumaco.cl"),
    ("Placilla", "MU223", "https://www.muniplacilla.cl"),
    ("Quemchi", "MU248", "https://www.muniquemchi.cl"),
    ("Quinchao", "MU255", "https://www.muniquinchao.cl"),
    ("Pelluhue", "MU207", "https://www.munipelluhue.cl"),
    ("Ercilla", "MU088", "https://www.muniercilla.cl"),
    ("Coinco", "MU054", "https://www.municoinco.cl"),
    ("Los Sauces", "MU156", "https://www.munilossauces.cl"),
    ("Panquehue", "MU201", "https://www.munipanquehue.cl"),
    ("Ninhue", "MU182", "https://www.munininhue.cl"),
    ("Pumanque", "MU237", "https://www.munipumanque.cl"),
    ("Cochrane", "MU050", "https://www.municochrane.cl"),
    ("Camarones", "MU024", "https://www.municamarones.cl"),
    ("Torres del Paine", "MU325", "https://www.munitorresdelpaine.cl"),
    ("Primavera", "MU227", "https://www.muniprimavera.cl"),
    ("Timaukel", "MU320", "https://www.munitimaukel.cl"),
]

results = []

print("=== INICIANDO SONDEO TIER 3 (16 COMUNAS RURALES Y EXTREMAS) ===")

for name, mu, web in tier3_targets:
    res = {
        "comuna": name,
        "mu": mu,
        "web": web,
        "web_status": None,
        "web_links": [],
        "cplt_mn_links": [],
    }

    # 1. Sondeo Web Municipal
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

    # 2. Sondeo Marco Normativo CPLT
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
    c_stat = res.get("cplt_status")
    c_links_cnt = len(res["cplt_mn_links"])
    w_links_cnt = len(res["web_links"])
    print(f"[{name:17} - {mu}] Web: {w_stat} ({w_err if w_err else 'OK'}) | WebMatches: {w_links_cnt} | CPLT: {c_stat} (Matches: {c_links_cnt})")
    results.append(res)

with open("data/tier3_probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nGuardado sondeo Tier 3 en data/tier3_probe_results.json")
