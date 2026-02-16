import os
import json
import datetime
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# --- ASETUKSET ---
API_KEY = os.environ.get("YOUTUBE_API_KEY")

# Jos olet omalla koneella, voit laittaa avaimesi tähän (mutta älä pushaa sitä GitHubiin)
if not API_KEY:
    API_KEY = "TÄHÄN_AVAIMESI_JOS_TESTAAT_OMALLA_KONEELLA"

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

KATEGORIAT = {
    "Drifting Suomi": ["Drifting SM", "Drifting Suomi", "FPDA Drifting"],
    "Jokkis": ["Jokkis", "Jokamiesluokka", "Jokkisrace", "JM-SM"],
    "Rallicross": ["Rallicross SM", "Rallicross Suomi"],
    "Ralli": ["Ralli SM", "F-Cup", "Historic Rally Trophy", "Rallisarja", "Ralli Suomi"],
    "Projektit": ["Autoprojekti", "Moottorin rakennus", "Auton rakennus", "Tallivlogi"],
    "Simracing": ["Simracing Suomi", "iRacing Suomi", "GT7 Suomi"]
}

def hae_videot(haku_termit):
    if not API_KEY or API_KEY.startswith("TÄHÄN"):
        return []

    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
        
        # Määritetään aikaleima: haetaan vain videoita jotka on julkaistu 30 päivän sisällä
        # Tämä pakottaa YouTuben antamaan tuoretta tavaraa
        aika_raja = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat() + "Z"
        
        q = "|".join(haku_termit)
        
        search_response = youtube.search().list(
            q=q,
            part='id,snippet',
            maxResults=10,
            order='date',      # Järjestys: Uusimmat ensin
            type='video',
            publishedAfter=aika_raja, # <--- TÄMÄ PAKOTTAA TUOREET VIDEOT
            regionCode='FI',
            relevanceLanguage='fi'
        ).execute()

        videot = []
        found_count = len(search_response.get('items', []))
        print(f"      Löytyi {found_count} uutta videota hakusanalla: {q}")

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
        print(f"      ❌ Virhe haussa: {e}")
        return []

def hae_kalenteri():
    # Pidetään kalenteri ennallaan
    return [
        {"pvm": "08.02.", "laji": "Rallisprint", "nimi": "2. Jäsentenvälinen", "paikka": "Rallisprint", "lahde": "AKK"},
        {"pvm": "14.02.", "laji": "Ralli", "nimi": "Kontiolahti Ralli", "paikka": "Ralli", "lahde": "HaMu"},
        {"pvm": "15.02.", "laji": "Jokkis", "nimi": "Akaa JM Talvimestaruus", "paikka": "Jokkis", "lahde": "AKK"},
        {"pvm": "21.02.", "laji": "Ralli", "nimi": "Hankiralli", "paikka": "Porvoo", "lahde": "AKK"},
        {"pvm": "28.02.", "laji": "Ralli", "nimi": "Tuuri Ralli", "paikka": "Tuuri", "lahde": "AKK"}
    ]

def luo_sivusto():
    print(f"🚀 Päivitys aloitettu {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    video_data = {}
    kaikki_videot = []
    
    for kategoria, termit in KATEGORIAT.items():
        print(f"   🔍 Haetaan: {kategoria}")
        vids = hae_videot(termit)
        video_data[kategoria] = vids
        kaikki_videot.extend(vids)

    # Lajittelu ja Top 10
    kaikki_videot.sort(key=lambda x: x['viewCountRaw'], reverse=True)
    seen = set()
    top_10 = []
    for v in kaikki_videot:
        if v['id'] not in seen:
            top_10.append(v)
            seen.add(v['id'])
        if len(top_10) >= 10: break

    # HTML generointi
    env = Environment(loader=FileSystemLoader('.'))
    tm = env.get_template('template.html')
    now_str = datetime.datetime.now().strftime("%d.%m.%Y klo %H:%M")
    v_json = json.dumps(video_data, default=str)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(tm.render(sivu='etusivu', video_data=video_data, video_data_json=v_json, top_10=top_10, viikon_tapahtumat=hae_kalenteri(), kaikki_tapahtumat=hae_kalenteri(), paivitetty=now_str))

    with open('kalenteri.html', 'w', encoding='utf-8') as f:
        f.write(tm.render(sivu='kalenteri', video_data=video_data, video_data_json=v_json, top_10=[], kaikki_tapahtumat=hae_kalenteri(), paivitetty=now_str))

    print(f"✅ Sivusto päivitetty kello {now_str}")

if __name__ == "__main__":
    luo_sivusto()