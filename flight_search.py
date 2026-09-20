import os
import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

API_KEY = os.environ.get("SERPAPI_KEY")

if not API_KEY:
    raise RuntimeError("没有读取到 SERPAPI_KEY")

DEPARTURE_AIRPORTS = "BRU,AMS"
ARRIVAL_AIRPORTS = "PVG,SHA"

START_DATE = date(2026, 10, 21)
END_DATE = date(2026, 10, 25)


def search_flights(outbound_date):
    params = {
        "engine": "google_flights",
        "api_key": API_KEY,
        "departure_id": DEPARTURE_AIRPORTS,
        "arrival_id": ARRIVAL_AIRPORTS,
        "outbound_date": outbound_date,
        "type": "2",
        "travel_class": "1",
        "currency": "EUR",
        "hl": "en",
    }

    url = "https://serpapi.com/search.json?" + urlencode(params)

    with urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


current_date = max(START_DATE, date.today())
all_results = []

while current_date <= END_DATE:
    date_str = current_date.isoformat()

    print(f"\n正在查询 {date_str} ...")

    try:
        data = search_flights(date_str)

        flights = (
            data.get("best_flights", [])
            + data.get("other_flights", [])
        )

        priced_flights = [
            flight for flight in flights
            if isinstance(flight.get("price"), (int, float))
        ]

        if not priced_flights:
            print(f"{date_str}: 没有找到价格")
            current_date += timedelta(days=1)
            continue

        cheapest = min(priced_flights, key=lambda x: x["price"])

        segments = cheapest.get("flights", [])

        departure = segments[0]["departure_airport"]["id"]
        arrival = segments[-1]["arrival_airport"]["id"]

        airlines = []
        for segment in segments:
            airline = segment.get("airline")
            if airline and airline not in airlines:
                airlines.append(airline)

        airline_text = " + ".join(airlines)
        stops = max(len(segments) - 1, 0)
        price = cheapest["price"]

        all_results.append({
            "date": date_str,
            "price": price,
            "departure": departure,
            "arrival": arrival,
            "airline": airline_text,
            "stops": stops,
        })

        print(
            f"{date_str}: €{price} | "
            f"{departure} → {arrival} | "
            f"{airline_text} | 中转 {stops} 次"
        )

    except Exception as e:
        print(f"{date_str}: 查询失败：{e}")

    current_date += timedelta(days=1)


print("\n====================")
print("查询结果汇总")
print("====================")

if all_results:
    for item in all_results:
        print(
            f"{item['date']}  €{item['price']}  "
            f"{item['departure']} → {item['arrival']}  "
            f"{item['airline']}"
        )

    cheapest_overall = min(all_results, key=lambda x: x["price"])

    print("\n最便宜：")
    print(
        f"{cheapest_overall['date']}  "
        f"€{cheapest_overall['price']}  "
        f"{cheapest_overall['departure']} → "
        f"{cheapest_overall['arrival']}  "
        f"{cheapest_overall['airline']}"
    )
else:
    print("没有取得有效价格。")