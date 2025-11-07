# -*- coding: utf-8 -*-
"""This file defines the Patient Visit model."""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PatientVisit(models.Model):
    """
    Model for storing patient visits.
    """
    _name = 'hr.hospital.patient.visit'
    _description = 'Patient Visit'
    _order = 'visit_date desc'
    display_name = fields.Char(compute='_compute_display_name', store=False)

    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
        domain="[('license_number', '!=', False)]"
    )

    is_intern_doctor = fields.Boolean(
        related='doctor_id.is_intern',
        string='Is Intern',
        store=False
    )
    mentor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Attending Mentor',
        readonly=True
    )

    status = fields.Selection(
        selection=[
            ('planned', 'Заплановано'),
            ('completed', 'Завершено'),
            ('cancelled', 'Скасовано'),
            ('missed', 'Не з\'явився')
        ],
        default='planned',
        required=True,
    )
    visit_date = fields.Datetime(
        string='Planned Visit Date',
        required=True,
        default=fields.Datetime.now
    )
    actual_visit_date = fields.Datetime(
        readonly=True
    )
    visit_type = fields.Selection(
        selection=[
            ('primary', 'Первинний'),
            ('repeat', 'Повторний'),
            ('preventive', 'Профілактичний'),
            ('urgent', 'Невідкладний')
        ],
        default='primary',
        required=True,
    )
    recommendations = fields.Html()
    diagnosis_ids = fields.One2many(  # Зв'язок One2many
        comodel_name='medical.diagnosis',
        inverse_name='visit_id',
        string='Diagnoses'
    )

    diagnosis_count = fields.Integer(
        string='Кількість діагнозів',
        compute='_compute_diagnosis_count',
        store=True
    )

    # Грошові поля
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    cost = fields.Monetary(currency_field='currency_id')

    @api.depends('diagnosis_ids')
    def _compute_diagnosis_count(self):
        """Обчислює кількість діагнозів, пов'язаних з цим візитом."""
        for visit in self:
            visit.diagnosis_count = len(visit.diagnosis_ids)

    @api.onchange('doctor_id')
    def _onchange_doctor_id_set_mentor(self):
        """Якщо обраний лікар - інтерн, автоматично заповнити його ментора."""
        if self.doctor_id and self.doctor_id.is_intern:
            self.mentor_id = self.doctor_id.mentor_id
        else:
            self.mentor_id = False

    @api.constrains('patient_id', 'doctor_id', 'visit_date')
    def _check_unique_visit_per_day(self):
        """Validator: Prohibit one patient from visiting one doctor > 1 time/day."""
        for visit in self:
            # Datetime в Date
            visit_day = fields.Date.context_today(visit, visit.visit_date)

            # Пошук "дублікатів"
            domain = [
                ('patient_id', '=', visit.patient_id.id),
                ('doctor_id', '=', visit.doctor_id.id),
                ('id', '!=', visit.id),
                ('visit_date', '>=', f'{visit_day} 00:00:00'),
                ('visit_date', '<=', f'{visit_day} 23:59:59'),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_(
                    "This patient already has a visit with this doctor "
                    "on the same day."))

    def write(self, vals):
        """Overrides write to prevent changes if the visit is completed."""
        for record in self:
            # Заборона зміни візиту, що вже відбувся
            if record.status == 'completed' and \
                    any(field in vals for field in
                        ['doctor_id', 'patient_id', 'visit_date']):
                raise ValidationError(_(
                    "Cannot change date, doctor, or patient "
                    "on a completed visit."))

            # Оновлення 'actual_visit_date', коли статус стає 'completed'
            if vals.get('status') == 'completed' and \
                    not record.actual_visit_date:
                vals['actual_visit_date'] = fields.Datetime.now()

        return super().write(vals)

    @api.depends('patient_id.full_name', 'visit_date')
    def _compute_display_name(self):
        """Computes the display name to show 'Patient Name @ Visit Date'."""
        for visit in self:
            patient_name = visit.patient_id.full_name if visit.patient_id \
                else _("Unknown Patient")

            visit_date_str = ''
            if visit.visit_date:
                visit_date_local = fields.Datetime.context_timestamp(
                    self, visit.visit_date
                )
                visit_date_str = visit_date_local.strftime('%Y-%m-%d %H:%M')

            visit.display_name = f"{patient_name} @ {visit_date_str}"
