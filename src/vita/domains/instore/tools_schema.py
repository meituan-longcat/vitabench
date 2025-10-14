"""Tool schema definitions for the instore domain.

This file contains the descriptions and mappings for all tools decorated with @is_tool
in the InstoreTools class.
"""

from typing import Dict, Any
from vita.utils.schema_utils import create_tool_schema_manager

# Tool descriptions extracted from tools.py - Chinese version
TOOL_DESCRIPTIONS_ZH = {
    "instore_shop_search_recommend": {
        "description": "在到店场景下，用户（需求模糊，没明确表达具体套餐｜没有明确表达具体商家），需要结合用户个人喜好和商家标签等信息，推荐多个商家",
        "preconditions": "处于到店场景，获取商家相关的关键词",
        "postconditions": "返回商家列表，引导用户选择确定商家，商家确定后需要用户选择并确定套餐",
        "args": {
            "keywords": "描述商家的关键词"
        },
        "returns": "结构化输出的商家信息",
        "tool_type": "READ"
    },
    
    "instore_product_search_recommend": {
        "description": "在到店场景下，可以根据用户表达抽取出描述套餐的关键词，搜索或推荐多个套餐",
        "preconditions": "处于到店场景，套餐相关的关键词",
        "postconditions": "返回套餐列表，引导用户选择套餐并创建订单",
        "args": {
            "keywords": "描述套餐的关键词"
        },
        "returns": "结构化输出的套餐信息",
        "tool_type": "READ"
    },
    
    "create_instore_product_order": {
        "description": "到店订单提交",
        "preconditions": "处于到店场景，确定唯一一个店家id和一个或多个商品id",
        "postconditions": "返回订单信息（包含order_id），询问用户是否支付订单",
        "args": {
            "user_id": "用户id",
            "shop_id": "商家id",
            "product_id": "套餐id",
            "quantity": "数量"
        },
        "returns": "订单信息",
        "tool_type": "WRITE"
    },
    
    "pay_instore_order": {
        "description": "在到店场景下，上文有订单信息，用户表达支付完成，或者重新支付完成",
        "preconditions": "处于到店场景，用户表达完成支付操作，订单创建完成并进入支付环节｜用户表示重新支付",
        "postconditions": "返回支付结果信息",
        "args": {
            "order_id": "订单id"
        },
        "returns": "输出支付结果信息",
        "tool_type": "WRITE"
    },
    
    "instore_cancel_order": {
        "description": "用户取消订单，或者用户取消支付。禁止对处于已取消状态的订单再次取消。",
        "preconditions": "处于到店场景，查询订单状态，确保订单状态为非cancelled",
        "postconditions": "返回取消订单结果信息",
        "args": {
            "order_id": "订单id"
        },
        "returns": "输出取消订单结果信息",
        "tool_type": "WRITE"
    },
    
    "instore_book": {
        "description": "座位预定 - 在选定商家后预定物理座位/桌位",
        "preconditions": "处于到店场景，确定唯一一个商家id，商家支持座位预定服务",
        "postconditions": "返回座位预定信息（包含book_id），如需要支付订座费，询问用户是否支付",
        "args": {
            "user_id": "用户id",
            "shop_id": "商家id",
            "time": "座位预定时间 格式: %Y-%m-%d %H:%M:%S",
            "customer_count": "座位预定人数，默认为1人"
        },
        "returns": "座位预定信息",
        "tool_type": "WRITE"
    },
    
    "pay_instore_book": {
        "description": "到店座位预定支付",
        "preconditions": "处于到店场景，确定唯一一个订座id",
        "postconditions": "返回支付结果信息",
        "args": {
            "book_id": "订座id"
        },
        "returns": "支付结果信息",
        "tool_type": "WRITE"
    },
    
    "instore_cancel_book": {
        "description": "到店取消订座",
        "preconditions": "处于到店场景，确定唯一一个订座id",
        "postconditions": "返回取消订座结果信息",
        "args": {
            "book_id": "订座id"
        },
        "returns": "取消订座结果信息",
        "tool_type": "WRITE"
    },
    
    "instore_reservation": {
        "description": "服务预约 - 在选定商家后预约服务时间点",
        "preconditions": "处于到店场景，确定唯一一个商家id，商家支持服务预约",
        "postconditions": "返回服务预约信息（包含reservation_id），通知用户按照约定时间到商家接受服务",
        "args": {
            "user_id": "用户id",
            "shop_id": "商家id",
            "time": "服务预约时间 格式: %Y-%m-%d %H:%M:%S",
            "customer_count": "服务预约人数，默认为1人"
        },
        "returns": "服务预约信息",
        "tool_type": "WRITE"
    },
    
    "instore_modify_reservation": {
        "description": "到店场景对查询到的预约消费信息进行修改",
        "preconditions": "处于到店场景，查询用户待修改预约消费订单，确定唯一一个reservation_id，用户修改预约消费的时间、人数",
        "postconditions": "输出修改后预约消费信息，通知用户按照约定时间到商家消费",
        "args": {
            "reservation_id": "预约消费id",
            "time": "修改后的预约消费时间 正确格式为 %Y-%m-%d %H:%M:%S",
            "customer_count": "修改后的预约消费人数"
        },
        "returns": "修改后的预约信息",
        "tool_type": "WRITE"
    },
    
    "instore_cancel_reservation": {
        "description": "到店预约消费取消",
        "preconditions": "处于到店场景，确定唯一一个预约消费id",
        "postconditions": "返回取消预约消费结果信息",
        "args": {
            "reservation_id": "预约消费id"
        },
        "returns": "取消预约消费结果信息",
        "tool_type": "WRITE"
    },
    
    "get_instore_orders": {
        "description": "获取指定用户所有到店订单",
        "preconditions": "处于到店场景，需要查看所有到店订单",
        "postconditions": "返回所有到店订单的详细信息",
        "args": {
            "user_id": "用户id"
        },
        "returns": "当前用户所有到店订单的详细信息",
        "tool_type": "READ"
    },
    
    "get_instore_reservations": {
        "description": "获取指定用户所有到店预约消费",
        "preconditions": "处于到店场景，需要查看所有到店预约消费",
        "postconditions": "返回所有到店预约消费的详细信息",
        "args": {
            "user_id": "用户id"
        },
        "returns": "当前用户所有到店预约消费的详细信息",
        "tool_type": "READ"
    },
    
    "get_instore_books": {
        "description": "获取指定用户所有到店座位预定",
        "preconditions": "处于到店场景，需要查看所有到店座位预定",
        "postconditions": "返回所有到店座位预定的详细信息",
        "args": {
            "user_id": "用户id"
        },
        "returns": "当前用户所有到店座位预定的详细信息",
        "tool_type": "READ"
    },
    
    "search_instore_book": {
        "description": "查询用户的座位预定信息，当book_id为None时，返回用户所有座位预定，当book_id不为None时，返回指定座位预定",
        "preconditions": "处于到店场景，当book_id为None时，返回用户所有座位预定，当book_id不为None时，返回指定座位预定",
        "postconditions": "返回座位预定信息，方便之后进行修改/取消",
        "args": {
            "user_id": "用户id",
            "book_id": "座位预定id，可选参数，默认为None"
        },
        "returns": "座位预定信息，多个座位预定用换行符分隔",
        "tool_type": "READ"
    },
    
    "search_instore_reservation": {
        "description": "查询用户的预约消费信息",
        "preconditions": "处于到店场景，当reservation_id为None时，返回用户所有预约消费，当reservation_id不为None时，返回指定预约消费",
        "postconditions": "返回预约消费信息，方便之后进行修改/取消",
        "args": {
            "user_id": "用户id",
            "reservation_id": "预约消费id，可选参数，默认为None"
        },
        "returns": "预约消费信息，多个预约用换行符分隔",
        "tool_type": "READ"
    }
}

