# -*- coding: utf-8 -*-
"""Defines the Disease Report Wizard."""

from odoo import models, fields, api, _


class DiseaseReportWizard(models.TransientModel):
    """Wizard for generating a filtered list of diagnoses."""
    _name = 'disease.report.wizard'
    _description = 'Disease Report Wizard'

    @api.model
    def _get_default_doctors(self):
        """Get default doctor(s) if action is called from doctor form/tree."""
        if self.env.context.get('active_model') == 'hr.hospital.doctor':
            return self.env.context.get('active_ids')
        return False

    doctor_ids = fields.Many2many(
        'hr.hospital.doctor',
        default=lambda self: self._get_default_doctors()
    )
    disease_ids = fields.Many2many('hr.hospital.disease')
    country_ids = fields.Many2many('res.country')
    date_start = fields.Date(required=True, default=fields.Date.today)
    date_end = fields.Date(required=True, default=fields.Date.today)
    report_type = fields.Selection(
        selection=[('detailed', 'Детальний'), ('summary', 'Підсумковий')],
        default='detailed', required=True
    )
    group_by = fields.Selection(
        selection=[
            ('doctor', 'Лікарем'),
            ('disease', 'Хворобою'),
            ('month', 'Місяцем'),
            ('country', 'Країною')
        ]
    )

    def action_generate_report(self):
        """
        Повертає список діагнозів за критеріями.
        'action', який відкриє відфільтрований список діагнозів.
        """
        self.ensure_one()

        domain = [
            ('visit_id.visit_date', '>=', self.date_start),
            ('visit_id.visit_date', '<=', self.date_end),
        ]
        if self.doctor_ids:
            domain.append(('visit_id.doctor_id', 'in', self.doctor_ids.ids))
        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))
        if self.country_ids:
            domain.append(('visit_id.patient_id.country_id', 'in',
                           self.country_ids.ids))

        action_context = {
            'group_by': 'disease_id',
            'domain': domain
        }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Disease Report'),
            'res_model': 'medical.diagnosis',
            'view_mode': 'tree,form,pivot,graph',
            'domain': domain,
            'context': action_context,
            'target': 'current',
        }
