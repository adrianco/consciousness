# UX Flow Diagrams - Visual Representations

## Device Discovery & Interview Flow Diagram

```
┌─────────────────┐
│  Entry Points   │
├─────────────────┤
│ • Dashboard     │
│ • Auto-detect   │
│ • Manual scan   │
└───────┬─────────┘
        │
        ▼
┌─────────────────────────┐      ┌──────────────────┐
│   Device Detection      │      │  Manual Trigger  │
├─────────────────────────┤      ├──────────────────┤
│ • Bluetooth scan        │◄─────┤ User clicks      │
│ • mDNS scan            │      │ "Scan Devices"   │
│ • UPnP scan            │      └──────────────────┘
│ • Network scan         │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│   Device Found          │
├─────────────────────────┤
│ Show notification:      │
│ "New device detected"   │
└───────┬─────────────────┘
        │
        ▼
    ┌───────────┐
    │ Decision  │
    ├───────────┤
    │ User      │
    │ Action?   │
    └─────┬─────┘
          │
    ┌─────┼─────┬──────────────┐
    ▼     ▼     ▼              ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Interview│ │ Skip   │ │ Ignore │ │ Cancel │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌──────┐
│Interview│ │ Add to │ │Add to  │ │ Exit │
│ Wizard  │ │Pending │ │Ignore  │ └──────┘
└────┬────┘ │ List   │ │List    │
     │      └────────┘ └────────┘
     │
     ▼
┌──────────────────────┐
│ Interview Step 1     │
├──────────────────────┤
│ "Name this device"   │
│ ┌──────────────────┐ │
│ │ [Text Input]     │ │
│ └──────────────────┘ │
│ Suggested: "Living   │
│ Room Light"          │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Interview Step 2     │
├──────────────────────┤
│ "Where is it?"       │
│ ┌──────────────────┐ │
│ │ [Dropdown]       │ │
│ └──────────────────┘ │
│ • Living Room        │
│ • Bedroom            │
│ • Kitchen            │
│ • [Custom...]        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Interview Step 3     │
├──────────────────────┤
│ "What can it do?"    │
│ ☑ Turn on/off        │
│ ☑ Dim/Brighten       │
│ ☐ Change colors      │
│ ☐ Set schedules      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Interview Step 4     │
├──────────────────────┤
│ "When active?"       │
│ ┌──────────────────┐ │
│ │ Schedule Builder │ │
│ └──────────────────┘ │
│ Always / Scheduled   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Configuration Review │
├──────────────────────┤
│ Name: Living Light   │
│ Room: Living Room    │
│ Type: Smart Bulb     │
│ Features: On/Off/Dim │
│                      │
│ [Confirm] [Back]     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Connection Attempt   │
├──────────────────────┤
│ "Connecting..."      │
│ ████████░░ 80%       │
└──────┬───────────────┘
       │
   ┌───┴───┐
   │Success│
   │  or   │
   │ Fail? │
   └───┬───┘
       │
   ┌───┼───┐
   ▼       ▼
┌──────┐ ┌─────────────┐
│Success│ │   Failure    │
├──────┤ ├─────────────┤
│ ✓    │ │ ⚠ Error     │
│Device│ │ Connection  │
│Added │ │ failed      │
│      │ │             │
│Create│ │ [Retry]     │
│Twin  │ │ [Help]      │
└──────┘ │ [Skip]      │
         └─────────────┘
```

## Natural Language Chat Flow Diagram

