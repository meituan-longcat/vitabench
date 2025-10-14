import math
import logging
import holidays
from enum import Enum
from typing import Annotated, Any, Callable, Dict, Optional, TypeVar
from functools import wraps
from datetime import datetime
from pydantic import BaseModel, Field
from thefuzz import process, fuzz

from vita.environment.db import DB
from vita.environment.tool import Tool, as_tool
from vita.utils import get_hash, update_pydantic_model_with_dict, get_now
from vita.utils.utils import rerank, fuzzy_ratio_match, check_time_format
from vita.data_model.tasks import Location

TOOL_ATTR = "__tool__"
TOOL_TYPE_ATTR = "__tool_type__"

T = TypeVar("T", bound=DB)


class ToolKitType(type):
    """Metaclass for ToolKit classes."""

    def __init__(cls, name, bases, attrs):
        func_tools = {}
        
        # Import schema utilities
        from vita.environment.toolkit_schema import get_domain_from_class, generate_tool_docstring
        
        # Import delivery schema to ensure it's available
        try:
            from vita.domains.delivery.tools_schema import TOOL_DESCRIPTIONS
        except ImportError:
            pass
        
        # Import instore schema to ensure it's available
        try:
            from vita.domains.instore.tools_schema import TOOL_DESCRIPTIONS
        except ImportError:
            pass
        
        # Import ota schema to ensure it's available
        try:
            from vita.domains.ota.tools_schema import TOOL_DESCRIPTIONS
        except ImportError:
            pass
        
        # Determine domain for this class
        domain = get_domain_from_class(cls)
        
        for name, method in attrs.items():
            if isinstance(method, property):
                method = method.fget
            if hasattr(method, TOOL_ATTR):
                # Try to enhance the docstring if we have domain information
                if domain:
                    # Use the method name directly since it's the same as the tool name
                    tool_name = name
                    try:
                        # Use current global language setting
                        from vita.utils.schema_utils import get_global_language
                        current_language = get_global_language()
                        enhanced_docstring = generate_tool_docstring(domain, tool_name, current_language)
                        if enhanced_docstring:
                            # Update the method's docstring
                            method.__doc__ = enhanced_docstring
                    except Exception:
                        # If schema lookup fails, keep the original docstring
                        pass
                
                func_tools[name] = method

        @property
        def _func_tools(self) -> Dict[str, Callable]:
            """Get the tools available in the ToolKit."""
            all_func_tools = func_tools.copy()
            try:
                all_func_tools.update(super(cls, self)._func_tools)
            except AttributeError:
                pass

            try:
                for attr_name in object.__getattribute__(self, '__dict__'):
                    if not attr_name.startswith("__"):
                        try:
                            attr = object.__getattribute__(self, attr_name)
                            if callable(attr) and hasattr(attr, TOOL_ATTR) and attr_name not in all_func_tools:
                                # Try to enhance the docstring for dynamically added tools too
                                if domain:
                                    # Use the attribute name directly since it's the same as the tool name
                                    tool_name = attr_name
                                    try:
                                        # Use current global language setting
                                        from vita.utils.schema_utils import get_global_language
                                        current_language = get_global_language()
                                        enhanced_docstring = generate_tool_docstring(domain, tool_name, current_language)
                                        if enhanced_docstring:
                                            attr.__doc__ = enhanced_docstring
                                    except Exception:
                                        pass
                                
                                all_func_tools[attr_name] = attr
                        except AttributeError:
                            continue
            except AttributeError:
                pass

            return all_func_tools

        cls._func_tools = _func_tools


class ToolType(str, Enum):
    """Type of a tool."""

    READ = "read"
    WRITE = "write"
    THINK = "think"
    GENERIC = "generic"


def is_tool(tool_type: ToolType = ToolType.READ, domain: str = None, tool_name: str = None):
    """Decorator to mark a function as a tool.

    Args:
        tool_type: The type of the tool (READ, WRITE, THINK, GENERIC)
        domain: The domain name for schema lookup (optional)
        tool_name: The tool name for schema lookup (optional, defaults to function name)
    """

    def decorator(func):
        # Try to get domain from the class if not provided
        if domain is None:
            # This will be set when the decorator is applied to a method
            # We'll handle it in the metaclass
            pass
        
        # Try to get tool name if not provided
        actual_tool_name = tool_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AssertionError as e:
                return str(e)

        setattr(wrapper, TOOL_ATTR, True)
        setattr(wrapper, TOOL_TYPE_ATTR, tool_type)
        
        # Store additional metadata for schema lookup
        setattr(wrapper, "__tool_domain__", domain)
        setattr(wrapper, "__tool_name__", actual_tool_name)
        
        return wrapper

    return decorator


