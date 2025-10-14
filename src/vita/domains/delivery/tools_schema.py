"""Tool schema definitions for the delivery domain.

This file contains the descriptions and mappings for all tools decorated with @is_tool
in the deliveryTools class.
"""

from typing import Dict, Any
from vita.utils.schema_utils import create_tool_schema_manager

# Tool descriptions extracted from tools.py - Chinese version
TOOL_DESCRIPTIONS_ZH = {
    "delivery_distance_to_time": {
        "description": "根据距离（米）计算外卖配送时间（分钟）",
        "preconditions": "根据从商家到用户地址的距离计算外卖配送时间",
        "postconditions": "返回配送时间（分钟）",
        "args": {
            "distance": "距离（以米为单位）"
        },
        "returns": "时间（以分钟为单位）",
        "tool_type": "GENERIC"
    },

    "get_delivery_store_info": {
        "description": "获取商家信息，包括商家id、评分、地址、经度、纬度、标签、商品列表",
        "preconditions": "处于外卖场景，需要获取商家的详细信息",
        "postconditions": "返回商家的详细信息",
        "args": {
            "store_id": "商家id"
        },
        "returns": "商家的详细信息",
        "tool_type": "READ"
    },

    "get_delivery_product_info": {
        "description": "获取商品信息，包括商品名称、商品id、商店名称、商店id、商品评分、商品价格、商品标签",
        "preconditions": "处于外卖场景，需要获取商品的详细信息",
        "postconditions": "返回商品的详细信息",
        "args": {
            "food_id": "商品id"
        },
        "returns": "商品的详细信息",
        "tool_type": "READ"
    },

    "delivery_store_search_recommand": {
        "description": "在外卖场景下，可以根据用户表达抽取出描述商家的关键词，搜索或推荐多个商家",
        "preconditions": "处于外卖场景，获取描述商家的关键词",
        "postconditions": "返回商家列表，引导用户选择确定商家",
        "args": {
            "keywords": "描述商家的关键词"
        },
        "returns": "结构化输出的商家信息",
        "tool_type": "READ"
    },

    "delivery_product_search_recommand": {
        "description": "在外卖场景下，可以根据用户表达抽取出描述商品的关键词，搜索或推荐多个商品",
        "preconditions": "处于外卖场景，获取描述商品的关键词",
        "postconditions": "返回商品列表，引导用户选择商品并创建订单",
        "args": {
            "keywords": "描述商品的关键词"
        },
        "returns": "结构化输出的商品信息",
        "tool_type": "READ"
    },

    "create_delivery_order": {
        "description": "外卖订单创建，仅支持单个商家下单，单个商家可以下单多个商品",
        "preconditions": "处于外卖场景，确定唯一一个店家id和一个或多个商品id，确定用户的饮食禁忌，并在订单中体现",
        "postconditions": "返回订单信息，询问用户是否支付订单",
        "args": {
            "user_id": "用户id",
            "store_id": "商店id",
            "food_ids": "商品id列表",
            "food_cnts": "商品id对应数量列表",
            "address": "外卖配送目标地址",
            "dispatch_time": "外卖订单开始配送的时间（即骑手从商家取餐出发的时间），格式为yyyy-mm-dd HH:MM:SS",
            "attributes": "商品id对应商品规格属性",
            "note": "订单备注（禁止将用户关于时间等需求直接放在备注中），如饮食禁忌信息说明"
        },
        "returns": "如果创建成功，返回订单信息（包含订单id、用户id、商店id、商品id列表、商品数量列表、地址、下单时间、更新时间、订单状态、商品列表、备注），否则返回相关提示信息",
        "tool_type": "WRITE"
    },

    "pay_delivery_order": {
        "description": "在外卖场景下，上文有订单信息，用户表达确认支付，或者重新支付",
        "preconditions": "处于外卖场景，用户表达确认支付，订单创建完成并进入支付环节｜用户表示重新支付",
        "postconditions": "返回支付结果信息",
        "args": {
            "order_id": "订单id"
        },
        "returns": "支付结果信息",
        "tool_type": "WRITE"
    },

    "get_delivery_order_status": {
        "description": "获取订单状态",
        "preconditions": "查询外卖订单状态",
        "postconditions": "返回订单状态信息",
        "args": {
            "order_id": "订单id"
        },
        "returns": "订单状态信息",
        "tool_type": "READ"
    },

    "cancel_delivery_order": {
        "description": "用户取消订单，或者用户取消支付。禁止对处于已取消状态的订单再次取消。",
        "preconditions": "查询外卖订单状态，确保订单状态为非cancelled",
        "postconditions": "返回取消订单结果信息",
        "args": {
            "order_id": "订单id"
        },
        "returns": "取消订单结果信息",
        "tool_type": "WRITE"
    },

    "modify_delivery_order": {
        "description": "修改订单备注信息",
        "preconditions": "上文确定唯一一个外卖order_id，用户需要修改外卖订单备注",
        "postconditions": "输出修改后订单信息，如果订单还未支付则需要用户确认支付",
        "args": {
            "order_id": "订单id",
            "note": "新的订单备注信息"
        },
        "returns": "修改订单备注操作的结果",
        "tool_type": "WRITE"
    },

    "search_delivery_orders": {
        "description": "查询所有外卖订单，返回包含订单ID、订单类型、用户ID、商家ID、总价、下单时间、更新时间、订单状态等信息",
        "preconditions": "按照查询条件查看所有外卖订单",
        "postconditions": "返回所有符合条件外卖订单的详细信息",
        "args": {
            "user_id": "用户ID",
            "status": "订单状态，默认为未支付"
        },
        "returns": "返回所有符合条件的外卖订单详细信息，包括订单ID、订单类型、用户ID、商家ID、总价、下单时间、更新时间、订单状态等信息",
        "tool_type": "READ"
    },

    "get_delivery_order_detail": {
        "description": "根据订单ID查询外卖订单，返回包含订单ID、订单类型、商家ID、配送时间、配送耗时、送达时间、总价、下单时间、更新时间、订单状态和商品列表等详细信息",
        "preconditions": "上文确定唯一一个外卖order_id",
        "postconditions": "返回指定订单详细信息",
        "args": {
            "order_id": "订单id"
        },
        "returns": "指定订单的详细信息，包括订单ID、订单类型、商家ID、配送时间、配送耗时、送达时间、总价、下单时间、更新时间、订单状态和商品列表",
        "tool_type": "READ"
    }
}

