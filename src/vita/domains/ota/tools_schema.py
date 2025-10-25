"""Tool schema definitions for the ota domain.

This file contains the descriptions and mappings for all tools decorated with @is_tool
in the OTATools class.
"""

from typing import Dict, Any
from vita.utils.schema_utils import create_tool_schema_manager

# Tool descriptions extracted from tools.py - Chinese version
TOOL_DESCRIPTIONS_ZH = {
    "get_ota_hotel_info": {
        "description": "获取酒店信息，包含酒店id、名称、评分、星级、地址、标签、房间列表",
        "preconditions": "在酒店查询预订场景，需要获取酒店的详细信息",
        "postconditions": "返回酒店的详细信息，引导用户选择房间并下单",
        "args": {
            "hotel_id": "酒店id"
        },
        "returns": "酒店信息",
        "tool_type": "READ"
    },
    
    "get_ota_attraction_info": {
        "description": "获取景点信息，包含景点id、名称、地址、描述、评分、开放时间、门票价格、票种列表",
        "preconditions": "在景点旅游场景，需要获取景点的详细信息",
        "postconditions": "返回景点的详细信息，引导用户选择门票并下单",
        "args": {
            "attraction_id": "景点id"
        },
        "returns": "景点信息",
        "tool_type": "READ"
    },
    
    "get_ota_flight_info": {
        "description": "获取航班信息，包含航班id、航班号、出发城市、到达城市、出发机场位置、到达机场位置、出发时间、到达时间、航班标签、座位类型列表",
        "preconditions": "在机票查询购买场景，需要获取航班的详细信息",
        "postconditions": "返回航班的详细信息，引导用户选择座位并下单",
        "args": {
            "flight_id": "航班id"
        },
        "returns": "航班信息",
        "tool_type": "READ"
    },
    
    "get_ota_train_info": {
        "description": "获取火车信息，包含火车id、车次、出发城市、到达城市、出发车站位置、到达车站位置、出发时间、到达时间、火车标签、座位类型列表",
        "preconditions": "在火车票查询购买场景，需要获取火车的详细信息",
        "postconditions": "返回火车的详细信息，引导用户选择座位并下单",
        "args": {
            "train_id": "火车id"
        },
        "returns": "火车信息",
        "tool_type": "READ"
    },
    
    "hotel_search_recommand": {
        "description": "酒旅场景下，基于用户的地点需求和偏好，推荐合适的酒店选项，提供酒店的基础信息，包含酒店id、名称、评分、星级、地址、标签",
        "preconditions": "用户请求预定酒店，给出了酒店相关的关键词或地点",
        "postconditions": "返回符合条件的酒店列表，如需查看酒店详情（房间列表、价格等）需要使用酒店详情查询工具，引导用户选择酒店",
        "args": {
            "city_name": "城市名称",
            "key_words": "搜索关键词(匹配酒店名称、酒店介绍等)"
        },
        "returns": "结构化输出酒店基础信息",
        "tool_type": "READ"
    },
    
    "attractions_search_recommend": {
        "description": "基于用户的地点需求和偏好，推荐合适的景点选项，提供景点的基础信息，包含景点id、名称、地址、描述、评分、开放时间",
        "preconditions": "用户请求预定景点，给出了景点相关的关键词或地点",
        "postconditions": "返回符合条件的景点列表，如需查看景点详情（门票列表、价格等）需要使用景点详情查询工具，引导用户选择景点",
        "args": {
            "city_name": "城市名称",
            "key_words": "搜索关键词(匹配景点名称、位置、地址、特色等)"
        },
        "returns": "结构化输出景点基础信息",
        "tool_type": "READ"
    },
    
    "flight_search_recommend": {
        "description": "基于用户的地点需求和偏好，推荐合适的航班选项，提供航班的基础信息，包含航班id、航班号、出发城市、到达城市、出发机场位置、到达机场位置、出发时间、到达时间、航班标签",
        "preconditions": "用户请求预定航班，给出了航班相关的关键词或地点",
        "postconditions": "返回符合条件的航班列表，如需查看航班详情（座位类型列表、价格、日期等）需要使用航班详情查询工具，引导用户选择航班",
        "args": {
            "departure": "出发城市",
            "destination": "目的城市"
        },
        "returns": "结构化输出航班基础信息",
        "tool_type": "READ"
    },
    
    "train_ticket_search": {
        "description": "基于用户的地点需求和偏好，推荐合适的火车选项，提供火车票的基础信息，包含火车id、车次、出发城市、到达城市、出发车站位置、到达车站位置、出发时间、到达时间、火车标签",
        "preconditions": "用户请求预定火车，给出了火车相关的关键词或地点",
        "postconditions": "返回符合条件的火车票列表，如需查看火车票详情（座位类型列表、价格、日期等）需要使用火车票详情查询工具，引导用户选择火车票",
        "args": {
            "departure": "出发城市",
            "destination": "目的城市",
            "date": "出发日期"
        },
        "returns": "结构化输出火车基础信息",
        "tool_type": "READ"
    },
    
    "create_hotel_order": {
        "description": "用户预订酒店时，系统根据用户的需求（如酒店名称、入住日期、人数等）生成订单",
        "preconditions": "用户已登录并提供有效的身份标识（user_id），用户提供了有效的酒店名称（hotel_name）和房间类型（room_type），系统有关于目标酒店的信息，并且该酒店在所请求的日期内有房间",
        "postconditions": "生成订单，请用户确认支付",
        "args": {
            "hotel_id": "酒店ID",
            "room_id": "房间ID",
            "user_id": "用户ID"
        },
        "returns": "创建订单操作的反馈输出",
        "tool_type": "WRITE"
    },
    
    "create_attraction_order": {
        "description": "用户根据景点和日期购买门票，系统返回门票的相关信息并进行下单",
        "preconditions": "在景点旅游场景，用户请求预定景点，给出了预定相关必要信息",
        "postconditions": "生成订单，请用户确认支付",
        "args": {
            "attraction_id": "景点ID",
            "ticket_id": "门票ID",
            "user_id": "用户ID",
            "date": "参观日期，格式为 %Y-%m-%d",
            "quantity": "数量"
        },
        "returns": "创建订单操作的反馈输出",
        "tool_type": "WRITE"
    },
    
    "create_flight_order": {
        "description": "用户根据航班号、日期、座位类型、数量购买机票，系统返回机票的相关信息并进行下单",
        "preconditions": "在机票查询购买场景，用户请求预定航班，给出了预定相关必要信息",
        "postconditions": "生成订单，请用户确认支付",
        "args": {
            "flight_id": "航班ID",
            "seat_id": "座位ID",
            "user_id": "用户ID",
            "date": "出发日期",
            "quantity": "数量"
        },
        "returns": "创建订单操作的反馈输出",
        "tool_type": "WRITE"
    },
    
    "create_train_order": {
        "description": "用户根据车次、日期、座位类型、数量购买火车票，系统返回火车票的相关信息并进行下单",
        "preconditions": "在火车票查询购买场景，用户请求预定火车，给出了预定相关必要信息",
        "postconditions": "生成订单，请用户确认支付",
        "args": {
            "train_id": "火车ID",
            "seat_id": "座位ID",
            "user_id": "用户ID",
            "date": "出发日期",
            "quantity": "数量"
        },
        "returns": "创建订单操作的反馈输出",
        "tool_type": "WRITE"
    },
    
    "pay_hotel_order": {
        "description": "用户进行酒店订单支付",
        "preconditions": "在酒店查询预订场景，用户请求支付酒店订单，上文确定了订单ID",
        "postconditions": "确认支付并更新订单状态为已支付",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "支付结果信息",
        "tool_type": "WRITE"
    },
    
    "pay_attraction_order": {
        "description": "用户进行门票订单支付",
        "preconditions": "在景点旅游场景，用户请求支付景点门票订单，上文确定了订单ID",
        "postconditions": "确认支付并更新订单状态为已支付",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "支付结果信息",
        "tool_type": "WRITE"
    },
    
    "pay_flight_order": {
        "description": "用户进行机票订单支付",
        "preconditions": "在机票查询购买场景，用户请求支付航班订单，上文确定了订单ID",
        "postconditions": "确认支付并更新订单状态为已支付",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "支付结果信息",
        "tool_type": "WRITE"
    },
    
    "pay_train_order": {
        "description": "用户进行火车票订单支付",
        "preconditions": "在火车票查询购买场景，用户请求支付火车票订单，上文确定了订单ID",
        "postconditions": "确认支付并更新订单状态为已支付",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "支付结果信息",
        "tool_type": "WRITE"
    },
    
    "search_hotel_order": {
        "description": "根据用户ID，查询用户的酒店订单，返回包含订单ID、订单类型、用户ID、酒店ID、订单总价、下单时间、更新时间和订单状态",
        "preconditions": "用户需求为查询酒店订单",
        "postconditions": "返回订单信息，方便之后进行修改/取消",
        "args": {
            "user_id": "用户ID",
            "date": "日期",
            "status": "订单状态"
        },
        "returns": "指定用户的酒店订单信息",
        "tool_type": "READ"
    },
    
    "search_attraction_order": {
        "description": "根据用户ID，查询用户的景点门票订单，返回包含订单ID、订单类型、用户ID、景点ID、订单总价、下单时间、更新时间和订单状态",
        "preconditions": "用户需求为查询景点门票订单",
        "postconditions": "返回订单信息，方便之后进行修改/取消",
        "args": {
            "user_id": "用户ID",
            "date": "日期",
            "status": "订单状态"
        },
        "returns": "指定用户的景点门票订单信息",
        "tool_type": "READ"
    },
    
    "search_flight_order": {
        "description": "根据用户ID，查询用户的机票订单，返回包含订单ID、订单类型、用户ID、航班ID、订单总价、下单时间、更新时间和订单状态",
        "preconditions": "用户需求为查询机票订单",
        "postconditions": "返回订单信息，方便之后进行修改/取消",
        "args": {
            "user_id": "用户ID",
            "date": "日期",
            "status": "订单状态"
        },
        "returns": "指定用户的机票订单信息",
        "tool_type": "READ"
    },
    
    "search_train_order": {
        "description": "根据用户ID，查询用户的火车票订单，返回包含订单ID、订单类型、用户ID、火车ID、订单总价、下单时间、更新时间和订单状态",
        "preconditions": "用户需求为查询火车票订单",
        "postconditions": "返回订单信息，方便之后进行修改/取消",
        "args": {
            "user_id": "用户ID",
            "date": "日期",
            "status": "订单状态"
        },
        "returns": "指定用户的火车票订单信息",
        "tool_type": "READ"
    },
    
    "get_hotel_order_detail": {
        "description": "获取酒店订单详情，包含订单ID、订单类型、用户ID、酒店ID、订单总价、下单时间、更新时间、订单状态和订单房间详细信息（房间类型、入住日期、价格、房间ID）",
        "preconditions": "用户请求获取酒店订单详情，上文确定了订单ID",
        "postconditions": "返回订单详情",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "订单详情",
        "tool_type": "READ"
    },
    
    "get_attraction_order_detail": {
        "description": "获取景点门票订单详情，包含订单ID、订单类型、用户ID、景点ID、订单总价、下单时间、更新时间、订单状态和订单景点详细信息（门票类型、日期、价格、门票ID）",
        "preconditions": "用户请求获取景点门票订单详情，上文确定了订单ID",
        "postconditions": "返回订单详情",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "订单详情",
        "tool_type": "READ"
    },
    
    "get_flight_order_detail": {
        "description": "获取机票订单详情，包含订单ID、订单类型、用户ID、航班ID、订单总价、下单时间、更新时间、订单状态和订单机票详细信息（座位类型、日期、价格、座位ID）",
        "preconditions": "用户请求获取机票订单详情，上文确定了订单ID",
        "postconditions": "返回订单详情",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "订单详情",
        "tool_type": "READ"
    },
    
    "get_train_order_detail": {
        "description": "获取火车票订单详情，包含订单ID、订单类型、用户ID、火车ID、订单总价、下单时间、更新时间、订单状态和订单火车票详细信息（座位类型、日期、价格、座位ID）",
        "preconditions": "用户请求获取火车票订单详情，上文确定了订单ID",
        "postconditions": "返回订单详情",
        "args": {
            "order_id": "订单ID"
        },
        "returns": "订单详情",
        "tool_type": "READ"
    },
    
    "modify_train_order": {
        "description": "修改火车票订单，支持更改出发日期，自动处理补差价或退差价。",
        "preconditions": "在火车票查询购买场景，用户请求修改火车票订单，上文确定了订单ID",
        "postconditions": "修改订单并更新订单状态，若需补差价，订单状态改为unpaid，否则保持原状态，如需补差价，需引导用户支付当笔订单",
        "args": {
            "order_id": "订单ID",
            "user_id": "用户ID",
            "new_date": "新的出发日期，格式为 %Y-%m-%d"
        },
        "returns": "(修改后的订单内容, 差价，正为需补差价，负为退差价)",
        "tool_type": "WRITE"
    },
    
    "modify_flight_order": {
        "description": "修改机票订单，支持更改出发日期，自动处理补差价或退差价。",
        "preconditions": "在机票查询购买场景，用户请求修改机票订单，上文确定了订单ID",
        "postconditions": "修改订单并更新订单状态，若需补差价，订单状态改为unpaid，否则保持原状态，如需补差价，需引导用户支付当笔订单",
        "args": {
            "order_id": "订单ID",
            "user_id": "用户ID",
            "new_date": "新的出发日期，格式为 %Y-%m-%d"
        },
        "returns": "(修改后的订单内容, 差价，正为需补差价，负为退差价)",
        "tool_type": "WRITE"
    },
    
    "cancel_hotel_order": {
        "description": "用户取消已预订的酒店订单",
        "preconditions": "在酒店查询预订场景，用户请求取消酒店订单，上文确定了订单ID",
        "postconditions": "取消订单并更新订单状态，若需退差价，告知用户即可",
        "args": {
            "order_id": "订单ID",
            "user_id": "用户ID"
        },
        "returns": "取消订单的退款金额",
        "tool_type": "WRITE"
    },
    
    "cancel_attraction_order": {
        "description": "用户取消已预订的景点门票订单",
        "preconditions": "历史对话中有订单id或者已经进行过订单查询，用户有权限取消该订单",
        "postconditions": "如果退差价，告知用户即可",
        "args": {
            "order_id": "订单ID",
            "user_id": "用户ID"
        },
        "returns": "取消订单的退款金额",
        "tool_type": "WRITE"
    },
    
    "cancel_flight_order": {
        "description": "用户取消已预订的机票订单",
        "preconditions": "历史对话中有订单id或者已经进行过订单查询，用户有权限取消该订单",
        "postconditions": "如果退差价，告知用户即可",
        "args": {
            "order_id": "订单ID",
            "user_id": "用户ID"
        },
        "returns": "取消订单的退款金额",
        "tool_type": "WRITE"
    },
    
    "cancel_train_order": {
        "description": "用户取消已预订的火车票订单",
        "preconditions": "历史对话中有订单id或者已经进行过订单查询，用户有权限取消该订单",
        "postconditions": "如果退差价，告知用户即可",
        "args": {
            "order_id": "订单ID",
            "user_id": "用户ID"
        },
        "returns": "取消订单的退款金额",
        "tool_type": "WRITE"
    }
}

