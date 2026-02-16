import os
import json
import datetime
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# ASETUKSET
# 1. Yritetään lukea avain GitHubin ympäristömuuttujista
API_KEY = os.environ.get("YOUTUBE_API_KEY")

# 2. Jos ei löydy (ollaan omalla koneella), käytä tätä (vaihda oma avain tähän testatessa!)
if not API_KEY:
    API_KEY = "TÄHÄN_SE_PITKÄ_AVAIN_JOS_OLET_OMALLA_KONEELLA"

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

KATEGORIAT = {
    "Drifting Suomi": ["Drifting SM", "Drifting Suomi", "FPDA Drifting", "Radalle.com Drifting"],
    "Jokkis": ["Jokkis", "Jokamiesluokka", "Jokkisrace", "JM-SM"],
    "Rallicross": ["Rallicross SM", "Rallicross Suomi", "Ralicross"],
    "Ralli": ["Ralli SM", "F-Cup", "Historic Rally Trophy", "Rallisarja", "Ralli Suomi"],
    "Projektit": ["Autoprojekti", "Moottorin rakennus", "Auton rakennus", "Tallivlogi"],
    "Simracing": ["Simracing Suomi", "iRacing Suomi", "Assetto Corsa Suomi", "GT7 Suomi"]
}

def hae_videot(haku_termit):
    if not API_KEY or API_KEY.startswith("TÄHÄN"):
        # Estetään virhe jos avainta ei ole asetettu
        return []

    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
        q = "|".join(haku_termit)
        
        # Haetaan videot (poistettu aikarajoitus jotta varmasti löytyy sisältöä)
        search_response = youtube.search().list(
            q=q,
            part='id,snippet',
            maxResults=10,
            order='date', # Uusimmat ensin
            type='video',
            regionCode='FI',
            relevanceLanguage='fi'
        ).execute()

        videot = []
        for search_result in search_response.get('items', []):
            video_id = search_result['id']['videoId']
            
            # Haetaan katselukerrat
            stats_resp = youtube.videos().list(part='statistics', id=video_id).execute()
            if not stats_resp['items']: continue
            
            views_raw = int(stats_resp['items'][0]['statistics'].get('viewCount', 0))
            
            videot.append({
                'id': video_id,
                'title': search_result['snippet']['title'],
                'channel': search_result['snippet']['channelTitle'],
                'date': search_result['snippet']['publishedAt'],
                'views': f"{views_raw:,}".replace(",", " "),
                'viewCountRaw': views_raw
            })
        return videot
    except Exception as e:
        print(f"❌ Virhe haussa ({haku_termit}): {e}")
        return []

def hae_kalenteri():
    # Kiinteä kalenteridata (tätä voi myöhemmin laajentaa hakemaan netistä)
    return [
        {"pvm": "21.02.", "laji": "Ralli", "nimi": "Hankiralli", "paikka": "Porvoo", "lahde": "AKK"},
        {"pvm": "28.02.", "laji": "Drifting", "nimi": "Jäärata Drifting", "paikka": "Oulu", "lahde": "HaMu"},
        {"pvm": "28.02.", "laji": "Ralli", "nimi": "Tuuri Ralli", "paikka": "Tuuri", "lahde": "AKK"},
        {"pvm": "07.03.", "laji": "Jokkis", "nimi": "Talvimestaruus", "paikka": "Pieksämäki", "lahde": "AKK"},
        {"pvm": "14.03.", "laji": "Rallisprint", "nimi": "Kausala Sprint", "paikka": "Kausala", "lahde": "HaMu"}
    ]

def luo_sivusto():
    print("🚀 Aloitetaan sivuston päivitys...")
    
    video_data = {}
    kaikki_videot = []
    
    # 1. Haetaan videot
    for kategoria, termit in KATEGORIAT.items():
        print(f"   🔍 Haetaan: {kategoria}")
        v = hae_videot(termit)
        video_data[kategoria] = v
        kaikki_videot.extend(v)

    # 2. Haetaan kalenteri
    tapahtumat = hae_kalenteri()

    # 3. Top 10 lista
    kaikki_videot.sort(key=lambda x: x['viewCountRaw'], reverse=True)
    seen = set()
    top_10 = []
    for v in kaikki_videot:
        if v['id'] not in seen:
            top_10.append(v)
            seen.add(v['id'])
        if len(top_10) >= 10: break

    # 4. Generoidaan HTML
    print("📝 Kirjoitetaan tiedostoja...")
    env = Environment(loader=FileSystemLoader('.'))
    tm = env.get_template('template.html')
    now = datetime.datetime.now().strftime("%d.%m.%Y klo %H:%M")
    
    # Muunnetaan JSONiksi jotta JavaScript ymmärtää sen (TÄRKEÄ!)
    v_json = json.dumps(video_data, default=str)

    # Kirjoitetaan index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(tm.render(
            sivu='etusivu', 
            video_data=video_data, 
            video_data_json=v_json, 
            top_10=top_10, 
            viikon_tapahtumat=tapahtumat, # Näytetään kaikki kalenterissa etusivulla
            kaikki_tapahtumat=tapahtumat, 
            paivitetty=now
        ))

    # Kirjoitetaan kalenteri.html
    with open('kalenteri.html', 'w', encoding='utf-8') as f:
        f.write(tm.render(
            sivu='kalenteri', 
            video_data=video_data, 
            video_data_json=v_json, 
            top_10=[], 
            kaikki_tapahtumat=tapahtumat, 
            paivitetty=now
        ))

    print("✅ Valmis! Sivusto on luotu.")

if __name__ == "__main__":
    luo_sivusto()