"""Tool schema utilities for the toolkit system.

This file provides utilities for generating tool descriptions and docstrings
that can be used by the is_tool decorator.
"""

from typing import Dict, Any
from vita.utils.schema_utils import (
    generate_tool_docstring, 
    get_domain_from_class,
    create_tool_schema_manager
)

# Tool descriptions for toolkit.py - Chinese version
TOOLKIT_TOOL_DESCRIPTIONS_ZH = {
    "longitude_latitude_to_distance": {
        "description": "根据经纬度计算两点之间的距离（以米为单位）",
        "preconditions": "根据两个点的经纬度计算它们之间的距离",
        "postconditions": "返回两点之间的距离（整数，以米为单位）",
        "args": {
            "longitude1": "第一个点的经度",
            "latitude1": "第一个点的纬度",
            "longitude2": "第二个点的经度",
            "latitude2": "第二个点的纬度"
        },
        "returns": "两点之间的距离（整数，以米为单位）"
    },
    
    "weather": {
        "description": "查询指定地址在date_start到date_end期间的天气信息",
        "preconditions": "查询指定地址在指定日期范围内的天气信息",
        "postconditions": "返回天气信息",
        "args": {
            "address": "要查询的地址",
            "date_start": "开始时间，格式为 yyyy-mm-dd",
            "date_end": "结束时间，格式为 yyyy-mm-dd"
        },
        "returns": "天气信息"
    },
    
    "address_to_longitude_latitude": {
        "description": "根据地址获取经纬度",
        "preconditions": "根据地址获取对应的经纬度坐标",
        "postconditions": "返回经纬度坐标",
        "args": {
            "address": "要查询的地址"
        },
        "returns": "[经度, 纬度]"
    },
    
    "get_date_holiday_info": {
        "description": "判断某日期是否为中国节假日；如果是则返回节假日中文名称",
        "preconditions": "根据日期判断是否为节假日，如果是则返回节假日名称",
        "postconditions": "返回节假日信息",
        "args": {
            "date": "日期，格式为 yyyy-mm-dd"
        },
        "returns": "节假日信息判断结果"
    },
    
    "get_holiday_date": {
        "description": "获取指定年份中某个节假日对应的具体日期",
        "preconditions": "获取指定年份中某个节假日的具体日期",
        "postconditions": "返回节假日的日期",
        "args": {
            "year": "年份",
            "holiday_name": "节假日名称，仅支持中文表述"
        },
        "returns": "节假日的日期"
    },
    
    "get_user_historical_behaviors": {
        "description": "获取用户基本信息和历史行为偏好数据，包括用户ID、家庭住址、工作地址等基本信息，以及各场景的详细消费习惯、偏好品类、价格区间、评分要求、时间偏好等信息，用于个性化推荐和服务优化",
        "preconditions": "获取用户历史行为数据",
        "postconditions": "返回用户历史行为信息",
        "args": {},
        "returns": "用户历史行为信息摘要"
    },
    
    "get_user_all_orders": {
        "description": "获取用户所有订单信息",
        "preconditions": "获取用户的所有订单信息",
        "postconditions": "返回用户所有订单信息",
        "args": {},
        "returns": "用户所有订单信息摘要"
    },
    
    "get_nearby": {
        "description": "获取附近所有商店/商业场所的信息",
        "preconditions": "获取指定范围内（米）的所有商业场所（商店、机场或火车站、酒店、景点、商铺等）的信息",
        "postconditions": "返回商业场所信息",
        "args": {
            "longitude": "经度",
            "latitude": "纬度",
            "range": "范围（以米为单位）"
        },
        "returns": "商店/商业场所信息"
    },
}

# Tool descriptions for toolkit.py - English version
TOOLKIT_TOOL_DESCRIPTIONS_EN = {
    "longitude_latitude_to_distance": {
        "description": "Calculate distance between two points based on longitude and latitude (in meters)",
        "preconditions": "Calculate distance between two points based on their longitude and latitude",
        "postconditions": "Return distance between two points (integer, in meters)",
        "args": {
            "longitude1": "Longitude of first point",
            "latitude1": "Latitude of first point",
            "longitude2": "Longitude of second point",
            "latitude2": "Latitude of second point"
        },
        "returns": "Distance between two points (integer, in meters)"
    },
    
    "weather": {
        "description": "Query weather information for specified address during date_start to date_end period",
        "preconditions": "Query weather information for specified address within specified date range",
        "postconditions": "Return weather information",
        "args": {
            "address": "Address to query",
            "date_start": "Start time, format: yyyy-mm-dd",
            "date_end": "End time, format: yyyy-mm-dd"
        },
        "returns": "Weather information"
    },
    
    "address_to_longitude_latitude": {
        "description": "Get longitude and latitude based on address",
        "preconditions": "Get corresponding longitude and latitude coordinates based on address",
        "postconditions": "Return longitude and latitude coordinates",
        "args": {
            "address": "Address to query"
        },
        "returns": "[Longitude, Latitude]"
    },
    
    "get_date_holiday_info": {
        "description": "Determine if a date is a Chinese holiday; if so, return the Chinese holiday name",
        "preconditions": "Determine if it's a holiday based on date, if so return holiday name",
        "postconditions": "Return holiday information",
        "args": {
            "date": "Date, format: yyyy-mm-dd"
        },
        "returns": "Holiday information determination result"
    },
    
    "get_holiday_date": {
        "description": "Get the specific date corresponding to a holiday in a specified year",
        "preconditions": "Get the specific date of a holiday in a specified year",
        "postconditions": "Return the holiday date",
        "args": {
            "year": "Year",
            "holiday_name": "Holiday name, only supports English expressions"
        },
        "returns": "Holiday date"
    },
    
    "get_user_historical_behaviors": {
        "description": "Get user basic information and historical behavior preference data, including user ID, home address, work address and other basic information, as well as detailed consumption habits, preferred categories, price ranges, rating requirements, time preferences and other information for various scenarios, used for personalized recommendations and service optimization",
        "preconditions": "Get user historical behavior data",
        "postconditions": "Return user historical behavior information",
        "args": {},
        "returns": "User historical behavior information summary"
    },
    
    "get_user_all_orders": {
        "description": "Get all order information for user",
        "preconditions": "Get all order information for user",
        "postconditions": "Return all order information for user",
        "args": {},
        "returns": "Summary of all order information for user"
    },
    
    "get_nearby": {
        "description": "Get information about all nearby stores/commercial establishments",
        "preconditions": "Get information about all commercial establishments (stores, airports or train stations, hotels, attractions, shops, etc.) within specified range (in meters)",
        "postconditions": "Return commercial establishment information",
        "args": {
            "longitude": "Longitude",
            "latitude": "Latitude",
            "range": "Range (in meters)"
        },
        "returns": "Store/commercial establishment information"
    },

}

# Create Toolkit tool schema manager
_schema_manager = create_tool_schema_manager("toolkit", TOOLKIT_TOOL_DESCRIPTIONS_ZH, TOOLKIT_TOOL_DESCRIPTIONS_EN)

# For backward compatibility, provide original function interface
def get_toolkit_tool_descriptions():
    """Get toolkit tool descriptions based on language configuration."""
    return _schema_manager.get_tool_descriptions()

# Backward compatible variable
TOOLKIT_TOOL_DESCRIPTIONS = get_toolkit_tool_descriptions()