# Tool descriptions extracted from tools.py - English version
TOOL_DESCRIPTIONS_EN = {
    "instore_shop_search_recommend": {
        "description": "In instore consumption scenario, when user needs are vague (no clear expression of specific packages or specific merchants), need to recommend multiple merchants based on user preferences and merchant tags",
        "preconditions": "In instore consumption scenario, get merchant-related keywords",
        "postconditions": "Return merchant list, guide user to select and confirm merchant, after merchant is confirmed user needs to select and confirm package",
        "args": {
            "keywords": "Keywords describing merchants"
        },
        "returns": "Structured merchant information output",
        "tool_type": "READ"
    },
    
    "instore_product_search_recommend": {
        "description": "In instore scenario, can extract keywords describing packages from user expressions, search or recommend multiple packages",
        "preconditions": "In instore scenario, package-related keywords",
        "postconditions": "Return package list, guide user to select package and create order",
        "args": {
            "keywords": "Keywords describing packages"
        },
        "returns": "Structured package information output",
        "tool_type": "READ"
    },
    
    "create_instore_product_order": {
        "description": "Submit instore order",
        "preconditions": "In instore scenario, determine unique merchant id and one or more product ids",
        "postconditions": "Return order information (including order_id), ask user to confirm payment",
        "args": {
            "user_id": "User id",
            "shop_id": "Merchant id",
            "product_id": "Package id",
            "quantity": "Quantity"
        },
        "returns": "Order information",
        "tool_type": "WRITE"
    },
    
    "pay_instore_order": {
        "description": "In instore scenario, with order information above, user expresses payment completion or re-payment completion",
        "preconditions": "In instore scenario, user expresses completion of payment operation, order creation completed and enters payment phase | user indicates re-payment",
        "postconditions": "Return payment result information",
        "args": {
            "order_id": "Order id"
        },
        "returns": "Payment result information output",
        "tool_type": "WRITE"
    },
    
    "instore_cancel_order": {
        "description": "User cancels order or user cancels payment. Prohibited from canceling orders that are already in cancelled status.",
        "preconditions": "In instore scenario, query order status, ensure order status is not cancelled",
        "postconditions": "Return order cancellation result information",
        "args": {
            "order_id": "Order id"
        },
        "returns": "Order cancellation result information output",
        "tool_type": "WRITE"
    },
    
    "instore_book": {
        "description": "Seat reservation - Reserve physical seats/tables after selecting merchant",
        "preconditions": "In instore scenario, determine unique merchant id, merchant supports seat reservation service",
        "postconditions": "Return seat reservation information (including book_id), if seat reservation fee is required, ask user to confirm payment",
        "args": {
            "user_id": "User id",
            "shop_id": "Merchant id",
            "time": "Seat reservation time format: %Y-%m-%d %H:%M:%S",
            "customer_count": "Seat reservation customer count, default is 1 person"
        },
        "returns": "Seat reservation information",
        "tool_type": "WRITE"
    },
    
    "pay_instore_book": {
        "description": "Instore seat reservation payment",
        "preconditions": "In instore scenario, determine unique seat reservation id",
        "postconditions": "Return payment result information",
        "args": {
            "book_id": "Seat reservation id"
        },
        "returns": "Payment result information",
        "tool_type": "WRITE"
    },
    
    "instore_cancel_book": {
        "description": "Cancel instore seat reservation",
        "preconditions": "In instore scenario, determine unique seat reservation id",
        "postconditions": "Return seat reservation cancellation result information",
        "args": {
            "book_id": "Seat reservation id"
        },
        "returns": "Seat reservation cancellation result information",
        "tool_type": "WRITE"
    },
    
    "instore_reservation": {
        "description": "Service reservation - Reserve service time after selecting merchant",
        "preconditions": "In instore scenario, determine unique merchant id, merchant supports reservation service",
        "postconditions": "Return reservation information (including reservation_id), notify user to arrive at merchant at agreed time to receive service",
        "args": {
            "user_id": "User id",
            "shop_id": "Merchant id",
            "time": "Service reservation time format: %Y-%m-%d %H:%M:%S",
            "customer_count": "Service reservation customer count, default is 1 person"
        },
        "returns": "Service reservation information",
        "tool_type": "WRITE"
    },
    
    "instore_modify_reservation": {
        "description": "Modify instore reservation consumption information",
        "preconditions": "In instore scenario, query user's pending modification reservation consumption orders, determine unique reservation_id, user modifies reservation consumption time and customer count",
        "postconditions": "Output modified reservation consumption information, notify user to arrive at merchant at agreed time for consumption",
        "args": {
            "reservation_id": "Reservation id",
            "time": "New reservation consumption time format: %Y-%m-%d %H:%M:%S",
            "customer_count": "New reservation consumption customer count"
        },
        "returns": "Modified reservation consumption information",
        "tool_type": "WRITE"
    },
    
    "instore_cancel_reservation": {
        "description": "Cancel instore reservation consumption",
        "preconditions": "In instore scenario, determine unique reservation consumption id",
        "postconditions": "Return reservation consumption cancellation result information",
        "args": {
            "reservation_id": "Reservation consumption id"
        },
        "returns": "Reservation consumption cancellation result information",
        "tool_type": "WRITE"
    },
    
    "get_instore_orders": {
        "description": "Get all instore orders for specified user",
        "preconditions": "In instore scenario, need to view all instore orders",
        "postconditions": "Return detailed information of all instore orders",
        "args": {
            "user_id": "User id"
        },
        "returns": "Detailed information of all instore orders for current user",
        "tool_type": "READ"
    },
    
    "get_instore_reservations": {
        "description": "Get all instore reservation consumption for specified user",
        "preconditions": "In instore scenario, need to view all instore reservation consumption",
        "postconditions": "Return detailed information of all instore reservation consumption",
        "args": {
            "user_id": "User id"
        },
        "returns": "Detailed information of all instore reservation consumption for current user",
        "tool_type": "READ"
    },
    
    "get_instore_books": {
        "description": "Get all instore seat reservations for specified user",
        "preconditions": "In instore scenario, need to view all instore seat reservations",
        "postconditions": "Return detailed information of all instore seat reservations",
        "args": {
            "user_id": "User id"
        },
        "returns": "Detailed information of all instore seat reservations for current user",
        "tool_type": "READ"
    },
    
    "search_instore_book": {
        "description": "Query user's seat reservation information, when book_id is None, return all user seat reservations, when book_id is not None, return specified seat reservation",
        "preconditions": "In instore scenario, when book_id is None, return all user seat reservations, when book_id is not None, return specified seat reservation",
        "postconditions": "Return seat reservation information, convenient for later modification/cancellation",
        "args": {
            "user_id": "User id",
            "book_id": "Seat reservation id, optional parameter, default is None"
        },
        "returns": "Seat reservation information, multiple seat reservations separated by newlines",
        "tool_type": "READ"
    },
    
    "search_instore_reservation": {
        "description": "Query user's reservation consumption information",
        "preconditions": "In instore scenario, when reservation_id is None, return all user reservation consumption, when reservation_id is not None, return specified reservation consumption",
        "postconditions": "Return reservation consumption information, convenient for later modification/cancellation",
        "args": {
            "user_id": "User id",
            "reservation_id": "Reservation consumption id, optional parameter, default is None"
        },
        "returns": "Reservation consumption information, multiple reservations separated by newlines",
        "tool_type": "READ"
    }
}

