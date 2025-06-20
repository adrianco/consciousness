# Consciousness (abbreviated as c11s)
## Observability and Introspection System

Based on ideas from this blog post I wrote a few years ago [Perhaps Conciousness is Just Human Observability](https://medium.com/@adrianco/perhaps-consciousness-is-just-human-observability-84dfda40d70f) (extracted text included in this repo) I would like to be able to have a conversation with an autonomous system to understand how it is feeling, why it did something, and what is bothering it.

If my self driving car was conscious, I could ask it why it did something, it could tell me it's worried and slowing down because it's raining, or that it saw a deer at the side the road (that I didn't see) and braked hard, it could say that the pressure in one of it's tires has been dropping slowly over the last few days so I should get it checked for a puncture before I go on a long drive. However I don't have a way to interface into my cars to build this.

If my house was conscious, it could tell me that it's worried about the storm that's forecasted, that we left the heating on in the guest house when no-one is staying there, that the aircon filters are getting clogged or that the furnace has failed because it's asking for heat/cool but not responding. It would know who lives here, I could tell it that we expect visitors, or are leaving the house empty and it would understand the context. There are a large number of independent IoT based systems around my house, from multiple vendors, some of which have APIs and some just have mobile apps or web interfaces. It seems plausible to develop a system that figures out how to create interfaces to different aspects of the house, and to feed them into something like a [Self Aware Feeback Loop Algorithm](https://github.com/ruvnet/safla) that has a mental model scoped to entities and activities related to living in a relatively complicated connected house.

## Scope, Examples and Conversations

### Entities and Environment For Houses
- Climate, Memories of notable weather events
- Weather, the situation now
- Emotion – bored, happy/satisfied, excited, unhappy
- Mood – accumulated emotion over time
- Health status
- Pain – memories of bad things to avoid
- Pleasure – memories of good days
- Events - people coming and going, maintenance
- Entities – people, devices, rooms, spaces outside and systems around the house

Joke reference - Marvin from the Hitchhikers Guide for the Galaxy “I’ve got a pain in the diodes down my left hand side.”

### Climate and Seasons Examples
- Winter – Nov to April
- Summer – May to August
- Hurricane/Storm Season – Sept to Oct
- Length of day variation
- Temperature - is the pool heater needed or not?
- Rainy season or fire season
- Bugs / Mosquitoes season

Hurricane, storm, nearby fire preparation
- Wind - need to pack stuff away
- Power cuts
- Fires
- Possible house damage

Memories of hurricanes etc.

### Calendar Patterns & Activities Examples
- Pool guy, yard workers or cleaners - normal behavior on a schedule
- Other visitors are unusual → notify and question the owner, record
- Owners could be home or away – remember calendar entries and flights, prepare for return

### Energy management - Cooling, heating, lighting and charging
- Air conditioning zone management based on owner and guest activity
- Hot water schedule
- When are guests staying, or larger groups and parties
- Ask owner "Guest coming, guest space hot water heater is off, want it on?" → Yes for 6 days
- Battery backup levels
- Electric car charging schedule

### Health Checks and Pain
Assume that most houses have things that are known to not be working at the moment
- Is Heating / cooling working properly?
- Hot water supply
- High winds / storms
- Water pressure
- Leaks & floods
- Frost / snow
- Power outage
- Internet connection outage

### house context-aware conversation examples
Detected owner is up: “Good morning, do you want to open the blinds and turn off the lights? Anything else happening today?”
→ "yes, and we have a plumber coming to fix a leak between 10 and noon"

“Good evening, do you want to setup for dinner inside or outside?”
→ "inside"
"Room scenes set in kitchen and dining room... anything else?"
→ "turn on <your choice of music> in those rooms

"Rain / storm / hurricane forecast for later — is everything put away outside, or would you like a reminder to do that at 3pm?"

"It’s going to be hot today, do you want to turn on the AC?"
→ "yes" → "OK, check windows are closed"

"Stuff being delivered today — should I open the gate?"

"Pool or yard worker comes today — should I close blinds when the gate is opened?"

### Troubleshooting + Emotional Check-ins
"AC is running but not cooling in the hallway. Something isn’t right. Did someone call for service?"
→ "yes"
→ "How many days to fix?" → 4
→ "Duly noted."

"AC seems better now, did it get fixed?"
→ "yes"
→ "Good, I'm happy now"

### How do you feel?
- Happy — everything is working fine and it’s a nice day
- Worried — bad weather coming
- Bored — nothing much happened recently
- Excited — lots going on

## Development Architecture
Coded in Python, with a service running on something like a Mac Mini somewhere in the house, calling out to APIs and web interfaces as needed.

Mobile single page web app that surfaces a basic interface to the owners and guests. iOS app if needed to support notifications and spoken interface.

Architecture consiste of a control loop along the lines of the STPA model described in the blog post [Failure Modes and Continuous Resilience](https://medium.com/@adrianco/failure-modes-and-continuous-resilience-6553078caad5), text of this post is supplied in the references folder.
The house is a system that has many "Observability" interfaces. The observable inputs feed a "Consciousness" model. Some aspects of the house system can be manipulated via "Controllability" interfaces. 




