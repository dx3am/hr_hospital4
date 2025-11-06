# -*- coding: utf-8 -*-
"""Defines the Reschedule Visit Wizard."""

from odoo import models, fields


class RescheduleVisitWizard(models.TransientModel):
    """Wizard for rescheduling an existing patient visit."""
    _name = 'reschedule.visit.wizard'
    _description = 'Reschedule Visit Wizard'

    visit_id = fields.Many2one(
        comodel_name='hr.hospital.patient.visit',
        readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )
    new_doctor_id = fields.Many2one('hr.hospital.doctor')
    new_date = fields.Datetime(required=True)
    reschedule_reason = fields.Text(required=True)

    def action_reschedule(self):
        """Reschedules the visit."""
        self.ensure_one()
        visit = self.visit_id

        # До скасування, щоб 'copy()' не скопіювала статус 'cancelled'
        new_visit = visit.copy({
            'visit_date': self.new_date,
            'doctor_id': self.new_doctor_id.id or visit.doctor_id.id,
            'status': 'planned',
            'actual_visit_date': False,
            'recommendations': f"<p>Перенесено з візиту: {visit.id}</p>"
        })

        visit.write({
            'status': 'cancelled',
            'recommendations': (visit.recommendations or '') +
                               f"<p>Перенесено на візит {new_visit.id}: "
                               f"{self.reschedule_reason}</p>"
        })

        return {'type': 'ir.actions.act_window_close'}
