import requests
import pandas as pd
import time, os
from requests.exceptions import RequestException

# 🔑 Cheia ta Football-Data.org
API_KEY = "0e6ae9600634488c9e13439b917456a4" 
# **Înlocuiește această cheie cu cheia ta reală, activă!**

# ID-urile echipelor din API
ECHIPE = {
    "Real Madrid": 86,
    "Barcelona": 81,
    "Manchester City": 65,
    "Liverpool": 64,
    "Bayern Munich": 5,
    "PSG": 524,
    "Arsenal": 57,
    "Juventus": 109,
    "AC Milan": 98,
    "Inter": 108
}

def determina_rezultat(echipa, gazda, oaspete, scor_g, scor_o):
    """Returnează V / E / Î în funcție de echipă și scor"""
    if scor_g is None or scor_o is None:
        return "-"
    
    try:
        g, o = int(scor_g), int(scor_o)
    except (ValueError, TypeError):
        return "-"

    if g == o:
        return "E"
    
    # Folosim funcția echipe_egale pentru o logică consistentă cu aplicația Streamlit
    # Deși aici nu avem funcția, în contextul acestui script este mai rapid să folosim egalitatea simplă,
    # presupunând că numele din API sunt canonice.
    if echipa == gazda and g > o:
        return "V"
    if echipa == oaspete and o > g:
        return "V"
        
    return "Î"

def extrage_meciuri(team_name, team_id):
    print(f"🔄 Extragem meciurile pentru {team_name}...")
    
    # 🌟 CORECȚIA CRITICĂ: Eliminarea parametrului &limit=20 care cauza eroarea 400
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED"
    headers = {"X-Auth-Token": API_KEY}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status() # Ridică excepție pentru 4xx/5xx erori
    except requests.exceptions.HTTPError as e:
        if "403" in str(e):
            print("⚠️ Eroare 403 — cheia API e invalidă sau expirată. Verifică-ți cheia.")
        elif "400" in str(e):
             print(f"⚠️ Eroare 400 - Bad Request pentru {team_name}. URL-ul este corect. Verifică din nou cheia API.")
        else:
            print(f"⚠️ Eroare de rețea/HTTP pentru {team_name}: {e}")
        return []
    except RequestException as e:
        print(f"⚠️ Eroare de rețea neașteptată pentru {team_name}: {e}")
        return []

    data = r.json()
    meciuri = []
    
    sorted_matches = sorted(data.get("matches", []), key=lambda x: x["utcDate"], reverse=True)
    
    for match in sorted_matches:
        gazda = match["homeTeam"]["name"]
        oaspete = match["awayTeam"]["name"]
        
        scor_g = match["score"]["fullTime"].get("home")
        scor_o = match["score"]["fullTime"].get("away")
        
        data_meci = match["utcDate"][:10]
        competitie = match["competition"]["name"]
        rezultat = determina_rezultat(team_name, gazda, oaspete, scor_g, scor_o)

        meciuri.append({
            "Echipa": team_name,
            "Data": data_meci,
            "Competitie": competitie,
            "Gazda": gazda,
            "Oaspete": oaspete,
            "Scor_Gazda": scor_g, # Pot fi None, dar aplicația Streamlit gestionează asta
            "Scor_Oaspete": scor_o, # Pot fi None, dar aplicația Streamlit gestionează asta
            "Rezultat": rezultat
        })
    print(f"✅ {team_name}: {len(meciuri)} meciuri extrase.")
    return meciuri


def main():
    print("--- 💾 Începe actualizarea datelor din Football-Data.org ---")
    toate = []
    for echipa, team_id in ECHIPE.items():
        toate += extrage_meciuri(echipa, team_id)
        time.sleep(1) # respectă limita API-ului (1s între cereri)

    if toate:
        os.makedirs("data", exist_ok=True)
        df = pd.DataFrame(toate)
        
        # Elimină eventualele dubluri (dacă același meci a fost extras pentru Gazdă și Oaspete)
        df_clean = df.drop_duplicates(subset=["Data", "Gazda", "Oaspete"], keep="first")
        
        # Sortare finală pentru a avea întotdeauna cele mai noi meciuri la început
        df_clean["Data"] = pd.to_datetime(df_clean["Data"])
        df_clean = df_clean.sort_values(by=["Echipa", "Data"], ascending=[True, False])
        
        df_clean.to_csv("data/istoric.csv", index=False, encoding="utf-8-sig")
        print("\n🎉 Salvate cu succes datele complete în **data/istoric.csv**")
        print(f"Total meciuri unice salvate: {len(df_clean)}")
    else:
        print("\n🛑 Nicio echipă nu a returnat date. Verifică-ți cheia API.")


if __name__ == "__main__":
    main()