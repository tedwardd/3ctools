#!/usr/bin/env python3

from py3cw.request import Py3CW
import click
import configparser
import sys
from pathlib import Path
from datetime import datetime
import time
import json

"""
Usage Examples:
    To show total for all bots:
        python dca_pl.py

    To show totals for specific bot:
        python dca_pl.py -b 1234567

The bot ID (1234567 in the example above) is a seven digit number found in the URL when viewing a bot.
Example: When viewing my bot, my URL is "https://3commas.io/bots/1234567", my bot ID is "1234567"
"""

MAX_RESP = 1000  # Max response size for 3commas API
OMIT_STATUS = ["cancelled", "failed"]  # Default statuses to omit if not in config.ini


class Config:
    def __init__(self, config_file, nolog):
        config = configparser.ConfigParser()
        config.read(config_file)

        self.api_key = config["GLOBAL"]["api_key"]
        self.api_secret = config["GLOBAL"]["api_secret"]
        try:
            self.omit_statuses = config["GLOBAL"]["omit_statuses"]
        except KeyError:
            self.omit_statuses = OMIT_STATUS

        if not nolog:
            try:
                self.outfile = config["GLOBAL"]["outfile"]
            except KeyError:
                click.secho(
                    f"No value for 'outfile' configured in {config_file}",
                    fg="red",
                    bold=True,
                )
                exit(1)


class Client:
    def __init__(self, config):
        self.p3cw = Py3CW(
            key=config.api_key,
            secret=config.api_secret,
            request_options={
                "request_timeout": 10,
                "nr_of_retries": 1,
                "retry_status_codes": [502],
            },
        )

    def deals(self, bot_id, offset):
        payload = {
            "limit": MAX_RESP,
            "offset": int(offset),
            "scope": "finished",
        }
        if bot_id is not None:
            payload.update(
                {
                    "bot_id": bot_id,
                }
            )
        error, deals = self.p3cw.request(
            entity="deals",
            action="",
            payload=payload,
        )

        return error, deals

    def bots(self, bot_id):
        if bot_id is not None:
            error, bot_info = self.p3cw.request(
                entity="bots",
                action="show",
                action_id=bot_id,
            )
            return error, bot_info
        error, bot_info = self.p3cw.request(
            entity="bots",
            action="",
        )
        return error, bot_info

    def get_prices(self, deal):
        try:
            sold = float(deal.get("sold_volume"))
        except TypeError:
            sold = float(0)
        try:
            bought = float(deal.get("bought_volume"))
        except TypeError:
            bought = float(0)

        pl_val = sold - bought
        if bought > 0 and sold > 0:
            pl_perc = "%.2f" % (round(1 - (bought / sold), 4) * 100)
        else:
            pl_perc = 0

        return pl_val, pl_perc

    def balances_by_exchange(self):
        error, account_data = self.p3cw.request(
            entity="accounts",
            action="",
        )

        if error.get("error"):
            click.secho(error.get("msg"), fg="red", bold=True)
            sys.exit(1)

        exchange_balances = []
        for exchange in account_data:
            exchange_name = exchange.get("name")
            usd_balance = "%.2f" % float(exchange.get("usd_amount"))
            exchange_dict = {exchange_name: usd_balance}
            exchange_balances.append(exchange_dict)

        return exchange_balances


@click.command()
@click.option(
    "-b",
    "--bot",
    required=False,
    default=None,
    help="Target Bot ID",
)
@click.option(
    "-c",
    "--config",
    "config_file",
    required=False,
    default="config.ini",
    help="Alternate config file. Default: config.ini",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Quiet: supress output to screen",
)
@click.option(
    "--nolog",
    is_flag=True,
    help="Do not write to output file",
)
@click.option(
    "-s",
    "--size",
    default=None,
    required=False,
    help="Amount allocated for bot (use with -b)",
)
@click.option(
    "--totals-only",
    is_flag=True,
    help="Only print totals to stdout",
)
def main(
    bot: int,
    config_file: str,
    quiet: bool,
    nolog: bool,
    size: int,
    totals_only: bool,
):
    """
    Calculate total P/L from DCA bot trades.
    Will calculate all deals unless bot ID specified with optional argument
    """

    config = Config(config_file, nolog)
    client = Client(config)
    error, bot_info = client.bots(bot)
    if error.get("error"):
        click.secho(error.get("msg"), fg="red", bold=True)
        sys.exit(1)
    if type(bot_info) is list:
        count = 0
        for list_bot in bot_info:
            count += int(list_bot.get("finished_deals_count"))
    else:
        count = int(bot_info.get("finished_deals_count"))
    if count > MAX_RESP:
        count = round(count / MAX_RESP)

    else:
        count = 1
    deals = []
    offset = 0
    while count > 0:
        error, deal_part = client.deals(bot, offset)
        if error.get("error"):
            click.secho(error.get("msg"), fg="red", bold=True)
            sys.exit(1)
        deals += deal_part
        count -= 1
        offset = offset + MAX_RESP

    total_pl = float(0)
    total_perc = float(0)
    deal_count = len(deals)
    total_deals_len = None
    for deal in deals:
        if not nolog:
            if deals.index(deal) == 0:
                values = ",".join(deal.keys()) + "\n"
        pl, pl_perc = client.get_prices(deal)
        if pl is None:
            continue
        if deal.get("status") in config.omit_statuses:
            del deals[deals.index(deal)]
            continue
        if not quiet and not totals_only:
            click.echo(f"Deal ID: {deal.get('id')}")
            click.echo(f"P/L: ${round(pl, 2)}")
            click.echo(f"P/L%: {pl_perc}%\n")
        total_perc += float(pl_perc)
        total_pl += pl
        value_list = list(deal.values())
        start = str(deal.get("created_at")).split(".")[0]
        end = str(deal.get("closed_at")).split(".")[0]
        if start is not None and end is not None:
            start = datetime.fromisoformat(start)
            end = datetime.fromisoformat(end)
            deal_len = end - start
            if total_deals_len is None:
                total_deals_len = deal_len
            else:
                total_deals_len += deal_len
        if not nolog:
            for i in value_list:
                values += str(i) + ","
            values += "\n"
    avg_deal_len = str(total_deals_len.seconds / int(deal_count) / 60)
    # print(time.strftime(avg_deal_len))
    if not nolog:
        with Path(config.outfile) as f:
            f.open("w").write(values)
    if not quiet:
        click.secho("Totals", bold=True)
        click.secho("-----", bold=True)
        click.echo(f"Deals Completed: {len(deals)}")
        click.echo(f"P/L: ${round(total_pl, 2)}")
        if size is not None:
            click.echo(f"Total P/L %: {round((total_pl/float(size))*100, 2)}%")
        avg_pl = int(total_perc) / int(deal_count)
        click.echo(f"Avg. P/L %: {round(avg_pl, 2)}%")

    balances_by_exchange = json.dumps(client.balances_by_exchange())


if __name__ == "__main__":
    main()