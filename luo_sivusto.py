import os
import json
import datetime
from googleapiclient.discovery import build
from jinja2 import Template
from dotenv import load_dotenv

# --- TIETOTURVAOSIO ---
# 1. Ladataan paikallinen .env tiedosto (jos ollaan omalla koneella)
load_dotenv()

# 2. Haetaan avain ympäristömuuttujista
API_KEY = os.getenv("YOUTUBE_API_KEY")

# 3. Tarkistetaan, löytyikö avain
if not API_KEY:
    print("❌ VIRHE: API-avainta ei löytynyt! Tarkista .env-tiedosto tai GitHub Secrets.")
    exit()

def lataa_kanavat():
    kanavat = {}
    nykyinen = None
    if not os.path.exists("kanavat.txt"): return {}
    with open("kanavat.txt", "r", encoding="utf-8") as f:
        for rivi in f:
            rivi = rivi.strip()
            if not rivi or rivi.startswith("#"): continue
            if rivi.startswith("--- HAKU:"):
                nykyinen = rivi.replace("--- HAKU:", "").replace("---", "").strip()
                kanavat[nykyinen] = []
            elif rivi.startswith('"') and nykyinen:
                kanavat[nykyinen].append(rivi.split(":")[0].replace('"', '').strip())
    return kanavat

def lataa_tapahtumat():
    tapahtumat = []
    if not os.path.exists("tapahtumat.txt"): return []
    with open("tapahtumat.txt", "r", encoding="utf-8") as f:
        for rivi in f:
            osat = rivi.strip().split("|")
            if len(osat) >= 4:
                try:
                    pvm_obj = datetime.datetime.strptime(osat[0].strip(), "%d.%m.%Y")
                    tapahtumat.append({
                        'pvm_raw': pvm_obj, 'pvm': osat[0].strip(),
                        'laji': osat[1].strip(), 'nimi': osat[2].strip(),
                        'paikka': osat[3].strip(), 'lahde': osat[4].strip() if len(osat) > 4 else "AKK"
                    })
                except: continue
    tapahtumat.sort(key=lambda x: x['pvm_raw'])
    return tapahtumat

def luo_sivusto():
    kanavat = lataa_kanavat()
    kaikki_tapahtumat = lataa_tapahtumat()
    tanaan = datetime.datetime.now()
    takaraja = tanaan + datetime.timedelta(days=7)
    viikon_tapahtumat = [t for t in kaikki_tapahtumat if t['pvm_raw'].date() >= tanaan.date() and t['pvm_raw'] <= takaraja]

    youtube = build('youtube', 'v3', developerKey=API_KEY)
    video_data = {}
    kaikki_vids = []

    for genre, id_lista in kanavat.items():
        video_data[genre] = []
        for cid in id_lista:
            try:
                res = youtube.channels().list(id=cid, part='contentDetails').execute()
                up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                v_res = youtube.playlistItems().list(playlistId=up_id, part='snippet', maxResults=5).execute()
                v_ids = [i['snippet']['resourceId']['videoId'] for i in v_res['items']]
                v_stats = youtube.videos().list(id=','.join(v_ids), part='statistics,snippet').execute()
                for item in v_stats['items']:
                    v = {'id': item['id'], 'title': item['snippet']['title'], 'channel': item['snippet']['channelTitle'], 'views': int(item['statistics'].get('viewCount', 0))}
                    video_data[genre].append(v)
                    kaikki_vids.append(v)
            except: continue
    
    top_10 = sorted(kaikki_vids, key=lambda x: x['views'], reverse=True)[:10]
    
    with open("template.html", "r", encoding="utf-8") as f: tm = Template(f.read())
    paivitys = datetime.datetime.now().strftime('%d.%m.%Y klo %H:%M')

    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(tm.render(sivu="etusivu", video_data=video_data, video_data_json=json.dumps(video_data), top_10=top_10, viikon_tapahtumat=viikon_tapahtumat, paivitetty=paivitys))
    
    with open("kalenteri.html", "w", encoding="utf-8") as f: 
        f.write(tm.render(sivu="kalenteri", kaikki_tapahtumat=kaikki_tapahtumat, paivitetty=paivitys))
    
    print("✅ Sivusto luotu onnistuneesti!")

if __name__ == "__main__": luo_sivusto()