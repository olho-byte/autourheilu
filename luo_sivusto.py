import os
import json
import datetime
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# --- ASETUKSET ---
# 1. Yritetään lukea avain GitHubin ympäristömuuttujista (TÄMÄ ON SE TÄRKEIN KOHTA)
API_KEY = os.environ.get("YOUTUBE_API_KEY")

# 2. Jos avainta ei löydy (esim. omalla koneella), käytetään vara-avainta.
#    GitHubissa tämä ehto ei toteudu, jos Secret on asetettu oikein.
if not API_KEY:
    # Voit laittaa tähän oman avaimesi testausta varten lainausmerkkien väliin, 
    # mutta älä jätä sitä tähän kun lataat GitHubiin, jos haluat pitää sen salassa.
    API_KEY = "TÄHÄN_VOIT_LAITTAA_AVAIMEN_PAIKALLISTA_TESTAUSTA_VARTEN"

# Tulostetaan lokiin tietoa (ei itse avainta), jotta nähdään toimiiko se
if API_KEY and not API_KEY.startswith("TÄHÄN"):
    print(f"✅ API-avain löytyi (pituus: {len(API_KEY)} merkkiä).")
else:
    print("⚠️ VAROITUS: Oikeaa API-avainta ei löytynyt. Videohaut saattavat epäonnistua.")
# -----------------

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
    # Jos avain on yhä oletusarvossa, ei voida hakea
    if not API_KEY or API_KEY.startswith("TÄHÄN"):
        return []

    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
        videot = []
        q = "|".join(haku_termit)
        
        search_response = youtube.search().list(
            q=q, part='id,snippet', maxResults=10, order='date', type='video',
            regionCode='FI', relevanceLanguage='fi'
        ).execute()

        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                video_id = search_result['id']['videoId']
                # Haetaan katselukerrat erikseen
                stats_resp = youtube.videos().list(part='statistics', id=video_id).execute()
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
        print(f"   ❌ Virhe haussa ({q}): {e}")
        return []

def hae_kalenteri():
    # Esimerkkidataa kalenteriin
    return [
        {"pvm": "08.02.", "laji": "Rallisprint", "nimi": "2. Jäsentenvälinen", "paikka": "Rallisprint", "lahde": "AKK"},
        {"pvm": "08.02.", "laji": "Jäärata", "nimi": "Paltamo SM Jäärata 2.", "paikka": "Jäärata", "lahde": "AKK"},
        {"pvm": "14.02.", "laji": "Ralli", "nimi": "Kontiolahti Ralli", "paikka": "Ralli", "lahde": "HaMu"},
        {"pvm": "21.02.", "laji": "Ralli", "nimi": "Hankiralli", "paikka": "Porvoo", "lahde": "AKK"}
    ]

def luo_sivusto():
    print("🚀 Aloitetaan sivuston päivitys...")
    
    video_data = {}
    kaikki_videot = []
    
    # 1. Haetaan videot
    for kategoria, termit in KATEGORIAT.items():
        print(f"   🔍 Kategoria: {kategoria}")
        v = hae_videot(termit)
        video_data[kategoria] = v
        kaikki_videot.extend(v)

    # 2. Haetaan kalenteri
    tapahtumat = hae_kalenteri()

    # 3. Top 10
    kaikki_videot.sort(key=lambda x: x['viewCountRaw'], reverse=True)
    seen = set()
    top_10 = []
    for v in kaikki_videot:
        if v['id'] not in seen:
            top_10.append(v)
            seen.add(v['id'])
        if len(top_10) >= 10: break

    # 4. Kirjoitetaan tiedostot
    print("📝 Kirjoitetaan HTML-tiedostot...")
    env = Environment(loader=FileSystemLoader('.'))
    tm = env.get_template('template.html')
    now = datetime.datetime.now().strftime("%d.%m.%Y klo %H:%M")
    
    # Tärkeä: Muunnetaan data JSONiksi, jotta sivuston haku toimii
    v_json = json.dumps(video_data, default=str)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(tm.render(sivu='etusivu', video_data=video_data, video_data_json=v_json, top_10=top_10, viikon_tapahtumat=tapahtumat, kaikki_tapahtumat=tapahtumat, paivitetty=now))

    with open('kalenteri.html', 'w', encoding='utf-8') as f:
        f.write(tm.render(sivu='kalenteri', video_data=video_data, video_data_json=v_json, top_10=[], kaikki_tapahtumat=tapahtumat, paivitetty=now))

    print("✅ Valmis!")

if __name__ == "__main__":
    luo_sivusto()