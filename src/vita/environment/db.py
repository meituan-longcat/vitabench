from typing import Any, Optional, Dict, List
from datetime import datetime
from pydantic import Field

from vita.data_model.tasks import Weather, Location, Order
from vita.utils import dump_file, get_pydantic_hash, load_file
from vita.utils.pydantic_utils import BaseModelNoExtra
from vita.utils.utils import get_hash


class DB(BaseModelNoExtra):
    """Domain database.

    This is a base class for all domain databases.
    """

    time: Optional[str] = Field(default=None, description="Current Time.")
    user_id: Optional[str] = Field(default=None, description="User ID")
    weather: Optional[List[Weather]] = Field(default=None, description="Weather information")
    location: Optional[List[Location]] = Field(default=None,
                                               description="Address to longitude and latitude information")
    user_historical_behaviors: Optional[Dict[str, Any]] = Field(default={}, description="User historical behaviors")
    orders: Optional[Dict[str, Order]] = Field(default=None, description="Orders in the environment")

    @classmethod
    def load(cls, path: str) -> "DB":
        """Load the database from a structured file like JSON, YAML, or TOML."""
        data = load_file(path)
        env_data = {k: v for k, v in data.get("environment", {}).items() if k in cls.model_fields}
        return cls.model_validate(env_data)

    def dump(self, path: str, exclude_defaults: bool = False, **kwargs: Any) -> None:
        """Dump the database to a file."""
        data = self.model_dump(exclude_defaults=exclude_defaults)
        dump_file(path, data, **kwargs)

    def get_json_schema(self) -> dict[str, Any]:
        """Get the JSON schema of the database."""
        return self.model_json_schema()

    def get_hash(self) -> str:
        """Get the hash of the database."""
        return get_pydantic_hash(self)

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the database."""
        return {}

    def assign_order_id(self, scenario: str, user_id: str, **kwargs) -> str:
        """Unified order ID assignment function
        
        Args:
            scenario: Scenario type ("delivery", "hotel", "attraction", "flight", "train", "instore", "instore_book", "instore_reservation")
            user_id: User ID
            **kwargs: Scenario-specific parameters
            
        Returns:
            Generated order ID
            
        Raises:
            ValueError: If scenario type is not supported
        """
        scenario_configs = {
            "delivery": {
                "prefix": "#DELIVERY#",
                "id_prefix": "OT",
                "params": ["user_id"]
            },
            "hotel": {
                "prefix": "#HOTEL#",
                "id_prefix": "OO",
                "params": ["hotel_id", "product_id", "user_id"]
            },
            "attraction": {
                "prefix": "#ATTRACTION#",
                "id_prefix": "OO",
                "params": ["user_id"]
            },
            "flight": {
                "prefix": "#FLIGHT#",
                "id_prefix": "OO",
                "params": ["user_id"]
            },
            "train": {
                "prefix": "#TRAIN#",
                "id_prefix": "OO",
                "params": ["user_id"]
            },
            "instore": {
                "prefix": "#INSTORE#",
                "id_prefix": "OI",
                "params": []
            },
            "instore_book": {
                "prefix": "#INSTORE_BOOK#",
                "id_prefix": "OI",
                "params": []
            },
            "instore_reservation": {
                "prefix": "#INSTORE_RESV#",
                "id_prefix": "OI",
                "params": []
            }
        }

        if scenario not in scenario_configs:
            raise ValueError(f"Unsupported scenario type: {scenario}")

        config = scenario_configs[scenario]
        prefix = config["prefix"]
        id_prefix = config["id_prefix"]
        params = config["params"]

        hash_input = prefix
        for param in params:
            if param == "user_id":
                hash_input += user_id
            elif param in kwargs:
                hash_input += str(kwargs[param])
            else:
                raise ValueError(f"Missing required parameter: {param}")

        timestamp = datetime.now().timestamp()
        order_id = id_prefix + get_hash(hash_input + str(timestamp))[:10]
        return order_id


def get_db_json_schema(db: Optional[DB] = None) -> dict[str, Any]:
    """Get the JSONschema of the database."""
    if db is None:
        return {}
    return db.get_json_schema()


class MergedDB(DB):
    """Wrapper class for merging multiple databases"""

    def __init__(self):
        super().__init__()
        self._dbs = []
        self._method_cache = {}
        self._domain_fields = {}

    def add_db(self, db):
        """Add a database instance"""
        self._dbs.append(db)
        for attr_name in dir(db):
            if not attr_name.startswith("__") and not attr_name.startswith("_"):
                if attr_name in ['model_extra', 'model_fields', 'model_config', 'model_computed_fields',
                                 'model_fields_set', 'model_private_attributes', 'model_validate']:
                    continue

                attr = getattr(db, attr_name)
                if callable(attr):
                    try:
                        if hasattr(db, attr_name) and callable(getattr(db, attr_name, None)):
                            if not hasattr(self, attr_name):
                                setattr(self, attr_name, self._create_proxy_method(db, attr_name))
                    except (AttributeError, TypeError):
                        pass
                else:
                    if hasattr(self, attr_name):
                        object.__setattr__(self, attr_name, attr)
                    else:
                        self._domain_fields[attr_name] = attr
                        object.__setattr__(self, attr_name, attr)

    def _create_proxy_method(self, db, method_name):
        """Create proxy method that calls original database method"""

        def proxy_method(*args, **kwargs):
            original_method = getattr(db, method_name)
            return original_method(*args, **kwargs)

        return proxy_method

    def __getattr__(self, name):
        """When attribute does not exist, try to find from various databases"""
        if name in self._domain_fields:
            return self._domain_fields[name]

        for db in self._dbs:
            if hasattr(db, name):
                attr = getattr(db, name)
                if callable(attr):
                    return self._create_proxy_method(db, name)
                else:
                    return attr
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def get_hash(self) -> str:
        """Get the hash of the merged database."""
        hash_strings = []
        for db in self._dbs:
            hash_strings.append(db.get_hash())
        return get_hash("|".join(sorted(hash_strings)))

    def model_dump(self, **kwargs):
        """Dump the merged database to a dictionary."""
        merged_data = {}
        for db in self._dbs:
            db_data = db.model_dump(**kwargs)
            merged_data.update(db_data)
        return merged_data

    def get_statistics(self) -> dict[str, Any]:
        """Get the statistics of the merged database."""
        merged_stats = {}
        for db in self._dbs:
            db_stats = db.get_statistics()
            merged_stats.update(db_stats)
        return merged_stats