```
┌─────────────────┐
│  Entry Points   │
├─────────────────┤
│ • Chat tab      │
│ • Float button  │
│ • "Hey House"   │
│ • Mobile app    │
└────────┬────────┘
         │
         ▼
┌────────────────────────┐
│   Chat Interface       │
├────────────────────────┤
│ ┌────────────────────┐ │
│ │ Welcome! I'm your  │ │
│ │ house. How can I   │ │
│ │ help today?        │ │
│ └────────────────────┘ │
│                        │
│ Suggested:             │
│ • "How are you?"       │
│ • "Show my devices"    │
│ • "Run morning routine"│
│                        │
│ ┌────────────────────┐ │
│ │ [Type message...] 🎤│ │
│ └────────────────────┘ │
└────────┬───────────────┘
         │
    ┌────┴────┐
    │  Input  │
    │  Type?  │
    └────┬────┘
         │
    ┌────┼────┐
    ▼         ▼
┌────────┐ ┌────────┐
│  Text  │ │ Voice  │
└────┬───┘ └───┬────┘
     │         │
     │         ▼
     │   ┌──────────┐
     │   │Listening.│
     │   │ ●●●●●    │
     │   └────┬─────┘
     │        │
     │        ▼
     │   ┌──────────────┐
     │   │ Transcribe:  │
     │   │ "Turn on     │
     │   │ living room  │
     │   │ lights"      │
     │   └──────┬───────┘
     │          │
     └──────────┤
                │
                ▼
┌───────────────────────┐
│  Process Request      │
├───────────────────────┤
│ Understanding...      │
│ ░░░░░░░░░░           │
└──────────┬────────────┘
           │
           ▼
      ┌─────────┐
      │ Request │
      │  Type?  │
      └────┬────┘
           │
  ┌────────┼────────┬──────────┐
  ▼        ▼        ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Query │ │Action│ │Status│ │ Chat │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌──────┐ ┌──────────┐ ┌────────┐ ┌────────┐
│Return│ │ Need      │ │Display │ │Continue│
│ Info │ │Confirm?   │ │ Status │ │ Conv.  │
└──────┘ └────┬─────┘ └────────┘ └────────┘
              │
          ┌───┴───┐
          │  Yes  │
          └───┬───┘
              │
              ▼
┌────────────────────────┐
│   Confirmation         │
├────────────────────────┤
│ Turn on living lights? │
│                        │
│ This will:             │
│ • Turn on 3 bulbs      │
│ • Set to 100%          │
│                        │
│ [Yes, do it] [Cancel]  │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   Execute Action       │
├────────────────────────┤
│ Turning on lights...   │
│ ████████████ Done!     │
│                        │
│ ✓ Living room lights   │
│   are now on           │
└────────────────────────┘
```

## Scenario Execution Flow Diagram

```
┌──────────────────┐
│  Entry Points    │
├──────────────────┤
│ • Scenarios tab  │
│ • Chat command   │
│ • Schedule       │
│ • Quick action   │
└────────┬─────────┘
         │
         ▼
┌────────────────────────┐
│  Scenario Library      │
├────────────────────────┤
│ ┌──────┐ ┌──────┐     │
│ │Morning│ │ Party│     │
│ │Routine│ │ Mode │     │
│ └──────┘ └──────┘     │
│ ┌──────┐ ┌──────┐     │
│ │Energy │ │Vacation│   │
│ │ Save  │ │ Mode  │    │
│ └──────┘ └──────┘     │
│                        │
│ [Create Custom]        │
└────────┬───────────────┘
         │
         ▼
    ┌─────────┐
    │ Select  │
    │Scenario │
    └────┬────┘
         │
         ▼
┌────────────────────────┐
│  Scenario Preview      │
├────────────────────────┤
│ Morning Routine        │
│ ─────────────         │
│ Duration: 15 min       │
│                        │
│ Steps:                 │
│ 1. ☀ Lights gradual   │
│ 2. 🌡 Heat to 72°F    │
│ 3. ☕ Start coffee     │
│ 4. 📱 Show weather    │
│ 5. 🎵 Play music      │
│                        │
│ Affects: 8 devices     │
│                        │
│ [Run Now] [Schedule]   │
│ [Customize]            │
└────────┬───────────────┘
         │
    ┌────┴────┐
    │ Action? │
    └────┬────┘
         │
    ┌────┼────┬─────────┐
    ▼    ▼    ▼         ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│ Run  ││Schedule│Customize│Cancel│
└──┬───┘└───────┘└───────┘└──────┘
   │
   ▼
┌────────────────────────┐
│  Confirm Execution     │
├────────────────────────┤
│ Run Morning Routine?   │
│                        │
│ This will immediately: │
│ • Turn on lights       │
│ • Adjust temperature   │
│ • Start coffee maker   │
│                        │
│ [Start] [Cancel]       │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Execution Progress    │
├────────────────────────┤
│ Morning Routine        │
│ ████████░░░░ 66%       │
│                        │
│ ✓ Lights on (gradual)  │
│ ✓ Temperature set      │
│ ▶ Starting coffee...   │
│ ⧖ Weather display      │
│ ⧖ Music playlist       │
│                        │
│ [Pause] [Stop]         │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Completion            │
├────────────────────────┤
│ ✓ Morning Routine      │
│   Complete!            │
│                        │
│ Summary:               │
│ • 5/5 steps completed  │
│ • Time: 14:32          │
│ • Energy: +2.3 kWh     │
│                        │
│ How was it?           │
│ 😊 😐 😞              │
│                        │
│ [Save as Favorite]     │
│ [View Details]         │
└────────────────────────┘
```

