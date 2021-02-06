#!/usr/bin/env python3

import dca_pl

class Bot:

    def __init__(self, bot_id):
        self.bot_id = bot_id

    def get_max(self):
        bot = client.p3cw.request(entity="bots", action="show", action_id=self.bot_id)[1]

        self.max_safety_orders = bot.get('max_safety_orders')
        self.max_active_deals = bot.get('max_active_deals')
        self.base_order_volume = bot.get('base_order_volume')
        self.safety_order_volume = bot.get('safety_order_volume')
        self.step_perc = bot.get('martingale_volume_coefficient')
        self.order_size = float(self.base_order_volume) + float(self.safety_order_volume)
        count = float(self.max_safety_orders) - 1
        previous_safety = float(self.safety_order_volume)
        total_order_volume = previous_safety

        safety_order_volume = self.safety_order_volume
        while count > 0:
            current_order = float(safety_order_volume) * float(self.step_perc)
            total_order_volume += float(current_order)
            safety_order_volume = current_order
            count -= 1
            bot_max = round((total_order_volume + float(self.base_order_volume)) * float(self.max_active_deals),2)

        return bot_max

config = dca_pl.Config('config.ini', False)
client = dca_pl.Client(config)

bot = Bot("2515212") # Put your bot ID here
bot_total = bot.get_max()

account_size = client.p3cw.request(entity='accounts', action="")[1][0].get('usd_amount')
account_total = round(float(account_size),2)


print(str(round(bot_total / account_total * 100,2))+"%")

increment = float(0.01)
new_bot_total = float(0)