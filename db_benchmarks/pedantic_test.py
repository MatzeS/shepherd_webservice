from typing import Dict
from typing import Literal
from typing import Union

from pydantic import BaseModel
from pydantic import StrictInt

sample = {
    0: {0: {"S": "str1", "T": 4, "V": 0x3FF}, 1: {"S": "str2", "T": 5, "V": 0x2FF}},
    1: {
        0: {"S": "str3", "T": 8, "V": 0x1FF},
        1: {"S": "str4", "T": 7, "V": 0x0FF},
        2: {"S": "str4", "T": 7, "V": 0x0FF},
    },
}


# innermost model
class Data(BaseModel):
    S: str
    T: int
    V: int


class Model(BaseModel):
    __root__: Dict[int, Dict[int, Data]]


print(Model.parse_obj(sample))
