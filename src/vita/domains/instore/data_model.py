from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field

from vita.data_model.tasks import ProductBaseModel, StoreBaseModel, Location
from vita.environment.db import DB


class ShopProduct(ProductBaseModel):
    """Represents a product with its variants"""
    name: str = Field(description="Name of the product")
    shop_id: str = Field(description="ID of the shop this product belongs to")
    tags: List[str] = Field(description="Tags of the product")

    def __repr__(self):
        return (f"ShopProduct(shop_id={self.shop_id}, "
                f"product_id={self.product_id}, "
                f"name={self.name}, "
                f"price={self.price}, "
                f"quantity={self.quantity}, "
                f"tags={self.tags})")


class Shop(StoreBaseModel):
    """Represents a shop with its variants"""
    shop_id: str = Field(description="Unique identifier for the shop")
    shop_name: str = Field(description="Name of the shop")
    score: float = Field(description="Score of the shop")
    location: Location = Field(description="Location of the shop")
    tags: List[str] = Field(description="Tags of the shop")
    enable_book: bool = Field(description="Whether the shop supports booking")
    book_price: float = Field(description="Booking price")
    enable_reservation: bool = Field(description="Whether the shop supports reservation")
    products: List[ShopProduct] = Field(description="List of products")

    def __repr__(self):
        products_repr = "\n".join(repr(p) for p in self.products)
        return (f"Shop(shop_name={self.shop_name}, "
                f"shop_id={self.shop_id}, "
                f"score={self.score}, "
                f"location={repr(self.location)}, "
                f"tags={self.tags}, "
                f"enable_book={self.enable_book}, "
                f"book_price={self.book_price}, "
                f"enable_reservation={self.enable_reservation}, "
                f"products={products_repr})")

    def __str__(self):
        return (f"Shop(shop_name={self.shop_name}, "
                f"shop_id={self.shop_id}, "
                f"score={self.score}, "
                f"location={repr(self.location)}, "
                f"tags={self.tags}, "
                f"enable_book={self.enable_book}, "
                f"book_price={self.book_price}, "
                f"enable_reservation={self.enable_reservation})")
    
    def model_post_init(self, __context) -> None:
        """Set store_id after model initialization and register all products"""
        self.store_id = self.shop_id
        
        # Ensure all products are registered to global storage
        for product in self.products:
            if not hasattr(product, '_registered') or not product._registered:
                product.register_instance()
                product.register_polymorphic_instance(ProductBaseModel)
                product._registered = True

InstoreOrderStatus = Literal[
    "unpaid",
    "paid",
    "unconsumed",
    "consumed",
    "cancelled",
]


class BookInfo(BaseModel):
    book_id: str = Field(description="Booking ID")
    shop_id: str = Field(description="Shop ID")
    book_time: str = Field(description="Booking time in format %Y-%m-%d %H:%M:%S")
    update_time: str = Field(description="Update time in format %Y-%m-%d %H:%M:%S")
    customer_id: str = Field(description="Customer ID")
    customer_count: int = Field(description="Number of customers")
    book_price: float = Field(description="Booking price")
    status: InstoreOrderStatus = Field(description="Booking status")

    def __repr__(self):
        return f"BookInfo(book_id={self.book_id}," \
               f"shop_id={self.shop_id}, " \
               f"book_time={self.book_time}, " \
               f"customer_id={self.customer_id}, " \
               f"customer_count={self.customer_count}, " \
               f"book_price={self.book_price}, " \
               f"status={self.status}"


class ReservationInfo(BaseModel):
    reservation_id: str = Field(description="Reservation ID")
    shop_id: str = Field(description="Shop ID")
    reservation_time: str = Field(description="Reservation time in format %Y-%m-%d %H:%M:%S")
    update_time: str = Field(description="Update time in format %Y-%m-%d %H:%M:%S")
    customer_id: str = Field(description="Customer ID")
    customer_count: int = Field(description="Number of customers")
    status: InstoreOrderStatus = Field(description="Reservation status")

    def __repr__(self):
        return f"ReservationInfo(reservation_id={self.reservation_id}," \
               f"shop_id={self.shop_id}, " \
               f"reservation_time={self.reservation_time}, " \
               f"customer_id={self.customer_id}, " \
               f"customer_count={self.customer_count}, " \
               f"status={self.status}"


class InStoreDB(DB):
    """Database containing all instore-related data including shops"""

    shops: Dict[str, Shop] = Field(description="Shop information table")
    books: Dict[str, BookInfo] = Field(default={}, description="Booking information table")
    reservations: Dict[str, ReservationInfo] = Field(default={}, description="Reservation information table")

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the database."""
        num_stores = len(self.shops)
        return {
            "num_stores": num_stores,
        }
