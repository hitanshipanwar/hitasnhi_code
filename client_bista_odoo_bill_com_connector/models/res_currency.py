# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Currency(models.Model):
    _inherit = "res.currency"

    def _convert(self, from_amount, to_currency, company, date, round=True):
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        to_amount = False
        if self == to_currency:
            to_amount = from_amount
        else:
            context = self._context.copy()
            new_currency_exchange_rate = context.get('currency_exchange_rate')
            if new_currency_exchange_rate and new_currency_exchange_rate > 0.0:
                to_amount = from_amount / new_currency_exchange_rate
            else:
                to_amount = from_amount * self._get_conversion_rate(self, to_currency, company, date)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

