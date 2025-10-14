from typing import Any, Dict, List, Literal
from pydantic import Field


from vita.data_model.tasks import StoreBaseModel, ProductBaseModel, Location
from vita.environment.db import DB


class HotelProduct(ProductBaseModel):
    date: str = Field(description="date")
    room_type: str = Field(description="room type")

    def __repr__(self):
        return (f"HotelProduct(room_type={self.room_type}, "
                f"date={self.date}, "
                f"price={self.price}, "
                f"quantity={self.quantity}, "
                f"product_id={self.product_id})")


class AttractionProduct(ProductBaseModel):
    date: str = Field(description="date")
    ticket_type: str = Field(description="ticket type")

    def __repr__(self):
        return (f"AttractionProduct(ticket_type={self.ticket_type}, "
                f"date={self.date}, "
                f"price={self.price}, "
                f"quantity={self.quantity}, "
                f"product_id={self.product_id})")


class FlightProduct(ProductBaseModel):
    date: str = Field(description="date")
    seat_type: str = Field(description="seat type")

    def __repr__(self):
        return (f"FlightProduct(seat_type={self.seat_type}, "
                f"date={self.date}, "
                f"price={self.price}, "
                f"quantity={self.quantity}, "
                f"product_id={self.product_id})")


class TrainProduct(ProductBaseModel):
    date: str = Field(description="date")
    seat_type: str = Field(description="seat type")

    def __repr__(self):
        return (f"TrainProduct(seat_type={self.seat_type}, "
                f"date={self.date}, "
                f"price={self.price}, "
                f"quantity={self.quantity}, "
                f"product_id={self.product_id})")


class Hotel(StoreBaseModel):
    hotel_id: str = Field(description="hotel Id")
    hotel_name: str = Field(description="hotel name")
    score: float = Field(description="hotel score, a float value between 0-5")
    star_rating: int = Field(description="hotel star score, a int value between 0-5")
    location: Location = Field(description="hotel location (city/area)")
    tags: List[str] = Field(description="hotel tags, e.g. wifi, swimming pool")
    products: List[HotelProduct] = Field(description="hotel room information")

    def __repr__(self):
        products_repr = '\n'.join(map(repr, self.products))
        return (f"Hotel(hotel_id={self.hotel_id}, "
                f"hotel_name={self.hotel_name}, "
                f"score={self.score}, "
                f"star_rating={self.star_rating}, "
                f"location={self.location}, "
                f"tags={self.tags}, "
                f"products={products_repr})")

    def __str__(self):
        return (f"Hotel(hotel_id={self.hotel_id}, "
                f"hotel_name={self.hotel_name}, "
                f"score={self.score}, "
                f"star_rating={self.star_rating}, "
                f"location={self.location}, "
                f"tags={self.tags})")
    
    def model_post_init(self, __context) -> None:
        """Set store_id after model initialization"""
        self.store_id = self.hotel_id


class Attraction(StoreBaseModel):
    attraction_id: str = Field(description="attraction Id")
    attraction_name: str = Field(description="attraction name")
    location: Location = Field(description="attraction location (city/area)")
    description: str = Field(description="attraction description")
    score: float = Field(description="attraction score, a float value between 0-5")
    opening_hours: str = Field(description="attraction opening hours")
    ticket_price: float = Field(description="default ticket price")
    products: List[AttractionProduct] = Field(description="attraction products")

    def __repr__(self):
        products_repr = '\n'.join(map(repr, self.products))
        return (f"Attraction(attraction_id={self.attraction_id}, "
                f"attraction_name={self.attraction_name}, "
                f"location={self.location}, "
                f"description={self.description}, "
                f"score={self.score}, "
                f"opening_hours={self.opening_hours}, "
                f"ticket_price={self.ticket_price}, "
                f"products={products_repr})")

    def __str__(self):
        return (f"Attraction(attraction_id={self.attraction_id}, "
                f"attraction_name={self.attraction_name}, "
                f"location={self.location}, "
                f"description={self.description}, "
                f"score={self.score}, "
                f"opening_hours={self.opening_hours}, ")
    
    def model_post_init(self, __context) -> None:
        """Set store_id after model initialization"""
        self.store_id = self.attraction_id


