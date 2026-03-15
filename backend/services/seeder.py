"""
ClimaRisk Zone Seeder
======================
Standalone script — creates its own DB engine to avoid event loop conflicts.

Run:
  docker exec climarisk_backend python services/seeder.py
"""

import asyncio
import os
import sys
sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models.zone import Zone

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.environ.get('POSTGRES_USER', 'climarisk')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'climarisk')}@"
    f"{os.environ.get('POSTGRES_HOST', 'postgres')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'climarisk')}"
)

ALL_ZONES = [
    # ── Africa ────────────────────────────────────────────────────────────────
    ("Alger", "DZ-ALG", "Alger", "Algeria", 36.7372, 3.0865, 3415811),
    ("Cairo", "EG-CAI", "Cairo", "Egypt", 30.0444, 31.2357, 10107000),
    ("Lagos", "NG-LAG", "Lagos", "Nigeria", 6.5244, 3.3792, 14862111),
    ("Kano", "NG-KAN", "Kano", "Nigeria", 12.0022, 8.5920, 3848885),
    ("Abuja", "NG-ABJ", "FCT", "Nigeria", 9.0765, 7.3986, 3564126),
    ("Johannesburg", "ZA-GT", "Gauteng", "South Africa", -26.2041, 28.0473, 5635127),
    ("Cape Town", "ZA-WC", "Western Cape", "South Africa", -33.9249, 18.4241, 4618000),
    ("Nairobi", "KE-NAI", "Nairobi", "Kenya", -1.2921, 36.8219, 4397073),
    ("Addis Ababa", "ET-ADD", "Addis Ababa", "Ethiopia", 9.0320, 38.7468, 3384569),
    ("Dar es Salaam", "TZ-DAR", "Dar es Salaam", "Tanzania", -6.7924, 39.2083, 4364541),
    ("Accra", "GH-ACC", "Greater Accra", "Ghana", 5.6037, -0.1870, 2277282),
    ("Casablanca", "MA-CAS", "Casablanca-Settat", "Morocco", 33.5731, -7.5898, 3752000),
    ("Tunis", "TN-TUN", "Tunis", "Tunisia", 36.8190, 10.1658, 1056247),
    ("Kampala", "UG-KMP", "Kampala", "Uganda", 0.3476, 32.5825, 1659600),
    ("Dakar", "SN-DAK", "Dakar", "Senegal", 14.7167, -17.4677, 3137196),
    ("Kinshasa", "CD-KIN", "Kinshasa", "DR Congo", -4.3317, 15.3322, 14970460),
    ("Luanda", "AO-LUA", "Luanda", "Angola", -8.8390, 13.2894, 8329177),
    ("Khartoum", "SD-KHT", "Khartoum", "Sudan", 15.5007, 32.5599, 5274321),
    ("Harare", "ZW-HAR", "Harare", "Zimbabwe", -17.8252, 31.0335, 1542813),
    ("Lusaka", "ZM-LUS", "Lusaka", "Zambia", -15.4166, 28.2833, 2731696),
    ("Maputo", "MZ-MPT", "Maputo", "Mozambique", -25.9692, 32.5732, 1766184),
    ("Antananarivo", "MG-ANT", "Analamanga", "Madagascar", -18.9137, 47.5361, 2610000),
    ("Abidjan", "CI-ABJ", "Abidjan", "Ivory Coast", 5.3600, -4.0083, 4980000),
    ("Douala", "CM-DLA", "Littoral", "Cameroon", 4.0511, 9.7679, 3830000),
    ("Niamey", "NE-NIA", "Niamey", "Niger", 13.5137, 2.1098, 1026848),
    ("Ouagadougou", "BF-OUA", "Centre", "Burkina Faso", 12.3569, -1.5353, 2453496),
    ("Bamako", "ML-BKO", "Bamako", "Mali", 12.6392, -8.0029, 2715000),
    ("Windhoek", "NA-WDH", "Khomas", "Namibia", -22.5597, 17.0832, 431000),
    ("Port Harcourt", "NG-RI", "Rivers", "Nigeria", 4.8156, 7.0498, 1865000),
    ("Warri", "NG-DT", "Delta", "Nigeria", 5.5167, 5.7500, 536000),
    ("Calabar", "NG-CR", "Cross River", "Nigeria", 4.9517, 8.3220, 461796),
    # ── Asia ──────────────────────────────────────────────────────────────────
    ("Beijing", "CN-BJ", "Beijing", "China", 39.9042, 116.4074, 21893095),
    ("Shanghai", "CN-SH", "Shanghai", "China", 31.2304, 121.4737, 24870895),
    ("Guangzhou", "CN-GD", "Guangdong", "China", 23.1291, 113.2644, 18676605),
    ("Chengdu", "CN-SC", "Sichuan", "China", 30.5728, 104.0668, 16330000),
    ("Wuhan", "CN-HB", "Hubei", "China", 30.5928, 114.3055, 11212000),
    ("Chongqing", "CN-CQ", "Chongqing", "China", 29.4316, 106.9123, 32000000),
    ("Nanjing", "CN-NJ", "Jiangsu", "China", 32.0603, 118.7969, 8505500),
    ("Zhengzhou", "CN-HA", "Henan", "China", 34.7466, 113.6253, 10120000),
    ("Changsha", "CN-HN", "Hunan", "China", 28.2278, 112.9388, 8000000),
    ("Nanchang", "CN-JX", "Jiangxi", "China", 28.6820, 115.8579, 6329747),
    ("Yichang", "CN-YIC", "Hubei", "China", 30.6920, 111.2863, 4059100),
    ("Haikou", "CN-HAI", "Hainan", "China", 20.0458, 110.3417, 2046189),
    ("Hong Kong", "HK-HK", "Hong Kong", "China", 22.3193, 114.1694, 7482500),
    ("Taipei", "TW-TPE", "Taipei", "Taiwan", 25.0330, 121.5654, 2646204),
    ("Kaohsiung", "TW-KHH", "Kaohsiung", "Taiwan", 22.6273, 120.3014, 2773533),
    ("Mumbai", "IN-MH", "Maharashtra", "India", 19.0760, 72.8777, 20667656),
    ("Delhi", "IN-DL", "Delhi", "India", 28.6139, 77.2090, 32941000),
    ("Bangalore", "IN-KA", "Karnataka", "India", 12.9716, 77.5946, 13193000),
    ("Chennai", "IN-TN", "Tamil Nadu", "India", 13.0827, 80.2707, 11235000),
    ("Kolkata", "IN-WB", "West Bengal", "India", 22.5726, 88.3639, 14974000),
    ("Patna", "IN-BR", "Bihar", "India", 25.5941, 85.1376, 2046652),
    ("Guwahati", "IN-AS", "Assam", "India", 26.1445, 91.7362, 1000000),
    ("Varanasi", "IN-UP-VAR", "Uttar Pradesh", "India", 25.3176, 82.9739, 1432280),
    ("Muzaffarpur", "IN-BR-MUZ", "Bihar", "India", 26.1209, 85.3647, 393724),
    ("Visakhapatnam", "IN-AP-VIZ", "Andhra Pradesh", "India", 17.6868, 83.2185, 2035922),
    ("Vijayawada", "IN-AP-VJW", "Andhra Pradesh", "India", 16.5062, 80.6480, 1048240),
    ("Tokyo", "JP-13", "Tokyo", "Japan", 35.6762, 139.6503, 13960000),
    ("Osaka", "JP-27", "Osaka", "Japan", 34.6937, 135.5023, 2691000),
    ("Sapporo", "JP-01", "Hokkaido", "Japan", 43.0618, 141.3545, 1973395),
    ("Naha", "JP-47", "Okinawa", "Japan", 26.2124, 127.6809, 317405),
    ("Seoul", "KR-11", "Seoul", "South Korea", 37.5665, 126.9780, 9776000),
    ("Busan", "KR-26", "Busan", "South Korea", 35.1796, 129.0756, 3350000),
    ("Bangkok", "TH-10", "Bangkok", "Thailand", 13.7563, 100.5018, 10539000),
    ("Chiang Mai", "TH-50", "Chiang Mai", "Thailand", 18.7883, 98.9853, 1500000),
    ("Jakarta", "ID-JK", "Jakarta", "Indonesia", -6.2088, 106.8456, 10562088),
    ("Surabaya", "ID-SB", "East Java", "Indonesia", -7.2575, 112.7521, 2874699),
    ("Medan", "ID-SU", "North Sumatra", "Indonesia", 3.5952, 98.6722, 2435252),
    ("Manila", "PH-MNL", "Metro Manila", "Philippines", 14.5995, 120.9842, 13923452),
    ("Cebu", "PH-CEB", "Cebu", "Philippines", 10.3157, 123.8854, 2849213),
    ("Tacloban", "PH-LET", "Leyte", "Philippines", 11.2543, 125.0000, 250000),
    ("Legazpi", "PH-ALB", "Albay", "Philippines", 13.1391, 123.7438, 196639),
    ("Zamboanga", "PH-ZMB", "Zamboanga", "Philippines", 6.9214, 122.0790, 977234),
    ("Kuala Lumpur", "MY-KL", "Kuala Lumpur", "Malaysia", 3.1390, 101.6869, 1768000),
    ("Singapore", "SG-SG", "Singapore", "Singapore", 1.3521, 103.8198, 5850342),
    ("Ho Chi Minh City", "VN-SG", "Ho Chi Minh", "Vietnam", 10.8231, 106.6297, 9000000),
    ("Hanoi", "VN-HN", "Hanoi", "Vietnam", 21.0278, 105.8342, 8000000),
    ("Da Nang", "VN-DN", "Da Nang", "Vietnam", 16.0544, 108.2022, 1100000),
    ("Can Tho", "VN-CT", "Can Tho", "Vietnam", 10.0452, 105.7469, 1235171),
    ("My Tho", "VN-TG", "Tien Giang", "Vietnam", 10.3600, 106.3600, 220000),
    ("Dhaka", "BD-DHA", "Dhaka", "Bangladesh", 23.8103, 90.4125, 21741090),
    ("Chittagong", "BD-CHT", "Chittagong", "Bangladesh", 22.3569, 91.7832, 5000000),
    ("Sylhet", "BD-SYL", "Sylhet", "Bangladesh", 24.8949, 91.8687, 700000),
    ("Khulna", "BD-KHU", "Khulna", "Bangladesh", 22.8456, 89.5403, 1500000),
    ("Cox's Bazar", "BD-COX", "Chittagong", "Bangladesh", 21.4272, 92.0058, 249000),
    ("Karachi", "PK-KHI", "Sindh", "Pakistan", 24.8607, 67.0011, 16093786),
    ("Lahore", "PK-LHR", "Punjab", "Pakistan", 31.5204, 74.3587, 13095000),
    ("Colombo", "LK-COL", "Western", "Sri Lanka", 6.9271, 79.8612, 752993),
    ("Kathmandu", "NP-KTM", "Bagmati", "Nepal", 27.7172, 85.3240, 1442271),
    ("Yangon", "MM-YGN", "Yangon", "Myanmar", 16.8661, 96.1951, 7360703),
    ("Sittwe", "MM-RAK", "Rakhine", "Myanmar", 20.1500, 92.8833, 181000),
    ("Phnom Penh", "KH-PNH", "Phnom Penh", "Cambodia", 11.5564, 104.9282, 2281951),
    ("Riyadh", "SA-RUH", "Riyadh", "Saudi Arabia", 24.7136, 46.6753, 7676654),
    ("Dubai", "AE-DXB", "Dubai", "UAE", 25.2048, 55.2708, 3478300),
    ("Tehran", "IR-THR", "Tehran", "Iran", 35.6892, 51.3890, 9500000),
    ("Istanbul", "TR-IST", "Istanbul", "Turkey", 41.0082, 28.9784, 15636243),
    ("Ankara", "TR-ANK", "Ankara", "Turkey", 39.9334, 32.8597, 5747325),
    ("Baghdad", "IQ-BGD", "Baghdad", "Iraq", 33.3152, 44.3661, 8126755),
    ("Baku", "AZ-BAK", "Baku", "Azerbaijan", 40.4093, 49.8671, 2286200),
    ("Tashkent", "UZ-TAS", "Tashkent", "Uzbekistan", 41.2995, 69.2401, 2571668),
    ("Almaty", "KZ-ALA", "Almaty", "Kazakhstan", 43.2220, 76.8512, 1977011),
    ("Guam", "GU-HAG", "Hagatna", "Guam", 13.4443, 144.7937, 172400),
    # ── Europe ────────────────────────────────────────────────────────────────
    ("Paris", "FR-75", "Île-de-France", "France", 48.8566, 2.3522, 2161000),
    ("Lyon", "FR-69", "Auvergne-Rhône-Alpes", "France", 45.7640, 4.8357, 522228),
    ("Marseille", "FR-13", "Provence-Alpes-Côte d'Azur", "France", 43.2965, 5.3698, 870731),
    ("Toulouse", "FR-31", "Occitanie", "France", 43.6047, 1.4442, 493465),
    ("Bordeaux", "FR-33", "Nouvelle-Aquitaine", "France", 44.8378, -0.5792, 257804),
    ("Nantes", "FR-44", "Pays de la Loire", "France", 47.2184, -1.5536, 314138),
    ("Strasbourg", "FR-67", "Grand Est", "France", 48.5734, 7.7521, 284677),
    ("Lille", "FR-59", "Hauts-de-France", "France", 50.6292, 3.0573, 232741),
    ("Montpellier", "FR-34", "Occitanie", "France", 43.6108, 3.8767, 290053),
    ("Nice", "FR-06", "Provence-Alpes-Côte d'Azur", "France", 43.7102, 7.2620, 342669),
    ("London", "GB-LND", "Greater London", "United Kingdom", 51.5074, -0.1278, 8982000),
    ("Birmingham", "GB-BIR", "West Midlands", "United Kingdom", 52.4862, -1.8904, 1141816),
    ("Manchester", "GB-MAN", "Greater Manchester", "United Kingdom", 53.4808, -2.2426, 553230),
    ("Berlin", "DE-BE", "Berlin", "Germany", 52.5200, 13.4050, 3677472),
    ("Hamburg", "DE-HH", "Hamburg", "Germany", 53.5753, 10.0153, 1853935),
    ("Munich", "DE-BY", "Bavaria", "Germany", 48.1351, 11.5820, 1488202),
    ("Frankfurt", "DE-HE", "Hesse", "Germany", 50.1109, 8.6821, 763380),
    ("Madrid", "ES-MD", "Madrid", "Spain", 40.4168, -3.7038, 3305408),
    ("Barcelona", "ES-CT", "Catalonia", "Spain", 41.3851, 2.1734, 1620343),
    ("Valencia", "ES-VC", "Valencia", "Spain", 39.4699, -0.3763, 800666),
    ("Malaga", "ES-MA", "Andalusia", "Spain", 36.7213, -4.4214, 578460),
    ("Rome", "IT-RM", "Lazio", "Italy", 41.9028, 12.4964, 4355725),
    ("Milan", "IT-MI", "Lombardy", "Italy", 45.4654, 9.1859, 1396059),
    ("Palermo", "IT-PA", "Sicily", "Italy", 38.1157, 13.3615, 673735),
    ("Amsterdam", "NL-NH", "North Holland", "Netherlands", 52.3676, 4.9041, 921402),
    ("Brussels", "BE-BRU", "Brussels", "Belgium", 50.8503, 4.3517, 1208542),
    ("Vienna", "AT-WI", "Vienna", "Austria", 48.2082, 16.3738, 1897491),
    ("Zurich", "CH-ZH", "Zurich", "Switzerland", 47.3769, 8.5417, 434335),
    ("Stockholm", "SE-AB", "Stockholm", "Sweden", 59.3293, 18.0686, 975551),
    ("Oslo", "NO-03", "Oslo", "Norway", 59.9139, 10.7522, 1049475),
    ("Copenhagen", "DK-84", "Capital Region", "Denmark", 55.6761, 12.5683, 794128),
    ("Helsinki", "FI-01", "Uusimaa", "Finland", 60.1699, 24.9384, 656920),
    ("Warsaw", "PL-MZ", "Masovian", "Poland", 52.2297, 21.0122, 1860281),
    ("Prague", "CZ-PR", "Prague", "Czech Republic", 50.0755, 14.4378, 1324277),
    ("Budapest", "HU-BU", "Budapest", "Hungary", 47.4979, 19.0402, 1752704),
    ("Bucharest", "RO-B", "Bucharest", "Romania", 44.4268, 26.1025, 2161347),
    ("Athens", "GR-AT", "Attica", "Greece", 37.9838, 23.7275, 3153000),
    ("Thessaloniki", "GR-THE", "Central Macedonia", "Greece", 40.6401, 22.9444, 1110551),
    ("Lisbon", "PT-11", "Lisbon", "Portugal", 38.7223, -9.1393, 547631),
    ("Moscow", "RU-MOW", "Moscow", "Russia", 55.7558, 37.6173, 12506468),
    ("Saint Petersburg", "RU-SPE", "Saint Petersburg", "Russia", 59.9311, 30.3609, 5598486),
    ("Krasnoyarsk", "RU-KYA", "Krasnoyarsk Krai", "Russia", 56.0153, 92.8932, 1090811),
    ("Irkutsk", "RU-IRK", "Irkutsk Oblast", "Russia", 52.2978, 104.2964, 623562),
    ("Yakutsk", "RU-SA", "Sakha Republic", "Russia", 62.0355, 129.6755, 355521),
    ("Khabarovsk", "RU-KHA", "Khabarovsk Krai", "Russia", 48.4827, 135.0840, 618150),
    ("Kyiv", "UA-KIV", "Kyiv", "Ukraine", 50.4501, 30.5234, 2967360),
    # ── Americas ──────────────────────────────────────────────────────────────
    ("New York", "US-NY", "New York", "United States", 40.7128, -74.0060, 8336817),
    ("Los Angeles", "US-CA", "California", "United States", 34.0522, -118.2437, 3979576),
    ("Chicago", "US-IL", "Illinois", "United States", 41.8781, -87.6298, 2693976),
    ("Houston", "US-TX", "Texas", "United States", 29.7604, -95.3698, 2304580),
    ("Miami", "US-FL", "Florida", "United States", 25.7617, -80.1918, 470914),
    ("New Orleans", "US-LA", "Louisiana", "United States", 29.9511, -90.0715, 383997),
    ("Seattle", "US-WA", "Washington", "United States", 47.6062, -122.3321, 737255),
    ("Sacramento", "US-SAC", "California", "United States", 38.5816, -121.4944, 524943),
    ("Fresno", "US-FRE", "California", "United States", 36.7378, -119.7871, 542107),
    ("Redding", "US-RED", "California", "United States", 40.5865, -122.3917, 92724),
    ("Memphis", "US-TN", "Tennessee", "United States", 35.1495, -90.0490, 633104),
    ("Toronto", "CA-ON", "Ontario", "Canada", 43.6532, -79.3832, 2731571),
    ("Montreal", "CA-QC", "Quebec", "Canada", 45.5017, -73.5673, 1762949),
    ("Vancouver", "CA-BC", "British Columbia", "Canada", 49.2827, -123.1207, 675218),
    ("Mexico City", "MX-CMX", "Mexico City", "Mexico", 19.4326, -99.1332, 9209944),
    ("Veracruz", "MX-VER", "Veracruz", "Mexico", 19.1738, -96.1342, 607000),
    ("Cancún", "MX-CUN", "Quintana Roo", "Mexico", 21.1619, -86.8515, 888797),
    ("São Paulo", "BR-SP", "São Paulo", "Brazil", -23.5505, -46.6333, 12325232),
    ("Rio de Janeiro", "BR-RJ", "Rio de Janeiro", "Brazil", -22.9068, -43.1729, 6747815),
    ("Belém", "BR-PA", "Pará", "Brazil", -1.4558, -48.5044, 2272762),
    ("Marabá", "BR-PA-MAR", "Pará", "Brazil", -5.3686, -49.1178, 283542),
    ("Sinop", "BR-MT-SIN", "Mato Grosso", "Brazil", -11.8642, -55.5014, 146247),
    ("Porto Velho", "BR-RO", "Rondônia", "Brazil", -8.7612, -63.9004, 428527),
    ("Buenos Aires", "AR-C", "Buenos Aires", "Argentina", -34.6037, -58.3816, 15369919),
    ("Lima", "PE-LIM", "Lima", "Peru", -12.0464, -77.0428, 11044900),
    ("Bogotá", "CO-CUN", "Cundinamarca", "Colombia", 4.7110, -74.0721, 10978360),
    ("Santiago", "CL-RM", "Metropolitan Region", "Chile", -33.4489, -70.6693, 7112808),
    ("Port-au-Prince", "HT-OU", "Ouest", "Haiti", 18.5944, -72.3074, 2844229),
    ("San Juan", "PR-SJ", "San Juan", "Puerto Rico", 18.4655, -66.1057, 395326),
    ("Kingston", "JM-KGN", "Kingston", "Jamaica", 17.9971, -76.7936, 937700),
    ("Port of Spain", "TT-POS", "Port of Spain", "Trinidad and Tobago", 10.6549, -61.5019, 544000),
    # ── Oceania ───────────────────────────────────────────────────────────────
    ("Sydney", "AU-NSW", "New South Wales", "Australia", -33.8688, 151.2093, 5312000),
    ("Melbourne", "AU-VIC", "Victoria", "Australia", -37.8136, 144.9631, 5078000),
    ("Brisbane", "AU-QLD", "Queensland", "Australia", -27.4698, 153.0251, 2560720),
    ("Darwin", "AU-NT-DAR", "Northern Territory", "Australia", -12.4634, 130.8456, 147255),
    ("Alice Springs", "AU-NT-ALI", "Northern Territory", "Australia", -23.6980, 133.8807, 28671),
    ("Cairns", "AU-QLD-CAI", "Queensland", "Australia", -16.9186, 145.7781, 153000),
    ("Auckland", "NZ-AUK", "Auckland", "New Zealand", -36.8509, 174.7645, 1657200),
    ("Port Moresby", "PG-NCD", "National Capital", "Papua New Guinea", -9.4438, 147.1803, 364145),
]


async def seed_all():
    print(f"\n🌍 ClimaRisk Zone Seeder")
    print("="*60)
    print(f"   Total zones to process: {len(ALL_ZONES)}")

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        added = skipped = 0
        for name, code, region, country, lat, lon, population in ALL_ZONES:
            result = await db.execute(select(Zone).where(Zone.code == code))
            if result.scalar_one_or_none():
                skipped += 1
                continue
            db.add(Zone(
                name=name, code=code, region=region, country=country,
                latitude=lat, longitude=lon, population=population, is_active=True,
            ))
            added += 1
            if added % 50 == 0:
                await db.commit()
                print(f"   {added} zones added...")
        await db.commit()

    await engine.dispose()
    print(f"\n✅ Done! Added: {added}  Skipped: {skipped}  Total: {added + skipped}")
    print("The scheduler will run predictions for all zones automatically.")


if __name__ == "__main__":
    asyncio.run(seed_all())