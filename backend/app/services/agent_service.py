import requests

BASE_URL = "http://127.0.0.1:8000"


def auto_book_best_seats(match_id: int):

    # 🔹 Get seats
    res = requests.get(f"{BASE_URL}/available-seats/{match_id}")

    if res.status_code != 200:
        return {
            "error": "Failed to fetch seats",
            "details": res.json()
        }

    data = res.json()

    # 🔥 FIX: extract actual list
    if "available_seats" in data:
        seats = data["available_seats"]
    else:
        return {
            "error": "Invalid seat response",
            "response": data
        }

    # 🔹 select seats safely
    selected = seats[:2]

    if not selected:
        return {"error": "No seats available"}

    # 🔹 Initiate booking
    booking_res = requests.post(
        f"{BASE_URL}/payments/initiate-payment",
        json={
            "match_id": match_id,
            "seats": selected
        }
    )

    return {
        "selected_seats": selected,
        "booking_response": booking_res.json()
    }