## First-Time Onboarding Flow Diagram

```
┌──────────────────┐
│   First Launch   │
└────────┬─────────┘
         │
         ▼
┌────────────────────────┐
│     Welcome Screen     │
├────────────────────────┤
│   🏠                   │
│ Welcome to your        │
│ Conscious House!       │
│                        │
│ Your house is about    │
│ to become aware...     │
│                        │
│ [Let's Start]          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│    Basic Setup (1/5)   │
├────────────────────────┤
│ What should I call     │
│ your house?            │
│ ┌────────────────────┐ │
│ │ [e.g., Home]       │ │
│ └────────────────────┘ │
│                        │
│ [Next] [Skip]          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│   Location (2/5)       │
├────────────────────────┤
│ Where are we?          │
│ ┌────────────────────┐ │
│ │ [ZIP/Postal Code]  │ │
│ └────────────────────┘ │
│ (For weather & time)   │
│                        │
│ [Next] [Skip]          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Personality (3/5)     │
├────────────────────────┤
│ How should I talk?     │
│                        │
│ ○ Friendly & Chatty    │
│   "Hey! Good morning!" │
│                        │
│ ● Professional         │
│   "Good morning."      │
│                        │
│ ○ Minimal              │
│   [Status only]        │
│                        │
│ [Next]                 │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Discovery (4/5)       │
├────────────────────────┤
│ Looking for devices... │
│                        │
│ Scanning:              │
│ ✓ Bluetooth (3 found)  │
│ ▶ WiFi devices...      │
│ ⧖ Smart hubs          │
│                        │
│ Found so far: 7        │
│                        │
│ [Continue Scanning]    │
│ [Start Setup]          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Quick Setup (5/5)      │
├────────────────────────┤
│ Let's name your        │
│ devices:               │
│                        │
│ 💡 Philips Hue         │
│ └─ Living Room Light   │
│                        │
│ 🌡️ Nest Thermostat    │
│ └─ Main Thermostat     │
│                        │
│ 🔒 August Lock         │
│ └─ Front Door          │
│                        │
│ [Finish] [Details]     │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  First Interaction     │
├────────────────────────┤
│ 🎉 Setup Complete!     │
│                        │
│ Try saying:            │
│ "Hey House, how are    │
│  you feeling?"         │
│                        │
│ Or type below:         │
│ ┌────────────────────┐ │
│ │ [Type here...]    🎤│ │
│ └────────────────────┘ │
│                        │
│ [Go to Dashboard]      │
└────────────────────────┘
```

## Implementation Notes

These flow diagrams represent the ideal user experience for the House Consciousness System. Key principles:

1. **Progressive Disclosure**: Information revealed as needed
2. **Clear Feedback**: Users always know what's happening
3. **Easy Recovery**: Clear paths from any error state
4. **Quick Success**: Get to value quickly
5. **Personality**: Let the house consciousness shine through

The diagrams use standard flowchart notation:
- Rectangles: Process/Screen
- Diamonds: Decision points
- Arrows: Flow direction
- Icons: Visual cues for actions