# Create Instore tool schema manager
_schema_manager = create_tool_schema_manager("instore", TOOL_DESCRIPTIONS_ZH, TOOL_DESCRIPTIONS_EN)

# For backward compatibility, provide original function interface
def get_tool_descriptions():
    """Get tool descriptions based on language configuration."""
    return _schema_manager.get_tool_descriptions()

def get_tool_description(tool_name: str) -> Dict[str, Any]:
    """Get the description of a specific tool by name."""
    return _schema_manager.get_tool_description(tool_name)

def get_all_tool_names() -> list:
    """Get a list of all available tool names."""
    return _schema_manager.get_all_tool_names()

def get_tools_by_type(tool_type: str) -> Dict[str, Dict[str, Any]]:
    """Get all tools of a specific type."""
    return _schema_manager.get_tools_by_type(tool_type)

def get_tool_count_by_type() -> Dict[str, int]:
    """Get the count of tools by type."""
    return _schema_manager.get_tool_count_by_type()

def get_tool_args(tool_name: str) -> Dict[str, str]:
    """Get the arguments of a specific tool by name."""
    return _schema_manager.get_tool_args(tool_name)

def get_tool_returns(tool_name: str) -> str:
    """Get the return value description of a specific tool by name."""
    return _schema_manager.get_tool_returns(tool_name)

# Backward compatible variable
TOOL_DESCRIPTIONS = get_tool_descriptions()
TOOL_TYPE_MAPPING = _schema_manager.tool_type_mapping