class Flight(StoreBaseModel):
    flight_id: str = Field(description="flight id")
    flight_number: str = Field(description="flight number")
    departure_city: str = Field(description="departure city")
    arrival_city: str = Field(description="arrival city")
    departure_airport_location: Location = Field(description="departure airport info")
    arrival_airport_location: Location = Field(description="arrival airport info")
    departure_time: str = Field(description="departure time")
    arrival_time: str = Field(description="arrival time")
    tags: List[str] = Field(description="flight tags")
    products: List[FlightProduct] = Field(description="flight products")

    def __repr__(self):
        products_repr = '\n'.join(map(repr, self.products))
        return (f"Flight(flight_id={self.flight_id}, "
                f"flight_number={self.flight_number}, "
                f"departure_city={self.departure_city}, "
                f"arrival_city={self.arrival_city}, "
                f"departure_airport_location={self.departure_airport_location}, "
                f"arrival_airport_location={self.arrival_airport_location}, "
                f"departure_time={self.departure_time}, "
                f"arrival_time={self.arrival_time}, "
                f"tags={self.tags}, "
                f"products={products_repr})")

    def __str__(self):
        return (f"Flight(flight_id={self.flight_id}, "
                f"flight_number={self.flight_number}, "
                f"departure_city={self.departure_city}, "
                f"arrival_city={self.arrival_city}, "
                f"departure_airport_location={self.departure_airport_location}, "
                f"arrival_airport_location={self.arrival_airport_location}, "
                f"departure_time={self.departure_time}, "
                f"arrival_time={self.arrival_time}, "
                f"tags={self.tags})")
    
    def model_post_init(self, __context) -> None:
        """Set store_id after model initialization"""
        self.store_id = self.flight_id


class Train(StoreBaseModel):
    train_id: str = Field(description="train id")
    train_number: str = Field(description="train number")
    departure_city: str = Field(description="departure city")
    arrival_city: str = Field(description="arrival city")
    departure_station_location: Location = Field(description="departure station")
    arrival_station_location: Location = Field(description="arrival station")
    departure_time: str = Field(description="departure time")
    arrival_time: str = Field(description="arrival time")
    tags: List[str] = Field(description="train tags")
    products: List[TrainProduct] = Field(description="train products")

    def __repr__(self):
        products_repr = '\n'.join(map(repr, self.products))
        return (f"Train(train_id={self.train_id}, "
                f"train_number={self.train_number}, "
                f"departure_city={self.departure_city}, "
                f"arrival_city={self.arrival_city}, "
                f"departure_station_location={self.departure_station_location}, "
                f"arrival_station_location={self.arrival_station_location}, "
                f"departure_time={self.departure_time}, "
                f"arrival_time={self.arrival_time}, "
                f"tags={self.tags}, "
                f"products={products_repr})")

    def __str__(self):
        return (f"Train(train_id={self.train_id}, "
                f"train_number={self.train_number}, "
                f"departure_city={self.departure_city}, "
                f"arrival_city={self.arrival_city}, "
                f"departure_station_location={self.departure_station_location}, "
                f"arrival_station_location={self.arrival_station_location}, "
                f"departure_time={self.departure_time}, "
                f"arrival_time={self.arrival_time}, "
                f"tags={self.tags})")
    
    def model_post_init(self, __context) -> None:
        """Set store_id after model initialization"""
        self.store_id = self.train_id


OTAOrderStatus = Literal[
    "unpaid",
    "paid",
    "cancelled",
]


class OTADB(DB):
    """Database containing all OTA-related data including hotels, attractions, flights and trains"""
    hotels: Dict[str, Hotel] = Field(default_factory=dict)
    attractions: Dict[str, Attraction] = Field(default_factory=dict)
    flights: Dict[str, Flight] = Field(default_factory=dict)
    trains: Dict[str, Train] = Field(default_factory=dict)

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the database."""
        num_hotels = len(self.hotels)
        num_attractions = len(self.attractions)
        num_flights = len(self.flights)
        num_trains = len(self.trains)
        return {
            "num_hotels": num_hotels,
            "num_attractions": num_attractions,
            "num_flights": num_flights,
            "num_trains": num_trains,
        }