class ToolKitBase(metaclass=ToolKitType):
    """Base class for ToolKit classes."""

    def __init__(self, db: Optional[T] = None):
        self.db: Optional[T] = db
        self._update_tool_descriptions()

    @property
    def tools(self) -> Dict[str, Callable]:
        """Get the tools available in the ToolKit."""
        return {name: getattr(self, name) for name in self._func_tools.keys()}

    def use_tool(self, tool_name: str, **kwargs) -> str:
        """Use a tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found.")
        return self.tools[tool_name](**kwargs)

    def _update_tool_descriptions(self):
        try:
            from vita.utils.schema_utils import get_global_language, generate_tool_docstring
            from vita.environment.toolkit_schema import get_domain_from_class

            current_language = get_global_language()
            domain = get_domain_from_class(self.__class__)

            toolkit_domain = get_domain_from_class(ToolKitBase)

            if domain:
                for tool_name in self._func_tools.keys():
                    try:
                        enhanced_docstring = generate_tool_docstring(domain, tool_name, current_language)

                        if not enhanced_docstring and toolkit_domain:
                            enhanced_docstring = generate_tool_docstring(toolkit_domain, tool_name, current_language)

                        if enhanced_docstring:
                            tool_func = getattr(self, tool_name)
                            if hasattr(tool_func, '__doc__'):
                                if hasattr(tool_func, '__func__'):
                                    tool_func.__func__.__doc__ = enhanced_docstring
                                else:
                                    tool_func.__doc__ = enhanced_docstring
                    except Exception as e:
                        logging.debug(f"Failed to update docstring for {tool_name}: {e}")
        except Exception as e:
            logging.debug(f"Failed to update tool descriptions: {e}")

    def get_tools(self) -> Dict[str, Tool]:
        """Get the tools available in the ToolKit.
        Uses the `as_tool` to convert the functions to Tool objects.

        Returns:
            A dictionary of tools available in the ToolKit.
        """
        self._update_tool_descriptions()

        logging.debug(f"TOOLKIT: self.tools.items() {self.tools.items()}")
        return {name: as_tool(tool) for name, tool in self.tools.items()}

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool exists in the ToolKit."""
        return tool_name in self.tools

    def tool_type(self, tool_name: str) -> ToolType:
        """Get the type of a tool."""
        tool = self.tools[tool_name]
        return getattr(tool, TOOL_TYPE_ATTR, ToolType.GENERIC)

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the ToolKit."""
        num_tools = len(self.tools)
        num_read_tools = sum(
            self.tool_type(name) == ToolType.READ for name in self.tools
        )
        num_write_tools = sum(
            self.tool_type(name) == ToolType.WRITE for name in self.tools
        )
        num_think_tools = sum(
            self.tool_type(name) == ToolType.THINK for name in self.tools
        )
        num_generic_tools = sum(
            self.tool_type(name) == ToolType.GENERIC for name in self.tools
        )
        return {
            "num_tools": num_tools,
            "num_read_tools": num_read_tools,
            "num_write_tools": num_write_tools,
            "num_think_tools": num_think_tools,
            "num_generic_tools": num_generic_tools,
        }

    def update_db(self, update_data: Optional[dict[str, Any]] = None):
        """Update the database of the ToolKit."""
        if update_data is None:
            update_data = {}
        if self.db is None:
            raise ValueError("Database has not been initialized.")
        self.db = update_pydantic_model_with_dict(self.db, update_data)

    def get_db_hash(self) -> str:
        """Get the hash of the database."""
        return get_hash(self.db.model_dump())

    @is_tool(ToolType.GENERIC)
    def longitude_latitude_to_distance(self, longitude1: float, latitude1: float, longitude2: float,
                                       latitude2: float) -> float:
        if longitude1 == longitude2 and latitude1 == latitude2:
            return 0.0

        R = 6371000
        lon1, lat1, lon2, lat2 = map(math.radians, [longitude1, latitude1, longitude2, latitude2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        return round(distance, 0)

    @is_tool(ToolType.GENERIC)
    def weather(self, address: str, date_start: str, date_end: str) -> str:
        assert check_time_format(date_start,
                                 "%Y-%m-%d"), f"Invalid date_start format. Expected yyyy-mm-dd, got: {date_start}"
        assert check_time_format(date_end, "%Y-%m-%d"), f"Invalid date_end format. Expected yyyy-mm-dd, got: {date_end}"

        weather_dict = {city_weather.city: city_weather for city_weather in self.db.weather}
        weather_dict_for_rerank = {city_weather.city: city_weather.city for city_weather in self.db.weather}
        weather_info = rerank(address, weather_dict_for_rerank, True)[0]
        if weather_info[-1] < 50:
            raise ValueError(f"Weather information not found for {address}")

        filtered_weather = []
        start_date = datetime.strptime(date_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(date_end, "%Y-%m-%d").date()
        for city_weather in self.db.weather:
            if city_weather.city == weather_info[0]:
                weather_date = datetime.strptime(city_weather.datetime, "%Y-%m-%d").date()
                if start_date <= weather_date <= end_date:
                    filtered_weather.append(city_weather)

        if filtered_weather:
            filtered_weather.sort(key=lambda x: x.datetime)
            weather_results = []
            for weather in filtered_weather:
                weather_results.append(repr(weather))
            return "\n".join(weather_results)
        else:
            return f"No weather information found for {weather_info[0]} between {date_start} and {date_end}"

    @is_tool(ToolType.GENERIC)
    def address_to_longitude_latitude(self, address: str) -> tuple[float, float]:
        address_lng_lat_dict = Location.get_all()
        address_lng_lat_dict_for_rerank = {address: address for address in address_lng_lat_dict.keys()}
        address_info = rerank(address, address_lng_lat_dict_for_rerank, True)[0]
        if address_info[-1] < 30 or not fuzzy_ratio_match(address, address_info[0]):
            raise ValueError(f"Longitude and latitude not found for address {address}")
        address_lng_lat = address_lng_lat_dict.get(address_info[0])
        return [address_lng_lat.longitude, address_lng_lat.latitude]

    @is_tool(ToolType.GENERIC)
    def get_date_holiday_info(self, date: str) -> str:
        assert check_time_format(date, "%Y-%m-%d"), f"Date format error, should be yyyy-mm-dd, actual: {date}"
        date_format = datetime.strptime(date, "%Y-%m-%d")
        cn = holidays.China(years=date_format.year)
        holiday_name = cn.get(date_format)
        return holiday_name if holiday_name is not None else f"Date {date} is not a holiday"

    @is_tool(ToolType.GENERIC)
    def get_holiday_date(self, year: str, holiday_name: str) -> str:
        from vita.utils.schema_utils import get_global_language

        # 根据当前语言设置选择节日数据
        current_language = get_global_language()

        if current_language == 'english':
            holiday_data = {
                "2025": {
                    "New Year's Day": "2025-01-01",
                    "Start of Autumn": "2025-08-07",
                    "Women's Day": "2025-03-08",
                    "Laba Festival": "2025-01-07",
                    "Dragon Head Festival": "2025-03-01",
                    "Party Founding Day": "2025-07-01",
                    "Qingming Festival": "2025-04-04",
                    "Double Ninth Festival": "2025-10-29",
                    "Dragon Boat Festival": "2025-05-31",
                    "Mother's Day": "2025-05-11",
                    "Lantern Festival": "2025-02-15",
                    "Labor Day": "2025-05-01",
                    "Qixi Festival": "2025-08-29",
                    "Winter Solstice": "2025-12-21",
                    "Christmas Day": "2025-12-25",
                    "National Day": "2025-10-01",
                    "Mid-Autumn Festival": "2025-10-06"
                },
                "2024": {
                    "Double Ninth Festival": "2024-10-11",
                    "Qixi Festival": "2024-08-10",
                    "Valentine's Day": "2024-02-14",
                    "Qingming Festival": "2024-04-04",
                    "Dragon Boat Festival": "2024-06-10",
                    "Lantern Festival": "2024-02-24",
                    "Mid-Autumn Festival": "2024-09-17",
                },
                "2023": {
                    "National Day": "2023-10-01",
                    "Dragon Boat Festival": "2023-06-22",
                    "Mid-Autumn Festival": "2023-09-29",
                    "Qingming Festival": "2023-04-05",
                    "Double Ninth Festival": "2023-10-23",
                    "Father's Day": "2023-06-18",
                }
            }
        else:
            # 中文版本
            holiday_data = {
            "2025": {
                "元旦节": "2025-01-01",
                "立秋": "2025-08-07",
                "妇女节": "2025-03-08",
                "腊八节": "2025-01-07",
                "龙头节": "2025-03-01",
                "建党节": "2025-07-01",
                "清明节": "2025-04-04",
                "重阳节": "2025-10-29",
                "端午节": "2025-05-31",
                "母亲节": "2025-05-11",
                "元宵节": "2025-02-15",
                "劳动节": "2025-05-01",
                "七夕节": "2025-08-29",
                "冬至": "2025-12-21",
                "圣诞节": "2025-12-25",
                "国庆节": "2025-10-01",
                "中秋节": "2025-10-06"
            },
            "2024": {
                "重阳节": "2024-10-11",
                "七夕节": "2024-08-10",
                "情人节": "2024-02-14",
                "清明节": "2024-04-04",
                "端午节": "2024-06-10",
                "元宵节": "2024-02-24",
                "中秋节": "2024-09-17",
            },
            "2023": {
                "国庆节": "2023-10-01",
                "端午节": "2023-06-22",
                "中秋节": "2023-09-29",
                "清明节": "2023-04-05",
                "重阳节": "2023-10-23",
                "父亲节": "2023-06-18",
            }
        }

        if year not in holiday_data:
            return f"Holiday data for year {year} not found"

        year_holidays = holiday_data[year]
        holiday_names = list(year_holidays.keys())
        matched_holidays = process.extract(holiday_name, holiday_names, limit=None, scorer=fuzz.partial_ratio)
        if matched_holidays and matched_holidays[0][1] >= 80:
            matched_holiday = matched_holidays[0][0]
            return year_holidays[matched_holiday]
        else:
            return f"Holiday named '{holiday_name}' not found in year {year}"

    @is_tool(ToolType.READ)
    def get_user_historical_behaviors(self) -> str:
        return str(self.db.user_historical_behaviors)

    @is_tool(ToolType.READ)
    def get_user_all_orders(self) -> str:
        if self.db.orders is None:
            return "User currently has no order information"
        orders_repr = "\n".join([repr(order) for order in self.db.orders.values()])
        return orders_repr

    @is_tool(ToolType.READ)
    def get_nearby(self, longitude: float, latitude: float, range: float) -> str:
        target_list = []

        if hasattr(self.db, "stores"):
            for store in self.db.stores.values():
                distance = self.longitude_latitude_to_distance(longitude, latitude, store.location.longitude,
                                                               store.location.latitude)
                if distance <= range:
                    target_list.append(str(store))

        if hasattr(self.db, "shops"):
            for shop in self.db.shops.values():
                distance = self.longitude_latitude_to_distance(longitude, latitude, shop.location.longitude,
                                                               shop.location.latitude)
                if distance <= range:
                    target_list.append(str(shop))

        if hasattr(self.db, "hotels"):
            for hotel in self.db.hotels.values():
                distance = self.longitude_latitude_to_distance(longitude, latitude, hotel.location.longitude,
                                                               hotel.location.latitude)
                if distance <= range:
                    target_list.append(str(hotel))

        if hasattr(self.db, "attractions"):
            for attraction in self.db.attractions.values():
                distance = self.longitude_latitude_to_distance(longitude, latitude, attraction.location.longitude,
                                                               attraction.location.latitude)
                if distance <= range:
                    target_list.append(str(attraction))

        if hasattr(self.db, "flights"):
            for flight in self.db.flights.values():
                dep_distance = self.longitude_latitude_to_distance(longitude, latitude,
                                                                   flight.departure_airport_location.longitude,
                                                                   flight.departure_airport_location.latitude)
                if dep_distance <= range:
                    target_list.append(str(flight))
                    continue

                arr_distance = self.longitude_latitude_to_distance(longitude, latitude,
                                                                   flight.arrival_airport_location.longitude,
                                                                   flight.arrival_airport_location.latitude)
                if arr_distance <= range:
                    target_list.append(str(flight))

        if hasattr(self.db, "trains"):
            for train in self.db.trains.values():
                dep_distance = self.longitude_latitude_to_distance(longitude, latitude,
                                                                   train.departure_station_location.longitude,
                                                                   train.departure_station_location.latitude)
                if dep_distance <= range:
                    target_list.append(str(train))
                    continue

                arr_distance = self.longitude_latitude_to_distance(longitude, latitude,
                                                                   train.arrival_station_location.longitude,
                                                                   train.arrival_station_location.latitude)
                if arr_distance <= range:
                    target_list.append(str(train))

        if len(target_list) == 0:
            return "No search results found"
        return "\n".join(target_list)

    def get_now(self, format_str):
        if self.db.time is not None and len(self.db.time) > 0:
            return self.db.time
        return get_now(format_str)


class ToolSignature(BaseModel):
    """A signature of a tool."""

    name: Annotated[str, Field(description="The name of the tool")]
    doc: Annotated[str, Field(description="The documentation of the tool")]
    params: Annotated[
        Optional[dict],
        Field(description="JSON schema of the parameters of the tool", default=None),
    ]
    returns: Annotated[
        Optional[dict],
        Field(description="JSON schema of the return of the tool", default=None),
    ]


def get_tool_signatures(tools: ToolKitBase) -> dict[str, ToolSignature]:
    """Get all the tool signatures from a tool kit.

    Returns:
        A dictionary of tool signatures.
    """
    signatures = {}
    for name, tool in tools.get_tools().items():
        signatures[name] = ToolSignature(
            name=name,
            doc=str(tool),
            params=tool._serialize_params(tool.params),
            returns=tool._serialize_returns(tool.returns),
        )
    return signatures


def get_tool_types(tools: ToolKitBase) -> dict[str, ToolType]:
    """Get the type of a tool.

    Returns:
        A dictionary of tool types.
    """
    return {name: tools.tool_type(name) for name in tools.get_tools().keys()}
