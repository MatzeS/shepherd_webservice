
from pathlib import Path

from shepherd_core.data_models import FirmwareDType
from shepherd_core.data_models import GpioTracing
from shepherd_core.data_models.content import EnergyEnvironment
from shepherd_core.data_models.content import Firmware
from shepherd_core.data_models.experiment import Experiment
from shepherd_core.data_models.experiment import TargetConfig
from shepherd_core.data_models.testbed import MCU

import requests

experiment = Experiment(
    id="1337",
    name="matthias-meaningful_TestName",
    # time_start could be "2033-03-13 14:15:16" or "datetime.now() + timedelta(minutes=30)"
    duration=30,
    target_configs=[
        TargetConfig(
            target_IDs=[42],
            custom_IDs=[42],
            energy_env=EnergyEnvironment(name="eenv_static_3000mV_50mA_3600s"),
            firmware1=Firmware(
                name="FW_TestXYZ",
                # data=Path("/home/matthias/dev/app-template/target/thumbv7em-none-eabihf/debug/hello"),
                data=Path("/home/matthias/dev/app-template/hello.elf"),
                data_type=FirmwareDType.path_elf,
                data_local=True,
                mcu=MCU(name="nRF52"),
            ),
            power_tracing=None,
            gpio_tracing=GpioTracing(
                uart_decode=True,  # enables logging uart from userspace
                uart_baudrate=115_200,
            ),
        ),
    ],
)


r = requests.post("http://127.0.0.1:8000/auth/token", data={
    "username": "user@test.com",
    "password": "password",
})
access_token = r.json()["access_token"]


r = requests.post(
    'http://127.0.0.1:8000/experiment',
    data=experiment.model_dump_json(),
    headers={"Authorization": f"Bearer {access_token}"},
)

r = requests.get(
    'http://127.0.0.1:8000/experiment',
    headers={"Authorization": f"Bearer {access_token}"},
)
experiments = r.json()
experiment_id = next(iter(experiments.keys()))

r = requests.post(
    f"http://127.0.0.1:8000/experiment/{experiment_id}/schedule",
    headers={"Authorization": f"Bearer {access_token}"},
)