# Tool descriptions extracted from tools.py - English version
TOOL_DESCRIPTIONS_EN = {
    "delivery_distance_to_time": {
        "description": "Calculate delivery time (minutes) based on distance (meters)",
        "preconditions": "Calculate delivery time based on distance from store to user address",
        "postconditions": "Return delivery time (minutes)",
        "args": {
            "distance": "Distance (in meters)"
        },
        "returns": "Time (in minutes)",
        "tool_type": "GENERIC"
    },

    "get_delivery_store_info": {
        "description": "Get store information including store id, rating, address, longitude, latitude, tags, and product list",
        "preconditions": "In delivery scenario, need to get detailed store information",
        "postconditions": "Return detailed store information",
        "args": {
            "store_id": "Store id"
        },
        "returns": "Detailed store information",
        "tool_type": "READ"
    },

    "get_delivery_product_info": {
        "description": "Get food information including food name, food id, store name, store id, food rating, food price, and food tags",
        "preconditions": "In delivery scenario, need to get detailed food information",
        "postconditions": "Return detailed food information",
        "args": {
            "food_id": "Food id"
        },
        "returns": "Detailed food information",
        "tool_type": "READ"
    },

    "delivery_store_search_recommand": {
        "description": "In delivery scenario, can extract keywords describing stores from user expressions, search or recommend multiple stores",
        "preconditions": "In delivery scenario, get keywords describing stores",
        "postconditions": "Return store list, guide user to select and confirm store",
        "args": {
            "keywords": "Keywords describing stores"
        },
        "returns": "Structured store information output",
        "tool_type": "READ"
    },

    "delivery_product_search_recommand": {
        "description": "In delivery scenario, can extract keywords describing food from user expressions, search or recommend multiple food items",
        "preconditions": "In delivery scenario, get keywords describing food",
        "postconditions": "Return food list, guide user to select food and create order",
        "args": {
            "keywords": "Keywords describing food"
        },
        "returns": "Structured food information output",
        "tool_type": "READ"
    },

    "create_delivery_order": {
        "description": "Create delivery order, only supports single store orders, single store can order multiple food items",
        "preconditions": "In delivery scenario, determine unique store id and one or more food ids, determine user dietary restrictions and reflect in order",
        "postconditions": "Return order information, ask user to confirm payment",
        "args": {
            "user_id": "User id",
            "store_id": "Store id",
            "food_ids": "Food id list",
            "food_cnts": "Food id corresponding quantity list",
            "address": "delivery target address",
            "dispatch_time": "delivery order dispatch start time (when rider picks up food from store), format: yyyy-mm-dd HH:MM:SS",
            "attributes": "Food id corresponding food specification attributes",
            "note": "Order notes (prohibited from putting user time requirements directly in notes), such as dietary restriction information"
        },
        "returns": "If creation successful, return order information (including order id, user id, store id, food id list, food quantity list, address, order time, update time, order status, food list, notes), otherwise return related prompt information",
        "tool_type": "WRITE"
    },

    "pay_delivery_order": {
        "description": "In delivery scenario, with order information above, user expresses confirmation of payment or re-payment",
        "preconditions": "In delivery scenario, user expresses confirmation of payment, order creation completed and enters payment phase | user indicates re-payment",
        "postconditions": "Return payment result information",
        "args": {
            "order_id": "Order id"
        },
        "returns": "Payment result information",
        "tool_type": "WRITE"
    },

    "get_delivery_order_status": {
        "description": "Get order status",
        "preconditions": "Query delivery order status",
        "postconditions": "Return order status information",
        "args": {
            "order_id": "Order id"
        },
        "returns": "Order status information",
        "tool_type": "READ"
    },

    "cancel_delivery_order": {
        "description": "User cancels order or user cancels payment. Prohibited from canceling orders that are already in cancelled status.",
        "preconditions": "Query delivery order status, ensure order status is not cancelled",
        "postconditions": "Return order cancellation result information",
        "args": {
            "order_id": "Order id"
        },
        "returns": "Order cancellation result information",
        "tool_type": "WRITE"
    },

    "modify_delivery_order": {
        "description": "Modify order note information",
        "preconditions": "Above text determines unique delivery order_id, user needs to modify delivery order notes",
        "postconditions": "Output modified order information, if order not yet paid user needs to confirm payment",
        "args": {
            "order_id": "Order id",
            "note": "New order note information"
        },
        "returns": "Result of modifying order note operation",
        "tool_type": "WRITE"
    },

    "search_delivery_orders": {
        "description": "Query all delivery orders, return information including order ID, order type, user ID, store ID, total price, order time, update time, order status, etc.",
        "preconditions": "View all delivery orders according to query conditions",
        "postconditions": "Return detailed information of all delivery orders meeting conditions",
        "args": {
            "user_id": "User ID",
            "status": "Order status, default is unpaid"
        },
        "returns": "Return detailed information of all delivery orders meeting conditions, including order ID, order type, user ID, store ID, total price, order time, update time, order status, etc.",
        "tool_type": "READ"
    },

    "get_delivery_order_detail": {
        "description": "Query delivery order by order ID, return detailed information including order ID, order type, store ID, dispatch time, dispatch duration, delivery time, total price, order time, update time, order status and food list",
        "preconditions": "Above text determines unique delivery order_id",
        "postconditions": "Return specified order detailed information",
        "args": {
            "order_id": "Order id"
        },
        "returns": "Specified order detailed information, including order ID, order type, store ID, dispatch time, dispatch duration, delivery time, total price, order time, update time, order status and food list",
        "tool_type": "READ"
    }
}

# Create Delivery tool schema manager
_schema_manager = create_tool_schema_manager("delivery", TOOL_DESCRIPTIONS_ZH, TOOL_DESCRIPTIONS_EN)

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
