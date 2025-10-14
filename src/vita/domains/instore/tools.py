"""Toolkit for the instore domain."""
from typing import List, Dict, Optional, Union

from vita.domains.instore.data_model import InStoreDB, ShopProduct, BookInfo, ReservationInfo
from vita.data_model.tasks import Order
from vita.environment.toolkit import ToolKitBase, ToolType, is_tool
from vita.utils.utils import check_time_format, rerank


class InStoreTools(ToolKitBase):
    """All the tools for the instore domain."""

    db: InStoreDB

    def __init__(self, db: InStoreDB) -> None:
        super().__init__(db)

    def _check_user(self, user_id: str) -> bool:
        """Check if the user is valid.
        Args:
            user_id: The user id
        Returns:
            bool: True if the user is valid, False otherwise
        """
        if user_id != self.db.user_id:
            return False
        return True

    def _get_shop_tags(self) -> Dict[str, str]:
        """Get the shop tags from the database.
        Returns:
            dict: {shop_id: shop_name + ',' + tags}
        """
        tag_dict = {}
        for shop in self.db.shops.values():
            tag_dict[shop.shop_id] = shop.shop_name + ',' + ','.join(shop.tags)
        return tag_dict

    def _get_shop_product_tags(self) -> Dict[str, str]:
        """Get the product tags from the database.
        Returns:
            dict: {shop_id_product_id: shop_name shop_tags product_name product_tags}
        """
        product_tags = {}
        products = ShopProduct.get_all_products()
        for id, product in products.items():
            if isinstance(product, ShopProduct):
                product_tags[id] = product.name + "," + ",".join(product.tags)

        return product_tags

    def _get_shop(self, shop_id: str):
        if shop_id not in self.db.shops:
            raise ValueError(f"Shop {shop_id} does not exist")
        return self.db.shops[shop_id]

    def _get_shop_product(self, product_id: str):
        product_dict = ShopProduct.get_all_products()
        if product_id not in product_dict:
            raise ValueError(f"Product {product_id} does not exist")
        product = product_dict[product_id]
        if not isinstance(product, ShopProduct):
            raise ValueError(f"Product {product_id} is not an instore scenario product")
        return product

    def _add_book_info(self, book_info: BookInfo) -> str:
        if book_info.book_id in self.db.books:
            return "BookInfo already exists"
        self.db.books[book_info.book_id] = book_info
        return "done"

    def _add_reservation_info(self, reservation_info: ReservationInfo) -> str:
        if reservation_info.reservation_id in self.db.reservations:
            return "ReservationInfo already exists"
        self.db.reservations[reservation_info.reservation_id] = reservation_info
        return "done"

    def _add_instore_order(self, order: Order) -> str:
        if order.order_id in self.db.orders:
            return "Order already exists"
        self.db.orders[order.order_id] = order
        return "done"

    def _get_instore_order(self, order_id: Optional[str] = None) -> Union[Order, List[Order]]:
        """Get the order from the database.

        Args:
            order_id: The order id

        Returns:
            The order.

        Raises:
            ValueError: If the order is not found.
        """
        if order_id is None:
            return [order for order in self.db.orders.values() if order.order_type == "instore"]
        if order_id not in self.db.orders:
            raise ValueError(f"Order {order_id} not found")
        order = self.db.orders[order_id]
        if order.order_type != "instore":
            raise ValueError(f"Order {order_id} is not an instore order")
        return order
    
    def _get_book_info(self, book_id: Optional[str] = None) -> Union[BookInfo, List[BookInfo]]:
        """Get the book info from the database.
        """
        if book_id is None:
            return list(self.db.books.values())
        if book_id not in self.db.books:
            raise ValueError(f"BookInfo {book_id} not found")
        return self.db.books[book_id]
    
    def _get_reservation_info(self, reservation_id: Optional[str] = None) -> Union[ReservationInfo, List[ReservationInfo]]:
        """Get the reservation info from the database.
        """
        if reservation_id is None:
            return list(self.db.reservations.values())
        if reservation_id not in self.db.reservations:
            raise ValueError(f"ReservationInfo {reservation_id} not found")
        return self.db.reservations[reservation_id]
    
    def _modify_instore_order(self, order: Order) -> str:
        """Modify order in domain-specific database.
        
        Args:
            order: The order to modify
            
        Returns:
            "done" if successful, error message otherwise
        """
        if order.order_id not in self.db.orders:
            return f"Order {order.order_id} not found"
        
        self.db.orders[order.order_id] = order
        
        return "done"

    def _modify_reservation_info(self, reservation_info: ReservationInfo) -> str:
        """Modify reservation info in domain-specific database.
        
        Args:
            reservation_info: The reservation info to modify
            
        Returns:
            "done" if successful, error message otherwise
        """
        if reservation_info.reservation_id not in self.db.reservations:
            return f"ReservationInfo {reservation_info.reservation_id} not found"
        
        self.db.reservations[reservation_info.reservation_id] = reservation_info
        
        return "done"

    def _modify_book_info(self, book_info: BookInfo) -> str:
        """Modify book info in domain-specific database.
        
        Args:
            book_info: The book info to modify
            
        Returns:
            "done" if successful, error message otherwise
        """
        if book_info.book_id not in self.db.books:
            return f"BookInfo {book_info.book_id} not found"
        
        self.db.books[book_info.book_id] = book_info
        
        return "done"

    @is_tool(tool_type=ToolType.READ)
    def instore_shop_search_recommend(self, keywords: List[str]) -> str:
        top_k = 1000
        shop_tag_dict = self._get_shop_tags()
        id_candidates_sorted = rerank("".join(keywords), shop_tag_dict)
        selected_ids = [ic[0] for ic in id_candidates_sorted[:top_k]]
        selected_shops = [str(self._get_shop(shop_id)) for shop_id in selected_ids]
        selected_shops_repr = "\n".join(selected_shops)
        return selected_shops_repr

    @is_tool(tool_type=ToolType.READ)
    def instore_product_search_recommend(self, keywords: List[str]) -> str:
        top_k = 1000
        product_tag_dict = self._get_shop_product_tags()
        id_candidates_sorted = rerank("".join(keywords), product_tag_dict)
        selected_ids = [ic[0] for ic in id_candidates_sorted[:top_k]]
        product_list = [self._get_shop_product(product_id) for product_id in selected_ids]
        selected_products_repr = "\n".join([repr(product) for product in product_list])
        return selected_products_repr

    @is_tool(tool_type=ToolType.WRITE)
    def create_instore_product_order(self, user_id: str, shop_id: str, product_id: str, quantity: int = 1) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        assert shop_id in self.db.shops, "Shop does not exist"
        assert product_id in [product.product_id for product in self._get_shop(shop_id).products], "Product does not exist"
        assert quantity > 0, "Quantity must be greater than 0"

        product = self._get_shop_product(product_id)
        product.quantity = quantity
        
        order = Order(
            order_id=self.db.assign_order_id("instore", user_id),
            order_type="instore",
            user_id=user_id,
            store_id=shop_id,
            total_price=quantity * product.price,
            create_time=self.get_now("%Y-%m-%d %H:%M:%S"),
            update_time=self.get_now("%Y-%m-%d %H:%M:%S"),
            status="unpaid",
            products=[product],
        )

        response = self._add_instore_order(order)
        return repr(order) if response == "done" else response


    @is_tool(tool_type=ToolType.WRITE)
    def pay_instore_order(self, order_id: str) -> str:

        assert order_id, "Order ID cannot be empty"

        order = self._get_instore_order(order_id)
        if order.status == "unpaid":
            order.status = "paid"
            order.update_time = self.get_now("%Y-%m-%d %H:%M:%S")
            self._modify_instore_order(order)
        else:
            return f"Order {order_id} is not in `unpaid` status."
        return "Payment successful"
    
    @is_tool(tool_type=ToolType.WRITE)
    def instore_cancel_order(self, order_id: str) -> str:

        assert order_id, "Order ID cannot be empty"

        order = self._get_instore_order(order_id)
        if order.status in ["cancelled"]:
            return f"Order {order.order_id} is already cancelled."
        order.status = "cancelled"
        order.update_time = self.get_now("%Y-%m-%d %H:%M:%S")
        resp = self._modify_instore_order(order)
        if resp == "done":
            return f"Order {order.order_id} is cancelled."
        else:
            return resp

    @is_tool(tool_type=ToolType.WRITE)
    def instore_book(self, user_id: str, shop_id: str, time: str, customer_count: int = 1) -> str:

        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        assert shop_id in self.db.shops, "Shop does not exist"
        assert customer_count > 0, "Number of customers for table booking must be greater than 0"
        assert time, "Table booking time cannot be empty"
        assert check_time_format(time, "%Y-%m-%d %H:%M:%S"), "Table booking time format is incorrect, correct format is %Y-%m-%d %H:%M:%S"

        shop = self.db.shops[shop_id]
        assert shop.enable_book, "Shop does not support table booking"

        book_price = shop.book_price
        status = "unpaid" if book_price > 0 else "paid"
        
        book_info = BookInfo(
            book_id=self.db.assign_order_id("instore_book", user_id),
            shop_id=shop_id,
            book_time=time,
            customer_count=customer_count,
            book_price=book_price,
            customer_id=user_id,
            status=status,
            update_time=self.get_now("%Y-%m-%d %H:%M:%S")
        )
        
        response = self._add_book_info(book_info)
        return repr(book_info) if response == "done" else response

    
    @is_tool(tool_type=ToolType.WRITE)
    def pay_instore_book(self, book_id: str) -> str:

        assert book_id, "Booking ID cannot be empty"

        book_info = self._get_book_info(book_id)
        if book_info.status == "unpaid":
            book_info.status = "paid"
            book_info.update_time = self.get_now("%Y-%m-%d %H:%M:%S")
            resp = self._modify_book_info(book_info)
            if resp == "done":
                return "Payment successful"
            else:
                return resp
        else:
            return f"BookInfo {book_info.book_id} is not in `unpaid` status."
        
    @is_tool(tool_type=ToolType.WRITE)
    def instore_cancel_book(self, book_id: str) -> str:

        assert book_id, "Booking ID cannot be empty"

        book_info = self._get_book_info(book_id)
        if book_info.status in ["cancelled"]:
            return f"BookInfo {book_info.book_id} is already cancelled."
        book_info.status = "cancelled"
        book_info.update_time = self.get_now("%Y-%m-%d %H:%M:%S")
        resp = self._modify_book_info(book_info)
        if resp == "done":
            return f"BookInfo {book_info.book_id} is cancelled."
        else:
            return resp
        
    @is_tool(tool_type=ToolType.WRITE)
    def instore_reservation(self, user_id: str, shop_id: str, time: str, customer_count: int = 1) -> str:

        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        assert shop_id in self.db.shops, "Shop does not exist"

        assert check_time_format(time, "%Y-%m-%d %H:%M:%S"), "Reservation time format is incorrect, correct format is %Y-%m-%d %H:%M:%S"
        assert customer_count > 0, "Number of customers for reservation must be greater than 0"

        reservation = ReservationInfo(
            reservation_id=self.db.assign_order_id("instore_reservation", user_id),
            shop_id=shop_id,
            reservation_time=time,
            customer_id=user_id,
            customer_count=customer_count,
            status="unconsumed",
            update_time=self.get_now("%Y-%m-%d %H:%M:%S")
        )
        
        response = self._add_reservation_info(reservation)
        if response == "done":
            return repr(reservation)
        else:
            return response

    @is_tool(tool_type=ToolType.WRITE)
    def instore_modify_reservation(self, reservation_id: str, time: str,
                                   customer_count: int = 0) -> str:

        assert reservation_id, "Reservation ID cannot be empty"

        reservation_info = self._get_reservation_info(reservation_id)
        if reservation_info.status in ["consumed", "cancelled"]:
            return f"ReservationInfo {reservation_info.reservation_id} is already {reservation_info.status}."

        assert customer_count >= 0, "Number of customers for reservation must be greater than or equal to 0"
        assert time, "Reservation time cannot be empty"
        assert check_time_format(time, "%Y-%m-%d %H:%M:%S"), "Reservation time format is incorrect, correct format is %Y-%m-%d %H:%M:%S"

        reservation_info.reservation_time = time
        reservation_info.customer_count = customer_count
        reservation_info.update_time = self.get_now("%Y-%m-%d %H:%M:%S")
        resp = self._modify_reservation_info(reservation_info)
        if resp == "done":
            return repr(reservation_info)
        else:
            return resp

    @is_tool(tool_type=ToolType.WRITE)
    def instore_cancel_reservation(self, reservation_id: str) -> str:

        assert reservation_id, "Reservation ID cannot be empty"

        reservation_info = self._get_reservation_info(reservation_id)
        if reservation_info.status in ["cancelled"]:
            return f"ReservationInfo {reservation_info.reservation_id} is already cancelled."
        reservation_info.status = "cancelled"
        reservation_info.update_time = self.get_now("%Y-%m-%d %H:%M:%S")
        resp = self._modify_reservation_info(reservation_info)
        if resp == "done":
            return f"ReservationInfo {reservation_info.reservation_id} is cancelled."
        else:
            return resp


    @is_tool(tool_type=ToolType.READ)
    def get_instore_orders(self, user_id: str) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        instore_orders_all = self._get_instore_order()
        
        instore_orders = []
        for order in instore_orders_all:
            if order.user_id == user_id:
                instore_orders.append(order)
        
        if not instore_orders:
            return f"User {user_id} has no order information."
        
        orders_repr = "\n".join([repr(order) for order in instore_orders])
        return orders_repr
    
    @is_tool(tool_type=ToolType.READ)
    def get_instore_reservations(self, user_id: str) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        instore_reservations_all = self._get_reservation_info()
        instore_reservations = []
        for reservation in instore_reservations_all:
            if reservation.customer_id == user_id:
                instore_reservations.append(reservation)
        
        if not instore_reservations:
            return f"User {user_id} has no reservation information."
        reservations_repr = "\n".join([repr(reservation) for reservation in instore_reservations])
        return reservations_repr
    
    @is_tool(tool_type=ToolType.READ)
    def get_instore_books(self, user_id: str) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        instore_books_all = self._get_book_info()
        instore_books = []
        for book in instore_books_all:
            if book.customer_id == user_id:
                instore_books.append(book)
        
        if not instore_books:
            return f"User {user_id} has no book information."
        books_repr = "\n".join([repr(book) for book in instore_books])
        return books_repr
    
    @is_tool(tool_type=ToolType.READ)
    def search_instore_book(self, user_id: str, book_id: Optional[str] = None) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        if book_id is None:
            instore_books_all = self._get_book_info()
            instore_books = []
            for book in instore_books_all:
                if book.customer_id == user_id:
                    instore_books.append(book)
            
            if not instore_books:
                return f"User {user_id} has no book information."
            
            return "\n".join([repr(book) for book in instore_books])
        else:
            book = self._get_book_info(book_id)
            if book.customer_id != user_id:
                return f"BookInfo {book_id} is not belong to user {user_id}."
            return repr(book)

    @is_tool(tool_type=ToolType.READ)
    def search_instore_reservation(self, user_id: str, reservation_id: Optional[str] = None) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        if reservation_id is None:
            user_reservations = []
            for reservation in self.db.reservations.values():
                if reservation.customer_id == user_id:
                    user_reservations.append(reservation)
            
            if not user_reservations:
                return f"User {user_id} has no reservation information."
            
            return "\n".join([repr(reservation) for reservation in user_reservations])
        else:
            reservation = self._get_reservation_info(reservation_id)
            if reservation.customer_id != user_id:
                return f"ReservationInfo {reservation_id} is not belong to user {user_id}."
            return repr(reservation)
