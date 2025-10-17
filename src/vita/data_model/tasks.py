import json
import textwrap
import uuid
from enum import Enum
from typing import Optional, Dict, Union, ClassVar, List, Any, Literal, Tuple

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from vita.data_model.message import Message, ToolCall, ToolRequestor
from vita.data_model.thread_safe_base import ThreadSafeBase


class Action(BaseModel):
    """
    An Agent/User action.
    Example:
      {
      "action_id": "get_user_details_1",
      "requestor": "assistant",
      "name": "get_user_details",
      "arguments": { "user_id": "sophia_silva_7557", "note": "I need to get the user details for user_id: sophia_silva_7557" },
      "compare_args": ["user_id"]
    },
    A tool call can be compared with an action by comparing the arguments in compare_args.
    If compare_args is None, will check all the arguments.
    """

    action_id: str = Field(
        description="The unique identifier for the action within a scenario."
    )
    requestor: ToolRequestor = Field(
        description="The requestor of the action.",
        default="assistant",
    )
    name: str = Field(description="The name of the action.")
    arguments: dict = Field(description="The arguments for the action.")
    info: Optional[str] = Field(
        description="Information about the action.", default=None
    )
    compare_args: Optional[list[str]] = Field(
        description="The arguments to check in tool call. If None, will check all the arguments.",
        default=None,
    )

    def __str__(self) -> str:
        lines = []
        lines.append(f"Action ID: {self.action_id}")
        lines.append(f"Requestor: {self.requestor}")
        lines.append(f"Name: {self.name}")
        lines.append(f"Arguments:\n{json.dumps(self.arguments, indent=2, ensure_ascii=False)}")
        if self.info is not None:
            lines.append(f"Info:\n{textwrap.indent(self.info, '    ')}")
        return "\n".join(lines)

    def get_func_format(self) -> str:
        """
        Get the function format of the action.
        """
        return (
            f"{self.name}({', '.join([f'{k}={v}' for k, v in self.arguments.items()])})"
        )

    def compare_with_tool_call(self, tool_call: ToolCall) -> bool:
        """
        Compare the action with a tool call.
        If the name is not the same, return False.
        If compare_args is None, will check all the arguments.
        Otherwise, will check only the arguments in compare_args.
        """
        if self.name != tool_call.name:
            return False
        if self.compare_args is None:
            compare_args = tool_call.arguments.keys()
        else:
            compare_args = self.compare_args
        if len(compare_args) == 0:
            return True
        tool_args = {k: v for k, v in tool_call.arguments.items() if k in compare_args}
        action_args = {k: v for k, v in self.arguments.items() if k in compare_args}
        return tool_args == action_args


class EnvFunctionCall(BaseModel):
    """
    A function call on the agent or user environment.
    """

    env_type: Annotated[
        ToolRequestor,
        Field(description="The type of environment to call the function on."),
    ]
    func_name: Annotated[str, Field(description="The name of the function to call.")]
    arguments: Annotated[
        dict, Field(description="The arguments to pass to the function.")
    ]

    def __str__(self) -> str:
        lines = []
        lines.append(f"Env Type: {self.env_type}")
        lines.append(f"Func Name: {self.func_name}")
        lines.append(f"Arguments:\n{json.dumps(self.arguments, indent=2, ensure_ascii=False)}")
        return "\n".join(lines)


class EnvAssertion(EnvFunctionCall):
    """
    An assertion on the agent or user environment.
    """

    assert_value: Annotated[
        bool, Field(default=True, description="The value to assert on.")
    ]
    message: Annotated[
        Optional[str],
        Field(
            description="A message to display to the user if the assertion fails.",
            default=None,
        ),
    ]


class RewardType(str, Enum):
    NL_ASSERTION = "NL_ASSERTION"


class UserScenario(BaseModel):
    """
    User scenario. All the information that will be sent to the user simulator.
    """
    user_profile: Annotated[
        Dict[str, Union[Dict, str, List]],
        Field(
            description="Instructions for the User. This information defines the specific situation the user is in and the tasks they are trying to complete."
        ),
    ]

    def __str__(self) -> str:
        lines = []
        lines.append("User Profile:")
        lines.append(textwrap.indent(str(self.user_profile), "\t"))
        lines.append("User Historical Behaviors:")
        return "\n".join(lines)


    @classmethod
    def from_json(cls, json_data):
        if isinstance(json_data, str):
            obj = cls.model_validate_json(json_data)
        else:
            obj = cls.model_validate(json_data)
        return obj


