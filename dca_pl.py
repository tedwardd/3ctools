#!/usr/bin/env python3

from py3cw.request import Py3CW
import click
import configparser
import sys
from pathlib import Path

"""
Usage Examples:
    To show total for all bots:
        python dca_pl.py

    To show totals for specific bot:
        python dca_pl.py -b 1234567

The bot ID (1234567 in the example above) is a seven digit number found in the URL when viewing a bot.
Example: When viewing my bot, my URL is "https://3commas.io/bots/1234567", my bot ID is "1234567"
"""


class Config:
    def __init__(self, config_file, nolog):
        config = configparser.ConfigParser()
        config.read(config_file)

        self.api_key = config["GLOBAL"]["api_key"]
        self.api_secret = config["GLOBAL"]["api_secret"]
        self.exchange_fee = config["GLOBAL"]["exchange_fee"]
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
            "finished?": True,
            "limit": 1000,
            "offset": offset,
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
        error, bot_info = self.p3cw.request(
            entity="bots",
            action="show",
            action_id=bot_id,
        )

        return error, bot_info

    def get_prices(self, deal, fee: float):
        # TODO: Use API provided fee information once it's available
        try:
            sold = float(deal.get("sold_volume"))
        except TypeError:
            sold = float(0)
        try:
            bought = float(deal.get("bought_volume"))
        except TypeError:
            bought = float(0)

        sell_fee = sold * fee
        buy_fee = bought * fee
        fees = sell_fee + buy_fee

        real_pl = (sold - (sold * fee)) - (bought - (bought * fee))

        return real_pl, fees


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
def main(bot, config_file, quiet, nolog):
    """
    Calculate total P/L and Fees from DCA bot trades.
    Will calculate all deals unless bot ID specified with optional argument
    """
    config = Config(config_file, nolog)
    client = Client(config)
    if bot is not None:
        error, bot_info = client.bots(bot)
        if error.get("error"):
            click.secho(error.get("msg"), fg="red", bold=True)
            sys.exit(1)
        count = int(bot_info.get("finished_deals_count"))
        if count > 1000:
            count = round(count / 1000)
        deals = []
        offset = 0
        while count > 0:
            error, deal_part = client.deals(bot, offset)
            if error.get("error"):
                click.secho(error.get("msg"), fg="red", bold=True)
                sys.exit(1)
            deals += deal_part
            count -= 1
            offset = offset + 1000
    else:
        error, deals = client.deals(bot, offset)
        if error.get("error"):
            click.secho(error.get("msg"), fg="red", bold=True)
            sys.exit(1)

    total_pl = float(0)
    total_fees = float(0)
    fee = float(config.exchange_fee) / 100
    if not nolog:
        f = Path(config.outfile)
    for deal in deals:
        if not nolog:
            if deals.index(deal) == 0:
                values = ",".join(deal.keys()) + "\n"
        pl, fees = client.get_prices(deal, fee)
        if pl is None and fee is None:
            continue
        if not quiet:
            click.echo(f"Deal ID: {deal.get('id')}")
            click.secho("-----", bold=True)
            click.echo(f"P/L: ${round(pl, 2)}")
            click.echo(f"Fee: ${round(fees, 2)}")
            click.echo()
        total_pl += pl
        total_fees += fees
        value_list = list(deal.values())
        if not nolog:
            for i in value_list:
                values += str(i) + ","
            values += "\n"
    if not nolog:
        f.open("w").write(values)
    if not quiet:
        click.secho("Totals", bold=True)
        click.secho("-----", bold=True)
        click.echo(f"Deals Completed: {len(deals)}")
        click.echo(f"P/L: ${round(total_pl, 2)}")
        click.echo(f"Fees: ${round(total_fees, 2)}")


if __name__ == "__main__":
    main()