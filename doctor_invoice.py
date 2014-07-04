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
import time
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class doctor_invoice(osv.osv):
    _inherit = "account.invoice"
    _name = "account.invoice"

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_patient': 0.0,
                'amount_total': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_patient'] = invoice.amount_patient
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] - \
                                              res[invoice.id]['amount_patient']
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _columns = {
        'patient_id': fields.many2one('doctor.patient', "Patient"),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal',
                                          track_visibility='always',
                                          store={
                                              'account.invoice': (
                                              lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                                              'account.invoice.tax': (_get_invoice_tax, None, 20),
                                              'account.invoice.line': (_get_invoice_line,
                                                                       ['price_unit', 'invoice_line_tax_id', 'quantity',
                                                                        'discount', 'invoice_id'], 20),
                                          },
                                          multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
                                      store={
                                          'account.invoice': (
                                          lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                                          'account.invoice.tax': (_get_invoice_tax, None, 20),
                                          'account.invoice.line': (_get_invoice_line,
                                                                   ['price_unit', 'invoice_line_tax_id', 'quantity',
                                                                    'discount', 'invoice_id'], 20),
                                      },
                                      multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                                        store={
                                            'account.invoice': (
                                            lambda self, cr, uid, ids, c={}: ids, ['amount_patient'], 20),
                                            'account.invoice': (
                                            lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                                            'account.invoice.tax': (_get_invoice_tax, None, 20),
                                            'account.invoice.line': (_get_invoice_line,
                                                                     ['price_unit', 'invoice_line_tax_id', 'quantity',
                                                                      'discount', 'invoice_id'], 20),
                                        },
                                        multi='all'),
        'amount_patient': fields.float('Amount patient', digits_compute=dp.get_precision('Account'), readonly=True,
                                       states={'draft': [('readonly', False)]}),
        'amount_partner': fields.float('Amount partner', digits_compute=dp.get_precision('Account'), readonly=True,
                                       states={'draft': [('readonly', False)]}),
        'account_patient': fields.many2one('account.account', 'Account patient', readonly=True,
                                           states={'draft': [('readonly', False)]},
                                           help="The patient account used for this invoice."),
    }

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

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        if invoice_browse.amount_patient != 0:
            account = invoice_browse.account_patient.id
            total_patient = invoice_browse.amount_patient
            if not account:
                raise osv.except_osv(_('Warning!'), _('Please define the account for the patient.'))
            else:
                line = {
                    'name': invoice_browse.name or '/',
                    'partner_id': invoice_browse.patient_id.patient.id,
                    'journal_id': invoice_browse.journal_id.id,
                    'account_id': account,
                    'invoice': invoice_browse.id,
                    'debit': total_patient,
                    'credit': 0.0,
                    'quantity': 1,
                    'tax_amount': 0.0,
                    'amount_currency': 0,
                }
                move_lines.append((0, 0, line))
        return move_lines

    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id],
                           {'date_invoice': fields.date.context_today(self, cr, uid, context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = \
            self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (
                    inv.currency_id.rounding / 2.0)):
                    raise osv.except_osv(_('Bad Total!'), _(
                    'Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _(
                        "Cannot create the invoice.\nThe related payment term is probably misconfigured"
                        " as it gives a computed amount greater than the total invoiced amount. In order to"
                        " avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml,
                                                                     context=ctx)
            total_patient = inv.amount_patient
            total = total - total_patient
            acc_id = inv.account_id.id

            name = inv['name'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                                                    uid, inv.payment_term.id, total, inv.date_invoice or False,
                                                    context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1],
                                                          context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                           and amount_currency or False,
                        'currency_id': diff_currency_p \
                                       and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                                       and total_currency or False,
                    'currency_id': diff_currency_p \
                                   and inv.currency_id.id or False,
                    'ref': ref
                })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x: (0, 0, self.line_get_convert(cr, uid, x, part.id, date, context=ctx)), iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                                     _( 'You cannot create an invoice on a centralized journal. Uncheck the '
                                    'centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id, 'period_id': period_id, 'move_name': new_move_name},
                       context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True

    def invoice_pay_patient(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher',
                                                                             'view_vendor_receipt_dialog_form')

        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': _("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.patient_id.patient).id,
                'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.amount_patient or inv.amount_patient,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment'
            }
        }


doctor_invoice()