class EvaluationCriteria(BaseModel):
    """
    Evaluation criteria for a particular task. This will be sent to the evaluator.
    """

    expected_states: Annotated[
        Optional[list["ExpectedState"]],
        Field(
            description="Expected states for evaluation, including required and optional orders.",
            default=None,
        ),
    ]

    overall_rubrics: Annotated[
        Optional[List[str]],
        Field(
            description="Overall evaluation rubrics for the task.",
            default=None,
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.expected_states is not None:
            lines.append("Expected States:")
            lines.extend(
                [textwrap.indent(str(state), "\t") for state in self.expected_states]
            )
        if self.overall_rubrics is not None:
            lines.append("Overall Rubrics:")
            lines.extend(
                [textwrap.indent(rubric, "\t") for rubric in self.overall_rubrics]
            )
        return "\n".join(lines)

    def info(self) -> dict:
        num_expected_states = (
            len(self.expected_states) if self.expected_states is not None else 0
        )
        num_overall_rubrics = (
            len(self.overall_rubrics) if self.overall_rubrics is not None else 0
        )
        return {
            "num_expected_states": num_expected_states,
            "num_overall_rubrics": num_overall_rubrics,
        }


class Task(BaseModel):
    """
    A task for a particular domain. This will be sent to the user simulator, the environment and the evaluator.
    """

    id: str = Field(description="The unique identifier for the task.")
    domain: str = Field(description="The domain of the task.")
    environment: dict = Field(description="The environment of the task.")
    user_scenario: Annotated[
        UserScenario,
        Field(
            description="User scenario. This information will be sent to the user simulator."
        ),
    ]
    instructions: Annotated[
        str,
        Field(description="Instructions for the Agent.")
    ]
    evaluation_criteria: Annotated[
        Optional[EvaluationCriteria],
        Field(
            description="Evaluation criteria for the task. This will be sent to the evaluator.",
            default=None,
        ),
    ]
    message_history: Annotated[
        Optional[list[Message]],
        Field(
            default=None,
            description="Messages that have already been exchanged between the user, the agent and the environment. This will be used to set the initial state of the environment and of the orchestrator. Last messages must be from the user or the agent.",
        ),
    ]

    def __str__(self) -> str:
        lines = []
        lines.append(f"ID: {self.id}")
        lines.append("User Scenario:")
        lines.append(textwrap.indent(str(self.user_scenario), "\t"))

        if self.evaluation_criteria is not None:
            lines.append("Evaluation Criteria:")
            lines.append(textwrap.indent(str(self.evaluation_criteria), "\t"))
        return "\n".join(lines)


def make_task_id() -> str:
    """
    Make a task id.
    """
    return str(uuid.uuid4())


def make_task(
        user_instructions: str,
        eval_criteria: EvaluationCriteria,
) -> Task:
    """
    Make a task from a user instruction and an evaluation criteria.
    """

    user_scenario = UserScenario(
        user_profile={"instructions": user_instructions},
        user_historical_behaviors={}
    )
    return Task(
        id=make_task_id(),
        user_scenario=user_scenario,
        evaluation_criteria=eval_criteria,
    )


class Location(BaseModel, ThreadSafeBase["Location"]):
    """Represents a physical address"""

    address: str = Field(description="Primary address line")
    longitude: float = Field(description="longitude")
    latitude: float = Field(description="latitude")

    def __init__(self, **data):
        super().__init__(**data)
        self.register_instance()

    @classmethod
    def from_json(cls, json_data):
        if isinstance(json_data, str):
            obj = cls.model_validate_json(json_data)
        else:
            obj = cls.model_validate(json_data)
        return obj

    def get_instance_key(self) -> str:
        """Get the unique key of the instance"""
        return self.address

    @classmethod
    def get_all(cls):
        return super().get_all()

    def __repr__(self):
        return f"{self.address} longitude:{self.longitude},latitude:{self.latitude}"


OrderStatus = Literal[
    "unpaid",
    "paid",
    "unconsumed",
    "consumed",
    "processed",
    "in-progress",
    "delivered",
    "cancelled",
]

OrderType = Literal["delivery", "instore", "hotel", "attraction", "flight", "train"]


class StoreBaseModel(BaseModel, ThreadSafeBase["StoreBaseModel"]):
    """Represents a store with its variants"""

    store_id: Optional[str] = Field(default="", description="ID of the store")

    def __init__(self, **data):
        super().__init__(**data)
        self.register_instance()
        self.register_polymorphic_instance(StoreBaseModel)

    @classmethod
    def from_json(cls, json_data):
        if isinstance(json_data, str):
            obj = cls.model_validate_json(json_data)
        else:
            obj = cls.model_validate(json_data)
        return obj
 
    def get_instance_key(self) -> str:
        """Get the unique key of the instance"""
        return self.store_id
    
    @classmethod
    def get_all_stores(cls) -> Dict[str, "StoreBaseModel"]:
        """
        Get all store instances (including all subclass instances)
        
        Returns:
            Dict[str, StoreBaseModel]: All store instances
        """
        return cls.get_all_polymorphic()


class ProductBaseModel(BaseModel, ThreadSafeBase["ProductBaseModel"]):
    """Represents a product with its details"""
    product_id: str = Field(default="", description="Unique identifier for the product")
    price: float = Field(default=0.0, description="Price of the product")
    quantity: Optional[int] = Field(default=0, description="Quantity of the product")

    def __init__(self, **data):
        super().__init__(**data)
        self.register_instance()
        self.register_polymorphic_instance(ProductBaseModel)

    @classmethod
    def from_json(cls, json_data):
        if isinstance(json_data, str):
            obj = cls.model_validate_json(json_data)
        else:
            obj = cls.model_validate(json_data)
        return obj
    
    def get_instance_key(self) -> str:
        """Get the unique key of the instance"""
        return self.product_id

    @classmethod
    def get_all_products(cls) -> Dict[str, "ProductBaseModel"]:
        """
        Get all product instances (including all subclass instances)

        Returns:
            Dict[str, ProductBaseModel]: All product instances
        """
        return cls.get_all_polymorphic()


class Order(BaseModel):
    """Represents an order with its items, status, fulfillment and payment details"""

    order_id: str = Field(description="Unique identifier for the order")
    order_type: OrderType = Field(description="Type of the order")
    user_id: str = Field(description="Unique identifier for the user")
    store_id: str = Field(description="Unique identifier for the store")
    note: Optional[str] = Field(default="", description="note of the order")
    location: Optional[Location] = Field(default=None, description="Location of the user")
    dispatch_time: Optional[str] = Field(default="", description="Dispatch time of the order")
    shipping_time: Optional[float] = Field(default=0.0, description="Shipping time of the order")
    delivery_time: Optional[str] = Field(default="", description="Delivery time of the order")
    total_price: float = Field(default=0.0, description="Total price of the order")
    create_time: str = Field(default="", description="Creation time of the order")
    update_time: str = Field(default="", description="Update time of the order")
    status: OrderStatus = Field(default="unpaid", description="Status of the order")
    products: List[Any] = Field(default=[], description="Products in the order")

    id_str: ClassVar[Dict[str, str]] = {
        "delivery": "store_id",
        "instore": "shop_id",
        "hotel": "hotel_id",
        "attraction": "attraction_id",
        "flight": "flight_id",
        "train": "train_id"
    }

    def __init__(self, **data):
        super().__init__(**data)
        if not self.update_time and self.create_time:
            self.update_time = self.create_time

    def __str__(self) -> str:
        return (f"Order(order_id:{self.order_id}, "
                f"order_type:{self.order_type}, "
                f"user_id:{self.user_id}, "
                f"{self.id_str[self.order_type]}:{self.store_id}, "
                f"total_price:{self.total_price}, "
                f"create_time:{self.create_time}, "
                f"update_time:{self.update_time}, "
                f"status:{self.status}, "
                )

    def __repr__(self) -> str:
        if self.order_type == "delivery":
            return (f"Order(order_id:{self.order_id}, "
                    f"order_type:{self.order_type}, "
                    f"user_id:{self.user_id}, "
                    f"{self.id_str[self.order_type]}:{self.store_id}, "
                    f"dispatch_time:{self.dispatch_time}, "
                    f"shipping_time:{self.shipping_time}, " 
                    f"delivery_time:{self.delivery_time}, "
                    f"total_price:{self.total_price}, "
                    f"create_time:{self.create_time}, "
                    f"update_time:{self.update_time}, "
                    f"note:{self.note}, "
                    f"status:{self.status}, "
                    f"products:{self.products})"
                    )
        else:
            return (f"Order(order_id:{self.order_id}, "
                    f"order_type:{self.order_type}, "
                    f"user_id:{self.user_id}, "
                    f"{self.id_str[self.order_type]}:{self.store_id}, "
                    f"total_price:{self.total_price}, "
                    f"create_time:{self.create_time}, "
                    f"update_time:{self.update_time}, "
                    f"status:{self.status}, "
                    f"products:{self.products})"
                    )


class ExpectedState(BaseModel):
    """
    Expected state for evaluation, including required and optional orders.
    """

    required_orders: Annotated[
        Optional[List[Any]],
        Field(
            description="Required order that must be present in the final state.",
            default=None,
        ),
    ]

    optional_orders: Annotated[
        Optional[List[Order]],
        Field(
            description="Optional orders that may be present in the final state.",
            default=None,
        ),
    ]

    state_rubrics: Annotated[
        Optional[List[str]],
        Field(
            description="Evaluation rubrics specific to this state.",
            default=None,
        ),
    ]


class Weather(BaseModel):
    city: str = Field(description="City name")
    category: str = Field(description="Weather category")
    datetime: str = Field(description="Datetime")
    temperature: Tuple[float, float] = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Relative humidity in %")

    def __repr__(self) -> str:
        return (f"city: {self.city}, "
                f"weather: {self.category}, "
                f"datetime: {self.datetime}, "
                f"temperature: {self.temperature[0]}~{self.temperature[1]}, "
                f"humidity: {self.humidity}")