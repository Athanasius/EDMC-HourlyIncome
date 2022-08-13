"""
Calculate and display hourly income since last reset.

Based on Exynom's original.
"""
import time
import tkinter as tk

from config import config
from l10n import Locale

CFG_EARNINGS = "EarningSpeed_earnings"


class This():
    """Holds module globals."""

    def __init__(self):
        self.hourlyincome: HourlyIncome


class Transaction(object):
    """The details about a single transaction."""

    earnings = 0.0
    time = 0.0
    is_docking_event = 0.0


class HourlyIncome(object):
    """The main class for the hourlyincome plugin."""

    speed_widget = None
    rate_widget = None
    earned_widget = None
    saved_earnings = 0
    transactions: list = []

    def reset(self):
        """Handle the reset button being pressed."""
        self.transactions = []
        self.saved_earnings = 0
        self.update_window()
        self.save()

    def load(self):
        """Load saved earnings from config."""
        saved = config.get_str(CFG_EARNINGS)
        if not saved:
            self.saved_earnings = 0.0
        else:
            self.saved_earnings = float(saved)

    def save(self):
        """Save the saved earnings to config."""
        config.set(CFG_EARNINGS, str(self.saved_earnings + self.trip_earnings()))

    def transaction(self, earnings: float):
        """
        Record a transaction.

        :param earnings:
        """
        data = Transaction()
        data.earnings = earnings
        data.is_docking_event = 0.0
        data.time = time.time()
        self.transactions.append(data)
        self.update_window()
        self.save()

    def register_docking(self):
        """Record a docking event."""
        data = Transaction()
        data.earnings = 0.0
        data.is_docking_event = 1.0
        data.time = time.time()
        self.transactions.append(data)
        self.update_window()
        self.save()

    def trip_earnings(self):
        """
        Calculate the current trip earnings.

        :return: int - the current trip earnings
        """
        return sum([x.earnings for x in self.transactions])

    def rate(self):
        """
        Calculate the rate of station visits/hour.

        :return: Calculated visits/hour
        """
        if len(self.transactions) > 1:
            started = self.transactions[0].time
            now = time.time()
            return sum([x.is_docking_event for x in self.transactions]) * 60.0 * 60.0 / (now - started)
        else:
            return 0.0

    def speed(self):
        """
        Calculate the current credits/hour.

        :return: Calculated credits/hour
        """
        earned = self.trip_earnings()
        if len(self.transactions) > 1:
            started = self.transactions[0].time
            now = time.time()
            return earned * 60.0 * 60.0 / (now - started)
        else:
            return 0.0

    def update_window(self):
        """Update our EDMC UI elements."""
        self.update_earned()
        self.update_transaction_rate()
        self.update_hourlyincome()

    def update_transaction_rate(self):
        """
        Set the transaction rate rate in the EDMC window.

        :param msg:
        """
        msg = f"{Locale.stringFromNumber(self.rate(), 2)} Visits/hr"
        self.rate_widget.after(0, self.rate_widget.config, {"text": msg})

    def update_hourlyincome(self):
        """
        Set the transaction speed rate in the EDMC window.

        :param msg:
        """
        msg = f"{Locale.stringFromNumber(self.speed(), 2)} Cr/hr"
        self.speed_widget.after(0, self.speed_widget.config, {"text": msg})

    def update_earned(self):
        """
        Set the transaction speed rate in the EDMC window.

        :param msg:
        """
        msg = f"{Locale.stringFromNumber(self.trip_earnings() + self.saved_earnings, 2)} Cr"
        self.earned_widget.after(0, self.earned_widget.config, {"text": msg})


def plugin_start3(plugin_dir: str):
    """Plugin start-up."""
    hourlyincome = HourlyIncome()
    hourlyincome.load()
    this.hourlyincome = hourlyincome
    # this.hourlyincome.transaction(0)


def plugin_app(parent):
    """Create a pair of TK widgets for the EDMC main window."""
    hourlyincome = this.hourlyincome

    frame = tk.Frame(parent)

    hourlyincome.rate_widget = tk.Label(
        frame,
        text="...",
        justify=tk.RIGHT)
    rate_label = tk.Label(frame, text="Station Visit Rate:", justify=tk.LEFT)
    rate_label.grid(row=0, column=0, sticky=tk.W)
    hourlyincome.rate_widget.grid(row=0, column=2, sticky=tk.E)

    hourlyincome.speed_widget = tk.Label(
        frame,
        text="...",
        justify=tk.RIGHT)
    speed_label = tk.Label(frame, text="Hourly Income:", justify=tk.LEFT)
    speed_label.grid(row=1, column=0, sticky=tk.W)
    hourlyincome.speed_widget.grid(row=1, column=2, sticky=tk.E)

    hourlyincome.earned_widget = tk.Label(
        frame,
        text="...",
        justify=tk.RIGHT)
    earned_label = tk.Label(frame, text="Total Income:", justify=tk.LEFT)
    earned_label.grid(row=2, column=0, sticky=tk.W)
    hourlyincome.earned_widget.grid(row=2, column=2, sticky=tk.E)

    reset_btn = tk.Button(frame, text="Reset", command=hourlyincome.reset)
    reset_btn.grid(row=2, column=1, sticky=tk.W)

    frame.columnconfigure(2, weight=1)

    this.spacer = tk.Frame(frame)
    hourlyincome.update_window()
    return frame


