#!/usr/bin/env python3

import dca_pl

config = dca_pl.Config('config.ini', False)
client = dca_pl.Client(config)

bot_id = "xxxxxxx" # Put your bot ID here

bot = client.p3cw.request(entity="bots", action="show", action_id=bot_id)[1]

max_safety_orders = bot.get('max_safety_orders')
max_active_deals = bot.get('max_active_deals')
base_order_volume = bot.get('base_order_volume')
safety_order_volume = bot.get('safety_order_volume')
step_perc = bot.get('martingale_volume_coefficient')
order_size = float(base_order_volume) + float(safety_order_volume)
count = float(max_safety_orders) - 1
previous_safety = float(safety_order_volume)
total_order_volume = previous_safety

while count > 0:
    current_order = float(safety_order_volume) * float(step_perc)
    total_order_volume += float(current_order)
    safety_order_volume = current_order
    count -= 1

print((total_order_volume + float(base_order_volume)) * float(max_active_deals))