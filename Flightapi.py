from amadeus import Client, ResponseError
import pandas as pd
from datetime import datetime

AMADEUS_CLIENT_ID = "Pg9qgNHHf82iXZ7jw8RybicbzUB1qkqQ"
AMADEUS_CLIENT_SECRET = "XnFIQxT22YAG24XV"

amadeus = Client(client_id=AMADEUS_CLIENT_ID, client_secret=AMADEUS_CLIENT_SECRET)

def format_time(time_str):
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except:
        return time_str

def search_flights_with_booking(origin, destination, departure_date, adults=1, max_results=5):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
            max=max_results,
            currencyCode="USD"
        )
        offers = response.data
        if not offers:
            return None

        flight_data = []
        for offer in offers:
            try:
                priced_offer = amadeus.shopping.flight_offers.pricing.post(offer).data
                booking_link = priced_offer['links'].get('deeplink', 'N/A')
            except:
                booking_link = "N/A"

            price = offer['price']['total']
            airline = offer['validatingAirlineCodes'][0]
            itinerary = offer['itineraries'][0]
            segments = itinerary['segments']
            departure_time = format_time(segments[0]['departure']['at'])
            arrival_time = format_time(segments[-1]['arrival']['at'])
            duration = itinerary['duration']
            stops = len(segments) - 1
            flight_number = f"{segments[0]['carrierCode']}{segments[0]['number']}"

            flight_data.append({
                "Airline": airline,
                "Flight Number": flight_number,
                "Price (USD)": price,
                "Departure": departure_time,
                "Arrival": arrival_time,
                "Duration": duration,
                "Stops": stops,
                "Booking Link": booking_link
            })

        return pd.DataFrame(flight_data)
    except ResponseError as error:
        print("Error:", error)
        return None

def get_flight_status(carrier_code, flight_number, date):
    try:
        response = amadeus.schedule.flights.get(
            carrierCode=carrier_code,
            flightNumber=flight_number,
            scheduledDepartureDate=date
        )
        flights = response.data
        if not flights:
            return "No real-time data available"
        flight_info = flights[0]['flightPoints'][0]['departure']
        return {
            "Terminal": flight_info.get('terminal', 'N/A'),
            "Gate": flight_info.get('gate', 'N/A'),
            "Status": flight_info.get('status', 'Unknown')
        }
    except ResponseError as error:
        return f"Error: {error}"

origin_airport = input("Enter origin airport code (e.g., DEL): ").strip().upper()
destination_airport = input("Enter destination airport code (e.g., DXB): ").strip().upper()
departure_date = input("Enter departure date (YYYY-MM-DD): ").strip()

df = search_flights_with_booking(origin_airport, destination_airport, departure_date, adults=1, max_results=5)

if df is not None and not df.empty:
    print("\n" + "="*50)
    print("           ✈ AVAILABLE FLIGHT OFFERS ✈           ")
    print("="*50)
    print(df.to_string(index=False))

    first_flight = df.iloc[0]
    carrier_code = first_flight["Flight Number"][:2]
    flight_num = first_flight["Flight Number"][2:]
    status = get_flight_status(carrier_code, flight_num, departure_date)

    print("\n" + "="*50)
    print(f"  🛫 REAL-TIME STATUS: {first_flight['Flight Number']}  ")
    print("="*50)
    if isinstance(status, dict):
        for key, value in status.items():
            print(f"{key}: {value}")
    else:
        print(status)
    print("="*50)
else:
    print("\n❌ No results found. Please check airport codes or choose a closer date.")
