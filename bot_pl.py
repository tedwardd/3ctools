#!/usr/bin/env python3

from py3cw.request import Py3CW
import click
import configparser

"""
Usage Examples:
    To show total for all bots:
        python bot_pl.py

    To show totals for specific bot:
        python bot_pl.py -b 1234567

The bot ID (1234567 in the example above) is a seven digit number found in the URL when viewing a bot.
Example: When viewing my bot, my URL is "https://3commas.io/bots/1234567", my bot ID is "1234567"
"""


def get_prices(deal, fee: float):
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
    required=False,
    default="config.ini",
    help="Alternate config file. Default: config.ini",
)
def main(bot, config):
    """
    Calculate total P/L and Fees from DCA bot trades.
    Will calculate all deals unless bot ID specified with optional argument
    """
    cfg = configparser.ConfigParser()
    cfg.read(config)
    p3cw = Py3CW(
        key=cfg["GLOBAL"]["api_key"],
        secret=cfg["GLOBAL"]["api_secret"],
        request_options={
            "request_timeout": 10,
            "nr_of_retries": 1,
            "retry_status_codes": [502],
        },
    )

    if bot is not None:
        error, deals = p3cw.request(
            entity="deals",
            action="show",
            action_id=bot,
        )
    if bot is None:
        error, deals = p3cw.request(
            entity="deals",
            action="",
        )
    if error != {}:
        click.secho(error, fg="red", bold=True)
        exit(1)

    total_pl = float(0)
    total_fees = float(0)
    fee = float(cfg["GLOBAL"]["exchange_fee"]) / 100

    for deal in deals:
        if not deal.get("finished?"):
            continue
        pl, fees = get_prices(deal, fee)
        if pl is None and fee is None:
            continue
        if deal.get("status") != "failed":

            click.secho("-----", bold=True)
            click.echo(f"Deal ID: {deal.get('id')}")
            click.echo(f"P/L: {pl}")
            click.echo(f"Fee: {fees}")
            total_pl += pl
            total_fees += fees
    click.echo()
    click.secho("Totals", bold=True)
    click.secho("-----", bold=True)
    click.echo(f"P/L: {total_pl}")
    click.echo(f"Fees: {total_fees}")


if __name__ == "__main__":
    main()