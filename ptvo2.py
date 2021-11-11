"""Device handler for PTVO."""
from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zhaquirks import Bus, LocalDataCluster
from zigpy.zcl.clusters.homeautomation import Diagnostic
from zigpy.zcl.clusters.general import Basic, BinaryInput, Identify, AnalogInput, PowerConfiguration, OnOff, AnalogValue, AnalogInput, AnalogOutput
from zigpy.zcl.clusters.measurement import RelativeHumidity, TemperatureMeasurement, PressureMeasurement

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)

PTVO_DEVICE = 0xfffe
TEMPERATURE_REPORTED_1 = "temperature_reported_1"
TEMPERATURE_REPORTED_3 = "temperature_reported_3"
HUMIDITY_REPORTED = "humidity_reported"
PRESSURE_REPORTED = "pressure_reported"

class PtvoAnalogInputCluster(CustomCluster, AnalogInput):
    """Analog input cluster, used to relay temperature and humidity to Ptvo cluster."""

    cluster_id = AnalogInput.cluster_id


    def __init__(self, *args, **kwargs):
        """Init."""
        self._current_state = {}
        self._current_value = 0
        super().__init__(*args, **kwargs)

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if value is not None:
#            print('--------')
#            print(self._endpoint._endpoint_id)
#            print(attrid)
#            print(value)
            if attrid == 85:
                self._current_value = value * 100 # + self._endpoint._endpoint_id * 100000
                if (self._endpoint._endpoint_id == 4):
                    a_value = self._current_value
                    self.endpoint.device.counter_bus.listener_event("value_reported", a_value)

            if attrid == 28:
                if value.startswith("%"):
                    h_value = self._current_value
                    self.endpoint.device.humidity_bus.listener_event(HUMIDITY_REPORTED, h_value)

                if value.startswith("C"):
                    t_value = self._current_value
                    if self._endpoint._endpoint_id == 1:
                        self.endpoint.device.temperature_bus.listener_event("temperature_reported_1", t_value)
                    if self._endpoint._endpoint_id == 3:
                        self.endpoint.device.temperature_bus.listener_event("temperature_reported_3", t_value)

                if value.startswith("Pa"):
                    p_value = self._current_value / 10000.0
                    self.endpoint.device.pressure_bus.listener_event(PRESSURE_REPORTED, p_value)


class HumidityMeasurementCluster(LocalDataCluster, RelativeHumidity):
    """Humidity measurement cluster to receive reports that are sent to the analog cluster."""

    cluster_id = RelativeHumidity.cluster_id
    MEASURED_VALUE_ID = 0x0000

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.humidity_bus.add_listener(self)

    def humidity_reported(self, value):
        """Humidity reported."""
        self._update_attribute(self.MEASURED_VALUE_ID, value)


class TemperatureMeasurementCluster(LocalDataCluster, TemperatureMeasurement):
    """Temperature measurement cluster to receive reports that are sent to the analog cluster."""

    cluster_id = TemperatureMeasurement.cluster_id
    MEASURED_VALUE_ID = 0x0000

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.temperature_bus.add_listener(self)

    def temperature_reported_1(self, value):
        """Temperature reported."""
#        print('endpoint')
#        print(self._endpoint._endpoint_id)
        if self._endpoint._endpoint_id == 1:
#            print('updating 1')
            self._update_attribute(self.MEASURED_VALUE_ID, value)

    def temperature_reported_3(self, value):
        """Temperature reported."""
#        print('endpoint')
#        print(self._endpoint._endpoint_id)
        if self._endpoint._endpoint_id == 3:
#            print('updating 3')
            self._update_attribute(self.MEASURED_VALUE_ID, value)

class PressureMeasurementCluster(LocalDataCluster, PressureMeasurement):
    """Temperature measurement cluster to receive reports that are sent to the analog cluster."""

    cluster_id = PressureMeasurement.cluster_id
    MEASURED_VALUE_ID = 0x0000

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.pressure_bus.add_listener(self)

    def pressure_reported(self, value):
        """Pressure reported."""
        self._update_attribute(self.MEASURED_VALUE_ID, value)

class AnalogValueMeasurementCluster(LocalDataCluster, AnalogOutput):
    """Temperature measurement cluster to receive reports that are sent to the analog cluster."""

    cluster_id = AnalogOutput.cluster_id
    MEASURED_VALUE_ID = 0x0000

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.counter_bus.add_listener(self)

    def value_reported(self, value):
        """Value reported."""
#        print('value_reported')
        self._update_attribute(self.attridx["present_value"], value)

class ptvoTemperature(CustomDevice):
    """PTVO Temperature."""

    def __init__(self, *args, **kwargs):
        """Init device."""
        self.temperature_bus = Bus()
        self.humidity_bus = Bus()
        self.pressure_bus = Bus()
        self.counter_bus = Bus()
        super().__init__(*args, **kwargs)

    signature = {
        MODELS_INFO: [("ptvo.test1", "ptvo.swich.64991")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: PTVO_DEVICE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    AnalogInput.cluster_id,
                    Diagnostic.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Basic.cluster_id],
            },
            3: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: PTVO_DEVICE,
                INPUT_CLUSTERS: [AnalogInput.cluster_id],
                OUTPUT_CLUSTERS: [],
            },
            4: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: PTVO_DEVICE,
                INPUT_CLUSTERS: [AnalogInput.cluster_id],
                OUTPUT_CLUSTERS: [],
            }
        },
    }

    replacement = {
        ENDPOINTS: {
           1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [PtvoAnalogInputCluster, HumidityMeasurementCluster, TemperatureMeasurementCluster],
                OUTPUT_CLUSTERS: [Basic.cluster_id],
            },
            3: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [PtvoAnalogInputCluster, TemperatureMeasurementCluster, PressureMeasurementCluster],
                OUTPUT_CLUSTERS: [],
            },
            4: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.METER_INTERFACE,
                INPUT_CLUSTERS: [PtvoAnalogInputCluster, AnalogValueMeasurementCluster],
                OUTPUT_CLUSTERS: [],
            }
        }
    }
