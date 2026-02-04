import pandas as pd
from icalendar import Calendar
import datetime
import os

def tuo_tapahtumat(tiedostonimi, tyyppi, lahde_nimi):
    if not os.path.exists(tiedostonimi):
        print(f"❓ Ohitetaan: Tiedostoa '{tiedostonimi}' ei löytynyt.")
        return

    print(f"--- Tuodaan {lahde_nimi}: {tiedostonimi} ---")
    uudet_tapahtumat = []
    
    # AKK käännökset (Varmista että nämä vastaavat kalenterin nappeja!)
    akk_laji_muunnokset = {
        'Jokamiehenluokka': 'Jokkis', 'JM Joukkue': 'Jokkis', 'JM': 'Jokkis',
        'RA': 'Ralli', 'RS': 'Rallisprint', 'RC': 'Rallicross', 'DR': 'Drifting', 'Jäärata-ajo':'Jäärata'
    }

    try:
        if tyyppi == "excel":
            df = pd.read_excel(tiedostonimi)
            df.columns = [c.strip() for c in df.columns]
            for _, row in df.iterrows():
                try:
                    pvm_val = row['LoppuPvm']
                    pvm = pvm_val.strftime('%d.%m.%Y') if isinstance(pvm_val, datetime.datetime) else str(pvm_val).split(' ')[0]
                    raw_laji = str(row['Laji']).strip()
                    laji = akk_laji_muunnokset.get(raw_laji, raw_laji)
                    uudet_tapahtumat.append(f"{pvm} | {laji} | {row['Kilpailun nimi']} | {row['Paikka']} | {lahde_nimi}")
                except: continue
        
        elif tyyppi == "ics":
            with open(tiedostonimi, 'rb') as file:
                gcal = Calendar.from_ical(file.read())
                for component in gcal.walk():
                    if component.name == "VEVENT":
                        pvm = component.get('dtstart').dt.strftime('%d.%m.%Y')
                        nimi = str(component.get('summary')).strip()
                        paikka = str(component.get('location')).strip() if component.get('location') else "Harrastepaikka"
                        
                        # HAMU LOGIIKKA: JÄRJESTYS ON TÄRKEÄ!
                        nimi_lower = nimi.lower()
                        laji = "Harraste"
                        if "sprint" in nimi_lower: laji = "Rallisprint" # TÄMÄ ENSIN!
                        elif "ralli" in nimi_lower: laji = "Ralli"
                        elif "jokkis" in nimi_lower or "jokamiehen" in nimi_lower or "jm" in nimi_lower: laji = "Jokkis"
                        elif "drifting" in nimi_lower: laji = "Drifting"
                        elif "cross" in nimi_lower: laji = "Rallicross"
                        elif "jäärata" in nimi_lower: laji = "Jäärata"

                        uudet_tapahtumat.append(f"{pvm} | {laji} | {nimi} | {paikka} | {lahde_nimi}")

        if uudet_tapahtumat:
            with open("tapahtumat.txt", "a", encoding="utf-8") as f:
                for t in uudet_tapahtumat: f.write(t + "\n")
            print(f"✅ Tuotiin {len(uudet_tapahtumat)} tapahtumaa.")
    except Exception as e:
        print(f"❌ Virhe: {e}")

if __name__ == "__main__":
    if os.path.exists("tapahtumat.txt"): os.remove("tapahtumat.txt")
    tuo_tapahtumat("kalenteri_akk.xlsx", "excel", "AKK")
    tuo_tapahtumat("kalenteri_hamu.ics", "ics", "HaMu")