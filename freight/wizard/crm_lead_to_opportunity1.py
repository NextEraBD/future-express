# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    name = fields.Selection([
        ('convert', 'Convert to opportunity'),
        ('merge', 'Convert to contact')
    ], 'Conversion Action', compute='_compute_name', readonly=False, store=True, compute_sudo=False)
    action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ('nothing', 'Do not link to a customer')
    ], string='Related Customer', compute='_compute_action', readonly=False, store=True, compute_sudo=False)

    vat = fields.Char()

    def action_apply(self):
        if self.name == 'merge':
            self.action = 'create'
            self.lead_id._handle_partner_assignment(create_missing=True)
            convert = self.env['crm.lead'].search([('name', '=', self.lead_id.name)])
            convert['active'] = False

            result_opportunity = self._action_merge()
        else:
            result_opportunity = self._action_convert()

        return result_opportunity.redirect_lead_opportunity_view()

    def _action_merge(self):
        result_opportunities = self.env['crm.lead'].browse(self._context.get('active_ids', []))
        self._create_account_and_partner(result_opportunities, [self.user_id.id], team_id=self.team_id.id)
        return result_opportunities[0]

    def _action_convert(self):
        """ """
        result_opportunities = self.env['crm.lead'].browse(self._context.get('active_ids', []))
        self._convert_and_allocate(result_opportunities, [self.user_id.id], team_id=self.team_id.id)
        return result_opportunities[0]

    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner(
                    lead, self.action, self.partner_id.id or lead.partner_id.id)

            lead.convert_opportunity(lead.partner_id, user_ids=False, team_id=False)

        leads_to_allocate = leads
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate._handle_salesmen_assignment(user_ids, team_id=team_id)

    def _create_account_and_partner(self, leads, user_ids, team_id=False):
        self.ensure_one()
        for lead in leads:
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner(
                    lead, 'create', self.partner_id.id or lead.partner_id.id)

    def _convert_handle_partner(self, lead, action, partner_id):
        # used to propagate user_id (salesman) on created partners during conversion
        if self.vat:
            partner_id = self.env['res.partner'].search([('vat','=',self.vat)])
            if partner_id:
                raise ValidationError(_('Tax is already taken PLZ select another one'))
        lead.with_context(default_user_id=self.user_id.id)._handle_partner_assignment(
            force_partner_id=partner_id,
            create_missing=(action == 'create')
        )
        lead.partner_id.vat = self.vat


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _compute_opportunity_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        opportunity_data = self.env['crm.lead'].with_context(active_test=False)._read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('type', '=', 'opportunity')],
            fields=['partner_id'], groupby=['partner_id']
        )

        self.opportunity_count = 0
        for group in opportunity_data:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.opportunity_count += group['partner_id_count']
                partner = partner.parent_id

    def action_view_opportunity(self):
        '''
        This function returns an action that displays the opportunities from partner.
        '''
        action = self.env['ir.actions.act_window']._for_xml_id('crm.crm_lead_opportunities')
        action['context'] = {'active_test': False}
        if self.is_company:
            action['domain'] = [('partner_id.commercial_partner_id', '=', self.id), ('type', '=', 'opportunity')]
        else:
            action['domain'] = [('partner_id', '=', self.id), ('type', '=', 'opportunity')]
        return action