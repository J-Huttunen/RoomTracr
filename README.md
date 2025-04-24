# RoomTracr

Huoneen käyttöasteen ja ympäristödatan mittaus.

⚠️ Tämä README kuvaa projektin nykyistä tilannetta.

⚠️ Dokumentaatio täydentyy vielä.

## Käytetty laitteisto ja palvelut

- Raspberry Pi Zero W
- Pimoroni Enviro+ 
- PIR-liiketunnistin (SBC-PIR)
- PostgreSQL-tietokanta (CSC DBaaS)
- Grafana (asennettu Hetznerin palvelimelle)

## Sensorit ja mitattavat arvot

Sensorit mittaavat seuraavat arvot:

- Lämpötila
- Ilmanpaine
- Ilmankosteus
- Kaasut (oxidised/carbon monoxide, reduced/nitrogen dioxide, NH₃)
- Ilman partikkelit (PM1, PM2.5, PM10)
- Valo (lux)
- Liiketunnistus (motion: True/False)

## Yhteyksien ja IP-osoitteiden konfigurointi

Jotta järjestelmän eri osat voivat kommunikoida CSC:n tietokannan kanssa, hyväksyttiin kaksi IP-osoitetta CSC:n tietokannan CIDR-säännöstöön:

- Raspberry Pi lähettää sensoridataa CSC:n tietokantaan Python-skriptin kautta.
- Hetznerin palvelin pyörittää Grafanaa, joka hakee ja visualisoi tietokannassa olevaa dataa.

### 1. Raspberry Pi:n valmistelu ja Enviro+:n asennus

1. Flashaa Raspberry Pi OS microSD-kortille ja käynnistä Pi.

2. Yhdistä Pi WiFi-verkkoon.

3. Asenna Enviro+-kirjasto:
```bash
git clone https://github.com/pimoroni/enviroplus-python
cd enviroplus-python
./install.sh
```

### 2. PIR-liiketunnistimen kytkeminen

Liiketunnistin kytkettiin suoraan Enviro+-levyn läpivienteihin seuraavasti:

- SIG → GPIO 4 
- VCC → 5V 
- GND → GND
  
![PIR-Sensor](images/rasp&enviro.png)

Tunnistin mittaa liikettä ja palauttaa `True`, kun liikettä havaitaan.

### 3. PostgreSQL-tietokanta CSC:n DBaaS:ssa

1. Luotu tietokanta CSC:n hallintapaneelissa.

2. Lisätty Raspin ja Hetznerin palvelimen IP-osoitteet sallittuihin (CIDR-luettelo).

3. Luotu taulu tietokantaan:
```sql
CREATE TABLE data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature INTEGER,
    pressure INTEGER,
    humidity INTEGER,
    oxidised INTEGER,
    reduced INTEGER,
    nh3 INTEGER,
    pm1 REAL,
    pm2_5 REAL,
    pm10 REAL,
    motion BOOLEAN,
    lux INTEGER
);
```

### 4. Datan keruu (Raspilla)

Python-skripti (`main.py`) lukee sensoreita ja tallentaa arvot PostgreSQL-tietokantaan 10 sekunnin välein. 

### 5. Grafana (Hetznerin palvelimella)

1. Vuokrattu Hetznerin virtuaalipalvelin (debian).

2. Asennettu Docker ja Grafana
```bash
docker run -d -p 3000:3000 \
  --name=grafana \
  --volume grafana-storage:/var/lib/grafana \
  --restart always \
  grafana/grafana-oss
```

3. Selaimella osoitteeseen `http://<hetzner-ip>:3000`

4. Lisätty PostgreSQL-tietokanta Grafanan tietolähteeksi(Data sources)

5. Luotu Dashboard ja sinne `data`-taulusta kentät (lämpötila, liike, valo...)

![Grafana](images/grafana.png)


## Tilanne tällä hetkellä

- Sensoridatan keruu ja tallennus toimii Raspberryltä CSC:n tietokantaan

- Grafana toimii Hetznerin palvelimella ja lukee dataa onnistuneesti

- PIR-liiketunnistin ja valosensori on mukana datankeruussa
