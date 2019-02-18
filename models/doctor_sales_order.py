# -*- coding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class doctor_sales_order(models.Model):
    _inherit = "sale.order"
    _name = "sale.order"

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
                                                          line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                                                          line.product_uom_qty, line.product_id,
                                                          line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val


    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_patient': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_patient'] = order.amount_patient
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] - \
                                            res[order.id]['amount_patient']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    patient_id = fields.Many2one('doctor.patient', "Patient")
    amount_untaxed = fields.Float(compute='_amount_all', digits_compute=dp.get_precision('Account'),
                                      string='Untaxed Amount',
                                      store={
                                          'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                          'sale.order.line': (
                                              _get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                      },
                                      multi='sums', help="The amount without tax.", track_visibility='always')
    amount_tax = fields.Float(compute='_amount_all', digits_compute=dp.get_precision('Account'), string='Taxes',
                                  store={
                                      'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                      'sale.order.line': (
                                          _get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                  },
                                  multi='sums', help="The tax amount.")
    amount_total = fields.Float(compute='_amount_all', digits_compute=dp.get_precision('Account'), string='Total',
                                    store={
                                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                        'sale.order': (
                                            lambda self, cr, uid, ids, c={}: ids, ['amount_patient'], 10),
                                        'sale.order.line': (
                                            _get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                    },
                                    multi='sums', help="The total amount.")
    amount_patient = fields.Float('Amount patient', digits_compute=dp.get_precision('Account'), readonly=True,
                                   states={'draft': [('readonly', False)]})
    amount_partner = fields.Float('Amount partner', digits_compute=dp.get_precision('Account'), readonly=True,
                                   states={'draft': [('readonly', False)]})

    def onchange_amount_patient(self, cr, uid, ids, amount_untaxed, amount_tax, amount_patient, context=None):
        values = {}
        if not amount_patient:
            return values
        total_invoice = amount_untaxed
        total_tax = amount_tax
        total_patient = amount_patient
        total_partner = total_invoice + total_tax - total_patient
        values.update({
            'amount_total': total_partner,
        })
        return {'value': values}

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
                                                              [('type', '=', 'sale'),
                                                               ('company_id', '=', order.company_id.id)],
                                                              limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                                 _('Please define sales journal for this company: "%s" (id:%d).') % (
                                 order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'account_patient': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'patient_id': order.patient_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'amount_patient': order.amount_patient,
            #~ 'amount_partner':  order.amount_partner,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals


doctor_sales_order()
