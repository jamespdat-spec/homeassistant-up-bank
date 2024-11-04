Home Assistant Up Bank Integration

This integration will fetch details about all of your UP accounts, for you to use how you want. I'm in the process of integrating this with an LLM (AI language model) to provide you a break down of your major outgoings, especially subscriptions that can be altered.

At the moment it refreshes once an hour to update balances. Ideally I would like to receive webhooks and update in real-time.

Any feature requests feel free to vote or add a [discussion](https://github.com/richardsj/homeassistant-up--bank/discussions) or at the [upstream repo](https://github.com/jay-oswald/ha-up-bank/discussions)and any bugs create, or comment on an [issue](https://github.com/jay-oswald/ha-up-bank/issues)

# Installation
The easiest way is to install via HACS, see https://github.com/hacs/integration to install HACS in your Home Assistant install if you haven't already.

1. Go to HACS on your home assistant site (usually a tab on the left)
2. Select Integrations
3. Top right click on the 3 dots, then Custom repositories
3. Enter this repository https://github.com/richardsj/homeassistant-up-bank then underneath, select category *integration* and add
4. Explore and Download
5. Search for HA UP in the list at the top and install this integration - it will have the little Up logo
6. Restart Home Assistant
7. Go to regular e.g. Integrations (e.g. Settings -> Devices &amp; Services -> (ADD INTEGRATION) _(bottom right)_
8. Search for and add Up Bank for Home Assistant - click the three small dots on the right of the line and choose DOWNLOAD
9. Get your UP API key from: https://api.up.com.au/getting_started
10. Enter the API key on the config screen

# Development
I have included a docker-compose file with mapping, so make sure you have docker, and docker-compose installed. Then you can start it with `docker-compose up -d`. Every time you change the files you will need to restart the server inside the HA GUI for the changes to kick in.

# Updated in November 2024 to run with HACS
And has some robustness improvements, please let me know if you come up against any issues.
