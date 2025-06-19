# Consciousness (abbreviated as c11s)
## Observability and Introspection System

Based on ideas from this blog post I wrote a few years ago [Perhaps Conciousness is Just Huan Observability](https://medium.com/@adrianco/perhaps-consciousness-is-just-human-observability-84dfda40d70f) I would like to be able to have a conversation with an autonomous system to understand how it is feeling, why it did something, and what is bothering it.

If my self driving car was conscious, I could ask it why it did something, it could tell me it's worried and slowing down because it's raining, or that it saw a deer at the side the road (that I dodn't see) and braked hard, it could say that the pressure in one of it's tires has been dropping slowly over the last few days so I should get it checked for a puncture before I go on a long drive. However I don't have a way to interface into my cars to build this.

If my house was conscious, it could tell me that it's worried about the storm that's forecasted, that we left the heating on in the guest house when no-one is staying there, that the aircon filters are getting clogged or that the furnace has failed because it's asking for heat/cool but not responding. It would know who lives here, I could tell it that we expect visitors, or are leaving the house empty and it would understand the context. There are a large number of independent IoT based systems around my house, from multiple vendors, some of which have APIs and some just have mobile apps or web interfaces. It seems plausible to develop a system that incrementally adds interfaces to different aspects of the house, and to feed them into something like a [Self Aware Feeback Loop Algorithm](https://github.com/ruvnet/safla) that has a mental model scoped to entities and activities related to living in a  complicated connected house.

## Example conversations

### For Houses, could apply to other bounded domains.
Climate, Memories
Weather, Situation
Mood – accumulated emotion
Emotion – bored, happy/satisfied, excited
Health
Pain – memories to avoid
Pleasure – interactions
Events
Entities – people, devices

“I’ve got a pain in the diodes down my left hand side.”

### Climate / seasons
Winter – Nov to April
Summer – May to August
Hurricane/Storm Season – Sept to Oct
Length of day
Temperature → pool heater needed or not
Rain
Bugs / Mosquitoes

Hurricane
→ Wind → need to pack stuff away
→ Power cuts
→ Fires
→ Possible house damage

Memories of hurricanes

### Calendar Patterns & Activities

Pool guy on Fridays – normal
Yard workers or cleaners on a schedule
Others unusual → notify / record
Owners home or away – remember calendar entries and flights

### Cooling & lighting
Hot water
Guests staying
Parties
Hot water heater is off, want it on? → Y/N → for 6 days


### Health / Pain
Heating / cooling working
Hot water supply
High winds / storms
Water pressure
Leaks & floods
Frost / snow
Power outage

### house → context-aware conversation
“Good morning, do you want to open the blinds and gate, and turn off the lights? Anything else?”
→ yes → gate → lights
“Good evening, do you want to setup for dinner inside or outside?”
→ inside
→ (Turning on inside lights... anything else?)
→ (room scene set to cooking)

### house @ 4pm
Rain / storm / hurricane forecast for later — is everything put away outside, or would you like a reminder to do that at 3pm?
It’s going to be hot today, do you want to turn on the AC?
→ yes → OK, check windows and fans are closed
→ AC
→ Fans
Stuff delivery today — should I open the gate?
→ yes / no
Pool or yard worker comes today — close blinds when the gate is opened?

### Troubleshooting + Emotional Check-ins
AC is running but not cooling in the hallway. Something isn’t right. Did someone call for service?
→ yes
→ How many days to fix? → 4
→ Duly noted.
AC seems better now, did it get fixed?
→ yes
→ Good, I feel better now.

### How do you feel?
Happy — everything is working fine and it’s a nice day
Worried — bad weather coming
Bored — nothing much happened recently
Excited — lots going on


