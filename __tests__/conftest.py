from favicorn.event_buses import DequeEventBusFactory
from favicorn.i.event_bus import IEventBusFactory

event_bus_factories: list[IEventBusFactory] = [
    DequeEventBusFactory(),
]
