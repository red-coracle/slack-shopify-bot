# slack-shopify-bot
A Slack bot that sends Shopify order notifications to a specific channel

Usage:
1. Clone repo and install dependencies.
2. Copy `sample-config.py` to `config.py`, update values inside.
3. Copy `sample-order-notify.service` to systemd folder
(e.g. `/etc/systemd/system/order-notify.service`) and update the values inside.
4. Start the service and watch the notifications roll in!
