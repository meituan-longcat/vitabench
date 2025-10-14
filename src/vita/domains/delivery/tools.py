"""Toolkit for the delivery domain."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union

from vita.domains.delivery.data_model import (
    Store,
    StoreProduct,
    DeliveryDB
)
from vita.data_model.tasks import Order, Location, OrderStatus
from vita.environment.toolkit import ToolKitBase, ToolType, is_tool
from vita.utils.utils import check_time_format, get_now, str_to_datetime, format_time, rerank


class DeliveryTools(ToolKitBase):
    """All the tools for the delivery domain."""

    db: DeliveryDB

    def __init__(self, db: DeliveryDB) -> None:
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

    def _get_store_tags(self) -> Dict[str, str]:
        """Get the store tags from the database.
        Returns:
            dict: {store_id: store_name + ',' + tags, ...}
        """
        tag_dict = {}
        for store in self.db.stores.values():
            tag_dict[store.store_id] = store.name + ','.join(store.tags)
        return tag_dict

    def _get_store_product_tags(self) -> Dict[str, str]:
        """Get the product tags from the database.
        Returns:
            dict: {store_id_product_id: store_name + ',' + product_name + ',' + tags, ...}
        """
        product_tags_dict = {}

        product_dict = StoreProduct.get_all_products()
        for product in product_dict.values():
            if isinstance(product, StoreProduct):
                product_tags_dict[product.product_id] = f"{product.store_name} {product.name} {product.tags}"

        return product_tags_dict

    def _get_delivery_order(self, order_id: Optional[str] = None) -> Union[Order, List[Order]]:
        """Get the order from the database.

        Args:
            order_id: The order id

        Returns:
            Union[Order, List[Order]]: The order if order_id is provided, otherwise a list of all delivery orders.
        """
        if order_id is None:
            return [order for order in self.db.orders.values() if order.order_type == "delivery"]
        if order_id not in self.db.orders:
            raise ValueError(f"Order {order_id} not found")
        order = self.db.orders[order_id]
        if order.order_type != "delivery":
            raise ValueError(f"Order {order_id} is not a delivery order")
        return order

    def _add_delivery_order(self, order: Order) -> str:
        """Add order to the database.
        Args:
            order: The order to add
        Returns:
            "done" if successful, error message otherwise
        """
        if order.order_id in self.db.orders:
            return "Order already exists"
        self.db.orders[order.order_id] = order
        return "done"

    def _modify_delivery_order(self, order: Order) -> str:
        """Modify order in the database.
        
        Args:
            order: The order to modify
            
        Returns:
            "done" if successful, error message otherwise
        """
        if order.order_id not in self.db.orders:
            return "Order not found"

        self.db.orders[order.order_id] = order

        return "done"

    def _get_store(self, store_id: str) -> Store:
        """Get the store from the database.
        Args:
            store_id: The store id.

        Returns:
            Store: The store.
        """
        if store_id not in self.db.stores.keys():
            raise ValueError(f"Store {store_id} not found")
        return self.db.stores[store_id]

    def _get_store_product(self, product_id: str) -> StoreProduct:
        """Get the product from the database.

        Args:
            product_id: The product id.

        Returns:
            StoreProduct: The product.
        """
        product_dict = StoreProduct.get_all_products()
        if product_id not in product_dict:
            raise ValueError(f"{product_id} not found")
        product = product_dict[product_id]

        if not isinstance(product, StoreProduct):
            raise ValueError(f"{product_id} is not a delivery product")
        return product

    @is_tool(ToolType.GENERIC)
    def delivery_distance_to_time(self, distance: float) -> float:
        assert isinstance(distance, float) or isinstance(distance,
                                                         int), f"distance value type should be float or int, but get {type(distance)}"
        return round(25.00 + int(distance) * 0.006510, 0)

    @is_tool(ToolType.READ)
    def get_delivery_store_info(self, store_id: str) -> str:
        resp = self._get_store(store_id)
        return repr(resp)

    @is_tool(ToolType.READ)
    def get_delivery_product_info(self, product_id: str) -> str:
        resp = self._get_store_product(product_id)
        return repr(resp)

    @is_tool(ToolType.READ)
    def delivery_store_search_recommand(self, keywords: List[str]) -> str:
        top_k = 100
        store_tag_dict = self._get_store_tags()
        id_candidates_sorted = rerank("".join(keywords), store_tag_dict)
        selected_ids = [ic[0] for ic in id_candidates_sorted[:top_k]]
        selected_stores = [str(self._get_store(store_id)) for store_id in selected_ids]
        selected_stores_repr = "\n".join(selected_stores)
        return selected_stores_repr

    @is_tool(ToolType.READ)
    def delivery_product_search_recommand(self, keywords: List[str]) -> str:
        top_k = 100
        product_tag_dict = self._get_store_product_tags()
        id_candidates_sorted = rerank("".join(keywords), product_tag_dict)
        selected_ids = [ic[0] for ic in id_candidates_sorted[:top_k]]
        product_list = [self._get_store_product(product_id) for product_id in selected_ids]
        selected_products_repr = "\n".join([repr(product) for product in product_list])
        return selected_products_repr

    @is_tool(ToolType.WRITE)
    def create_delivery_order(
            self,
            user_id: str,
            store_id: str,
            product_ids: List[str],
            product_cnts: List[int],
            address: str,
            dispatch_time: str,
            # create_time: str,
            attributes: Optional[List[str]] = None,
            note: Optional[str] = "",
    ) -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        assert store_id in self.db.stores, f"Store {store_id} not found"
        assert all([self._get_store_product(product_id) is not None for product_id in product_ids]), f"products {product_ids} not found"
        assert address != "", f"Location {address} is empty"
        assert len(product_ids) == len(product_cnts) and all(
            [cnt > 0 for cnt in product_cnts]), f"product_cnts {product_cnts} list is invalid"
        assert dispatch_time and check_time_format(
            dispatch_time), f"dispatch_time {dispatch_time} time format is invalid, yyyy-mm-dd HH:MM:SS required"
        assert str_to_datetime(dispatch_time) >= str_to_datetime(
            self.get_now("%Y-%m-%d %H:%M:%S")), f"dispatch_time {dispatch_time} must be in the future"
        # assert create_time and check_time_format(
        #     create_time), f"create_time {create_time} time format is invalid, yyyy-mm-dd HH:MM:SS required"
        # assert str_to_datetime(create_time) >= str_to_datetime(
        #     self.get_now("%Y-%m-%d %H:%M:%S")), f"create_time {create_time} must be in the future"
        products = [self._get_store_product(product_id) for product_id in product_ids]

        store = self._get_store(store_id)
        longitude, latitude = self.address_to_longitude_latitude(address)
        distance = self.longitude_latitude_to_distance(longitude, latitude, store.location.longitude,
                                                       store.location.latitude)
        shipping_time = self.delivery_distance_to_time(distance)
        delivery_time = format_time(str_to_datetime(dispatch_time) + timedelta(minutes=shipping_time),
                                    "%Y-%m-%d %H:%M:%S")
        total_amount = sum([product.price * cnt for product, cnt in zip(products, product_cnts)])
        attribute_list = [""] * len(products)
        attributes = attributes if attributes is not None else []
        for i, attr in enumerate(attributes[:len(products)]):
            if attr:
                attribute_list[i] = attr
        ordered_products = []
        for product, cnt, attr in zip(products, product_cnts, attribute_list):
            store_product = StoreProduct(
                product_id=product.product_id,
                name=product.name,
                store_id=product.store_id,
                store_name=product.store_name,
                price=product.price,
                quantity=cnt,
                attributes=attr,
                tags=product.tags
            )
            ordered_products.append(store_product)

        order = Order(
            order_id=self.db.assign_order_id("delivery", user_id),
            order_type="delivery",
            user_id=user_id,
            store_id=store_id,
            location=Location(
                address=address,
                longitude=longitude,
                latitude=latitude
            ),
            dispatch_time=dispatch_time,
            shipping_time=shipping_time,
            delivery_time=delivery_time,
            total_price=total_amount,
            create_time=self.get_now("%Y-%m-%d %H:%M:%S"),
            update_time=self.get_now("%Y-%m-%d %H:%M:%S"),
            note=note,
            products=ordered_products,
            status="unpaid"
        )
        response = self._add_delivery_order(order)
        return repr(order) if response == "done" else response

    @is_tool(ToolType.WRITE)
    def pay_delivery_order(self, order_id: str) -> str:
        order = self._get_delivery_order(order_id)
        if order.status == "unpaid":
            order.status = "paid"
            self._modify_delivery_order(order)
        else:
            return "Order is not in `unpaid` status."
        return "Payment successful"

    @is_tool(ToolType.READ)
    def get_delivery_order_status(self, order_id: str) -> str:
        order = self._get_delivery_order(order_id)
        return order.status

    @is_tool(ToolType.WRITE)
    def cancel_delivery_order(self, order_id: str) -> str:
        order = self._get_delivery_order(order_id)
        assert order.status not in ["cancelled"], f"Order {order_id} is already cancelled"
        order.status = "cancelled"
        resp = self._modify_delivery_order(order)
        if resp == "done":
            return f"Order {order.order_id} has been cancelled."
        else:
            return resp

    @is_tool(ToolType.WRITE)
    def modify_delivery_order(self, order_id: str, note: str) -> str:
        order = self._get_delivery_order(order_id)
        order.note = note
        resp = self._modify_delivery_order(order)
        if resp == "done":
            return f"Order {order.order_id} has been modified."
        else:
            return resp

    @is_tool(ToolType.READ)
    def search_delivery_orders(self, user_id: str, status: Optional[OrderStatus] = "unpaid") -> str:
        assert user_id, "User ID cannot be empty"
        assert self._check_user(user_id), "User ID does not match"
        delivery_orders = []
        for order in self._get_delivery_order():
            if order.order_type == "delivery" and order.status == status and order.user_id == user_id:
                delivery_orders.append(order)

        if not delivery_orders:
            return "No delivery orders available"

        orders_repr = "\n".join([str(order) for order in delivery_orders])
        return orders_repr

    @is_tool(ToolType.READ)
    def get_delivery_order_detail(self, order_id: str) -> str:
        assert order_id, "Order ID cannot be empty"
        order = self._get_delivery_order(order_id)
        return repr(order)