def journal_entry(cmdr, is_beta, system, station, entry, state):  # noqa: CCR001, C901
    """
    Process a journal event.

    :param cmdr:
    :param system:
    :param station:
    :param entry:
    :param state:
    :return:
    """
    if "event" in entry:
        #######################################################################
        # ! trading
        #######################################################################
        if "MarketSell" in entry["event"]:
            this.hourlyincome.transaction(entry["TotalSale"])

        elif "MarketBuy" in entry["event"]:
            this.hourlyincome.transaction(-entry["TotalCost"])

        elif "BuyTradeData" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        #######################################################################

        #######################################################################
        # ! refuel/repair/restock
        #######################################################################
        elif "BuyAmmo" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])

        elif "BuyDrones" in entry["event"]:
            this.hourlyincome.transaction(-entry["TotalCost"])

        elif "SellDrones" in entry["event"]:
            this.hourlyincome.transaction(entry["TotalSale"])

        elif "RefuelAll" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])

        elif "RefuelPartial" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])

        elif "Repair" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])

        elif "RepairAll" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])

        elif "RestockVehicle" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        #######################################################################

        #######################################################################
        # ! shipyard/outfitting/engineering
        #######################################################################
        elif "ModuleBuy" in entry["event"]:
            this.hourlyincome.transaction(-entry["Buyprice"])
            if "SellItem" in entry:
                this.hourlyincome.transaction(entry["SellPrice"])

        elif "ModuleSell" in entry["event"]:
            this.hourlyincome.transaction(entry["SellPrice"])

        elif "ModuleSellRemote" in entry["event"]:
            this.hourlyincome.transaction(entry["SellPrice"])

        elif "FetchRemoteModule" in entry["event"]:
            this.hourlyincome.transaction(-entry["TransferCost"])

        elif "ShipyardBuy" in entry["event"]:
            this.hourlyincome.transaction(-entry["ShipPrice"])
            if "SellOldShip" in entry:
                this.hourlyincome.transaction(entry["SellPrice"])

        elif "ShipyardSell" in entry["event"]:
            this.hourlyincome.transaction(entry["ShipPrice"])

        elif "ShipyardTransfer" in entry["event"]:
            this.hourlyincome.transaction(-entry["TransferPrice"])

        elif "EngineerContribution" in entry["event"] and "Credits" in entry["Type"]:
            this.hourlyincome.transaction(-entry["Quantity"])
        #######################################################################

        #######################################################################
        # ! fees
        #######################################################################
        elif "PayBounties" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])

        elif "PayFines" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])

        elif "PayLegacyFines" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])
        #######################################################################

        #######################################################################
        # ! combat
        #######################################################################
        elif "RedeemVoucher" in entry["event"]:
            this.hourlyincome.transaction(entry["Amount"])
        # ? These are probably logged upon award of bond/voucher and not upon
        # payment; Instead, RedeemVoucher is logged upon payment
        # elif "Bounty" in entry["event"]:
        #     this.hourlyincome.transaction(entry["TotalReward"])
        # elif "CapShipBond" in entry["event"]:
        #     this.hourlyincome.transaction(entry["Reward"])
        # elif "FactionKillBond" in entry["event"]:
        #     this.hourlyincome.transaction(entry["Reward"])
        #######################################################################

        #######################################################################
        # ! exploration
        #######################################################################
        elif "BuyExplorationData" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "SellExplorationData" in entry["event"]:
            this.hourlyincome.transaction(entry["TotalEarnings"])
        #######################################################################

        #######################################################################
        # ! missions/community goals/search and rescue
        #######################################################################
        elif "CommunityGoalReward" in entry["event"]:
            this.hourlyincome.transaction(entry["Reward"])
        elif "SearchAndRescue" in entry["event"]:
            this.hourlyincome.transaction(entry["Reward"])
        elif "MissionCompleted" in entry["event"]:
            if "Dontation" in entry:
                this.hourlyincome.transaction(-entry["Dontation"])
            else:
                this.hourlyincome.transaction(entry["Reward"])
        #######################################################################

        #######################################################################
        # ! npc crew
        #######################################################################
        elif "CrewHire" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "NpcCrewPaidWage" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])
        #######################################################################

        #######################################################################
        # ! rebuy
        #######################################################################
        elif "SellShipOnRebuy" in entry["event"]:
            this.hourlyincome.transaction(entry["ShipPrice"])
        elif "Resurrect" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        #######################################################################

        #######################################################################
        # ! powerplay
        #######################################################################
        elif "PowerplayFastTrack" in entry["event"]:
            this.hourlyincome.transaction(-entry["cost"])
        elif "PowerplaySalary" in entry["event"]:
            this.hourlyincome.transaction(entry["Amount"])
        #######################################################################

        #######################################################################
        # ! is_docking_event
        #######################################################################
        elif "Docked" in entry["event"]:
            this.hourlyincome.register_docking()
        #######################################################################


this = This()