# Tool descriptions extracted from tools.py - English version
TOOL_DESCRIPTIONS_EN = {
    "get_ota_hotel_info": {
        "description": "Get hotel information including hotel id, name, rating, star level, address, tags, and room list",
        "preconditions": "In hotel query and booking scenario, need to get detailed hotel information",
        "postconditions": "Return detailed hotel information, guide user to select room and place order",
        "args": {
            "hotel_id": "Hotel id"
        },
        "returns": "Hotel information",
        "tool_type": "READ"
    },
    
    "get_ota_attraction_info": {
        "description": "Get attraction information including attraction id, name, address, description, rating, opening hours, ticket prices, and ticket type list",
        "preconditions": "In attraction travel scenario, need to get detailed attraction information",
        "postconditions": "Return detailed attraction information, guide user to select tickets and place order",
        "args": {
            "attraction_id": "Attraction id"
        },
        "returns": "Attraction information",
        "tool_type": "READ"
    },
    
    "get_ota_flight_info": {
        "description": "Get flight information including flight id, flight number, departure city, arrival city, departure airport location, arrival airport location, departure time, arrival time, flight tags, and seat type list",
        "preconditions": "In flight ticket query and purchase scenario, need to get detailed flight information",
        "postconditions": "Return detailed flight information, guide user to select seats and place order",
        "args": {
            "flight_id": "Flight id"
        },
        "returns": "Flight information",
        "tool_type": "READ"
    },
    
    "get_ota_train_info": {
        "description": "Get train information including train id, train number, departure city, arrival city, departure station location, arrival station location, departure time, arrival time, train tags, and seat type list",
        "preconditions": "In train ticket query and purchase scenario, need to get detailed train information",
        "postconditions": "Return detailed train information, guide user to select seats and place order",
        "args": {
            "train_id": "Train id"
        },
        "returns": "Train information",
        "tool_type": "READ"
    },
    
    "hotel_search_recommand": {
        "description": "In hotel query and booking scenario, recommend suitable hotel options based on user location needs and preferences, provide basic hotel information including hotel id, name, rating, star level, address, and tags",
        "preconditions": "User requests hotel booking, provides hotel-related keywords or location",
        "postconditions": "Return list of hotels meeting criteria, if hotel details (room list, prices, etc.) are needed, use hotel detail query tool, guide user to select hotel",
        "args": {
            "city_name": "City name",
            "key_words": "Search keywords (matching hotel name, hotel introduction, etc.)"
        },
        "returns": "Structured output of basic hotel information",
        "tool_type": "READ"
    },
    
    "attractions_search_recommend": {
        "description": "Recommend suitable attraction options based on user location needs and preferences, provide basic attraction information including attraction id, name, address, description, rating, and opening hours",
        "preconditions": "User requests attraction booking, provides attraction-related keywords or location",
        "postconditions": "Return list of attractions meeting criteria, if attraction details (ticket list, prices, etc.) are needed, use attraction detail query tool, guide user to select attraction",
        "args": {
            "city_name": "City name",
            "key_words": "Search keywords (matching attraction name, location, address, features, etc.)"
        },
        "returns": "Structured output of basic attraction information",
        "tool_type": "READ"
    },
    
    "flight_search_recommend": {
        "description": "Recommend suitable flight options based on user location needs and preferences, provide basic flight information including flight id, flight number, departure city, arrival city, departure airport location, arrival airport location, departure time, arrival time, and flight tags",
        "preconditions": "User requests flight booking, provides flight-related keywords or location",
        "postconditions": "Return list of flights meeting criteria, if flight details (seat type list, prices, dates, etc.) are needed, use flight detail query tool, guide user to select flight",
        "args": {
            "departure": "Departure city",
            "destination": "Destination city"
        },
        "returns": "Structured output of basic flight information",
        "tool_type": "READ"
    },
    
    "train_ticket_search": {
        "description": "Recommend suitable train options based on user location needs and preferences, provide basic train ticket information including train id, train number, departure city, arrival city, departure station location, arrival station location, departure time, arrival time, and train tags",
        "preconditions": "User requests train booking, provides train-related keywords or location",
        "postconditions": "Return list of train tickets meeting criteria, if train ticket details (seat type list, prices, dates, etc.) are needed, use train ticket detail query tool, guide user to select train ticket",
        "args": {
            "departure": "Departure city",
            "destination": "Destination city",
            "date": "Departure date"
        },
        "returns": "Structured output of basic train information",
        "tool_type": "READ"
    },
    
    "create_hotel_order": {
        "description": "When user books hotel, system generates order based on user requirements (such as hotel name, check-in date, number of people, etc.)",
        "preconditions": "User is logged in and provides valid identity (user_id), user provides valid hotel name (hotel_name) and room type (room_type), system has information about target hotel, and hotel has rooms available on requested dates",
        "postconditions": "Generate order, ask user to confirm payment",
        "args": {
            "hotel_id": "Hotel ID",
            "product_id": "Room ID",
            "user_id": "User ID"
        },
        "returns": "Feedback output of creating order operation",
        "tool_type": "WRITE"
    },
    
    "create_attraction_order": {
        "description": "User purchases tickets based on attraction and date, system returns ticket-related information and places order",
        "preconditions": "In attraction travel scenario, user requests to book attraction, provides necessary booking information",
        "postconditions": "Generate order, ask user to confirm payment",
        "args": {
            "attraction_id": "Attraction ID",
            "ticket_id": "Ticket ID",
            "user_id": "User ID",
            "date": "Visit date, format: %Y-%m-%d",
            "quantity": "Quantity"
        },
        "returns": "Feedback output of creating order operation",
        "tool_type": "WRITE"
    },
    
    "create_flight_order": {
        "description": "User purchases flight tickets based on flight and seat type, system returns flight ticket-related information and places order",
        "preconditions": "In flight ticket query and purchase scenario, user requests to book flight, provides necessary booking information",
        "postconditions": "Generate order, ask user to confirm payment",
        "args": {
            "flight_id": "Flight ID",
            "seat_id": "Seat ID",
            "user_id": "User ID",
            "date": "Departure date, format: %Y-%m-%d",
            "quantity": "Quantity"
        },
        "returns": "Feedback output of creating order operation",
        "tool_type": "WRITE"
    },
    
    "create_train_order": {
        "description": "User purchases train tickets based on train and seat type, system returns train ticket-related information and places order",
        "preconditions": "In train ticket query and purchase scenario, user requests to book train, provides necessary booking information",
        "postconditions": "Generate order, ask user to confirm payment",
        "args": {
            "train_id": "Train ID",
            "seat_id": "Seat ID",
            "user_id": "User ID",
            "date": "Departure date, format: %Y-%m-%d",
            "quantity": "Quantity"
        },
        "returns": "Feedback output of creating order operation",
        "tool_type": "WRITE"
    },
    
    "pay_hotel_order": {
        "description": "User pays for hotel order",
        "preconditions": "In hotel query and booking scenario, user requests payment for hotel order, order ID is determined above",
        "postconditions": "Confirm payment and update order status to paid",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Payment result information",
        "tool_type": "WRITE"
    },
    
    "pay_attraction_order": {
        "description": "User pays for attraction ticket order",
        "preconditions": "In attraction travel scenario, user requests payment for attraction ticket order, order ID is determined above",
        "postconditions": "Confirm payment and update order status to paid",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Payment result information",
        "tool_type": "WRITE"
    },
    
    "pay_flight_order": {
        "description": "User pays for flight order",
        "preconditions": "In flight ticket query and purchase scenario, user requests payment for flight order, order ID is determined above",
        "postconditions": "Confirm payment and update order status to paid",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Payment result information",
        "tool_type": "WRITE"
    },
    
    "pay_train_order": {
        "description": "User pays for train ticket order",
        "preconditions": "In train ticket query and purchase scenario, user requests payment for train ticket order, order ID is determined above",
        "postconditions": "Confirm payment and update order status to paid",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Payment result information",
        "tool_type": "WRITE"
    },
    
    "search_hotel_order": {
        "description": "Query user's hotel orders based on user ID, return order ID, order type, user ID, hotel ID, order total price, order time, update time and order status",
        "preconditions": "User needs to query hotel orders",
        "postconditions": "Return order information, convenient for later modification/cancellation",
        "args": {
            "user_id": "User ID",
            "date": "Date",
            "status": "Order status"
        },
        "returns": "Specified user's hotel order information",
        "tool_type": "READ"
    },
    
    "search_attraction_order": {
        "description": "Query user's attraction ticket orders based on user ID, return order ID, order type, user ID, attraction ID, order total price, order time, update time and order status",
        "preconditions": "User needs to query attraction ticket orders",
        "postconditions": "Return order information, convenient for later modification/cancellation",
        "args": {
            "user_id": "User ID",
            "date": "Date",
            "status": "Order status"
        },
        "returns": "Specified user's attraction ticket order information",
        "tool_type": "READ"
    },
    
    "search_flight_order": {
        "description": "Query user's flight orders based on user ID, return order ID, order type, user ID, flight ID, order total price, order time, update time and order status",
        "preconditions": "User needs to query flight orders",
        "postconditions": "Return order information, convenient for later modification/cancellation",
        "args": {
            "user_id": "User ID",
            "date": "Date",
            "status": "Order status"
        },
        "returns": "Specified user's flight order information",
        "tool_type": "READ"
    },
    
    "search_train_order": {
        "description": "Query user's train ticket orders based on user ID, return order ID, order type, user ID, train ID, order total price, order time, update time and order status",
        "preconditions": "User needs to query train ticket orders",
        "postconditions": "Return order information, convenient for later modification/cancellation",
        "args": {
            "user_id": "User ID",
            "date": "Date",
            "status": "Order status"
        },
        "returns": "Specified user's train ticket order information",
        "tool_type": "READ"
    },
    
    "get_hotel_order_detail": {
        "description": "Get hotel order details, including order ID, order type, user ID, hotel ID, order total price, order time, update time, order status and order room detailed information (room type, check-in date, price, room ID)",
        "preconditions": "User requests hotel order details, order ID is determined above",
        "postconditions": "Return order details",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Order details",
        "tool_type": "READ"
    },
    
    "get_attraction_order_detail": {
        "description": "Get attraction ticket order details, including order ID, order type, user ID, attraction ID, order total price, order time, update time, order status and order attraction detailed information (ticket type, date, price, ticket ID)",
        "preconditions": "User requests attraction ticket order details, order ID is determined above",
        "postconditions": "Return order details",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Order details",
        "tool_type": "READ"
    },
    
    "get_flight_order_detail": {
        "description": "Get flight order details, including order ID, order type, user ID, flight ID, order total price, order time, update time, order status and order flight ticket detailed information (seat type, date, price, seat ID)",
        "preconditions": "User requests flight order details, order ID is determined above",
        "postconditions": "Return order details",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Order details",
        "tool_type": "READ"
    },
    
    "get_train_order_detail": {
        "description": "Get train ticket order details, including order ID, order type, user ID, train ID, order total price, order time, update time, order status and order train ticket detailed information (seat type, date, price, seat ID)",
        "preconditions": "User requests train ticket order details, order ID is determined above",
        "postconditions": "Return order details",
        "args": {
            "order_id": "Order ID"
        },
        "returns": "Order details",
        "tool_type": "READ"
    },
    
    "modify_train_order": {
        "description": "Modify train ticket order, support changing departure date, automatically handle price difference compensation or refund",
        "preconditions": "In train ticket query and purchase scenario, user requests to modify train ticket order, order ID is determined above",
        "postconditions": "Modify order and update order status, if price difference compensation is needed, order status changes to unpaid, otherwise maintains original status, if price difference compensation is needed, guide user to pay for current order",
        "args": {
            "order_id": "Order ID",
            "user_id": "User ID",
            "new_date": "New departure date, format: %Y-%m-%d"
        },
        "returns": "(Modified order content, price difference, positive means need to compensate, negative means refund)",
        "tool_type": "WRITE"
    },
    
    "modify_flight_order": {
        "description": "Modify flight order, support changing departure date, automatically handle price difference compensation or refund",
        "preconditions": "In flight ticket query and purchase scenario, user requests to modify flight order, order ID is determined above",
        "postconditions": "Modify order and update order status, if price difference compensation is needed, order status changes to unpaid, otherwise maintains original status, if price difference compensation is needed, guide user to pay for current order",
        "args": {
            "order_id": "Order ID",
            "user_id": "User ID",
            "new_date": "New departure date, format: %Y-%m-%d"
        },
        "returns": "(Modified order content, price difference, positive means need to compensate, negative means refund)",
        "tool_type": "WRITE"
    },
    
    "cancel_hotel_order": {
        "description": "User cancels booked hotel order",
        "preconditions": "In hotel query and booking scenario, user requests to cancel hotel order, order ID is determined above",
        "postconditions": "Cancel order and update order status, if refund is needed, inform user",
        "args": {
            "order_id": "Order ID",
            "user_id": "User ID"
        },
        "returns": "Order cancellation refund amount",
        "tool_type": "WRITE"
    },
    
    "cancel_attraction_order": {
        "description": "User cancels booked attraction ticket order",
        "preconditions": "Order ID exists in conversation history or order query has been performed, user has permission to cancel this order",
        "postconditions": "If refund is needed, inform user",
        "args": {
            "order_id": "Order ID",
            "user_id": "User ID"
        },
        "returns": "Order cancellation refund amount",
        "tool_type": "WRITE"
    },
    
    "cancel_flight_order": {
        "description": "User cancels booked flight order",
        "preconditions": "Order ID exists in conversation history or order query has been performed, user has permission to cancel this order",
        "postconditions": "If refund is needed, inform user",
        "args": {
            "order_id": "Order ID",
            "user_id": "User ID"
        },
        "returns": "Order cancellation refund amount",
        "tool_type": "WRITE"
    },
    
    "cancel_train_order": {
        "description": "User cancels booked train ticket order",
        "preconditions": "Order ID exists in conversation history or order query has been performed, user has permission to cancel this order",
        "postconditions": "If refund is needed, inform user",
        "args": {
            "order_id": "Order ID",
            "user_id": "User ID"
        },
        "returns": "Order cancellation refund amount",
        "tool_type": "WRITE"
    }
}

# Create OTA tool schema manager
_schema_manager = create_tool_schema_manager("ota", TOOL_DESCRIPTIONS_ZH, TOOL_DESCRIPTIONS_EN)

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
