#!/usr/bin/env python3

from py3cw.request import Py3CW
import click

"""
Generate an API key for 3commas with using the link below 
Give the key "Bots read" permission and copy the generated key and secret in to the variables below
https://3commas.io/api_access_tokens

Next, set the fee for your exchange. I, personalaly, use the taker fee here. This may result in more 
fees being calculated than were actually incurrred but I would rather be conservative. You can set this 
to anything you want for your preferences.Unfortunately this is the best I can do right now until I find
a way to figure out what type of order was used for specific deals.
"""
### API KEY INFO (PUT YOURS HERE)
KEY = "XXXXXXXXXX"
SECRET = "XXXXXXXX"
### SET THIS TO YOUR FEE PERCENTAGE
FEE = ".5"

"""
Usage Examples:
    To show total for all bots:
        python bot_pl.py

    To show totals for specific bot:
        python bot_pl.py -b 1234567

The bot ID (1234567 in the example above) is a seven digit number found in the URL when viewing a bot.
Example: When viewing my bot, my URL is "https://3commas.io/bots/1234567", my bot ID is "1234567"
"""


def get_prices(deal):
    fee = float(FEE) / 100
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
@click.option("-b", "--bot", required=False, default=None, help="Target Bot ID")
def main(bot):
    """
    Calculate total P/L and Fees from DCA bot trades.
    Will calculate all deals unless bot ID specified with optional argument
    """
    p3cw = Py3CW(
        key=KEY,
        secret=SECRET,
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
        print(error)
        exit(1)

    total_pl = float(0)
    total_fees = float(0)
    for deal in deals:
        pl, fee = get_prices(deal)
        if pl is None and fee is None:
            continue
        if deal.get("status") != "failed":

            print("-----")
            print(f"Deal ID: {deal.get('id')}")
            print(f"P/L: {pl}")
            print(f"Fee: {fee}")
            total_pl += pl
            total_fees += fee
    print()
    print("Totals")
    print("-----")
    print(f"P/L: {total_pl}")
    print(f"Fees: {total_fees}")


if __name__ == "__main__":
    main()