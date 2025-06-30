# Feedback on feature set and UX plans
Rewrite the plans to take what follows into account, but don't start any implementation.

## Digital Twins
The current digital twin functionality is all wrong. The way a digital twin is supposed to work is that every device has a digital twin that is a software representation of the last recorded state seen and any pending changes and is always available. The real device is accessed remotely from time to time, depending on what kind of device it is, and is synchronized with the digital twin. It's a common pattern used with IoT devices. There may be existing Python frameworks that implement this pattern, so do some more research and re-write the plans for review. Don't code anything yet.

## Personas
The current UX personas look good except that the Professional Installer persona "Jordan" is going to be replaced by the intelligent discovery conversation features of this product.

## Conversations
There is currently more than one place in the app where conversations can take place, and they need to be combined into a single conversational interface which can be used for setup, installation and operation of the system.
When a mobile app is built, it will provide a single channel voice interface for controlling every aspect of the system.

## User experiences
There are three different User experiences to consider.
1. development activity, the service is running in Codespaces and testing takes place using an additional house simulator process and the web UI for dialog only.

2. for test deployment the service is installed from github, is running in the house and testing and development will take place of the service and the mobile app, using web ui and voice.

3. production deployment, the service will be deployed via a package manager and the mobile app via the app store.

For now we only need to consider the development experience. We will revisit later to develop a production plan.

## Discovery process
The first interactions with the system are the discovery process, it involves discovering the layout of the house itself and the devices that are in it, and it occurs incrementally, so that the first device or room that is found can be interacted with, and the minimal working system can be extended as time allows towards a more complete coverage of the house. Aspects of the house that are not currently accessable by the system can be described and stored as notes so that questions about how to do things in the house can be answered, and notes can be used to find and attach devices described in the notes. Existing notes and devices and rooms/areas can be updated as their situation changes, with archived memory of the previous configuration.

Step by step in the discovery process:
0. Create a local instance of a House Model Context Protocol server that will be used to persist all the configuration information known about this specific house. Device status and data updates are not stored in the House MCP. Create a local vault and use it to store all authentication and credentials specific to the house.
1. locate the house, by specifying an address or using location services if the mobile app is in use
2. lookup a source for the local weather forecast
3. connect to Apple Homekit if available and populate the house model with whatever rooms and devices are defined there
4. explore the house, one room or outside area at a time, making notes about the room, it's doorways and connected devices - this experience could feel a bit like the old zork adventure game, build a graph that connects the house and devices and generate a map view in the webui
5. gradually refine the notes until there is enough information to add as devices
6. add devices that aren't tied to any particular room like personal weather stations or outside temperature sensors
7. add devices that connect to multiple rooms like gas and electric heating/cooling furnaces, describing which thermostats control them, and which rooms they heat

Devices fall into three categories - device specific information is stored in a Devices Model Context Protocol server that is maintained in the github repo and shared across installations.
a - additional instances of known devices that are already integrated into the system, and just need to be identified
b - well known devices that the system has integrated with before, which may need account setup and authentication that can be handled locally.
c - novel devices that will need some research and code development to support, possibly leveraging Home Assistant drivers. These will need to create a github issue with a clearly defined prompt describing what is needed.

Github issues will be processed with claude-flow and resulting device integration code, once shown to be working, will be shared with other homes.

When performing reaserch and development on new device support, the token counts consumed must be noted so that cost estimates can be produced for similar work on future drivers.

## Simulator
The House simulator runs as a separate Python application with it's own webui (on a different port), and supports an API that the digital twin layer can call to obtain simulated device data.
The simulator also reads from the House MCP and Drivers MCP.
The simulator provides plausible fake data and the simulator webui allows this to be manipulated to create different test scenarios
