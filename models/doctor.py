# -*- coding: utf-8 -*-
"""This file defines the Doctor model."""

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class Doctor(models.Model):
    """Model for storing doctor records."""
    _name = 'hr.hospital.doctor'
    _inherit = ['abstract.person']  # Наслідування абстрактної моделі
    _description = 'Doctor'
    display_name = fields.Char(compute='_compute_display_name', store=False)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='System User')
    specialty_id = fields.Many2one(
        comodel_name='doctor.speciality',
        string='Speciality')
    is_intern = fields.Boolean(string='Intern')
    mentor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Mentor',
        domain="[('is_intern', '=', False)]"
    )
    license_number = fields.Char(required=True, copy=False)
    license_date = fields.Date()
    experience_years = fields.Integer(
        compute='_compute_experience_years',
        string='Experience (Years)'
    )
    rating = fields.Float(digits=(3, 2))
    schedule_ids = fields.One2many(
        comodel_name='doctor.schedule',
        inverse_name='doctor_id',
        string='Work Schedule'
    )
    study_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country of Study')

    intern_ids = fields.One2many(
        comodel_name='hr.hospital.doctor',
        inverse_name='mentor_id',
        string='Interns'
    )

    _sql_constraints = [  # Валідатор SQL
        ('license_number_uniq',
         'unique(license_number)',
         'License number must be unique!'),
        ('rating_check',
         'CHECK(rating >= 0 AND rating <= 5)',
         'Rating must be between 0.00 and 5.00.'),
    ]

    @api.constrains('is_intern', 'mentor_id')  # Валідатор Python
    def _check_mentor_is_not_intern(self):
        """Validator: An intern cannot be selected as a mentor."""
        for record in self:
            if record.mentor_id and record.mentor_id.is_intern:
                raise ValidationError(self.env._("An intern cannot be a mentor."))

    @api.constrains('mentor_id')  # Валідатор Python
    def _check_mentor_not_self(self):
        """Validator: A doctor cannot be their own mentor."""
        for record in self:
            if record.mentor_id and record.mentor_id == record:
                raise ValidationError(self.env._("A doctor cannot be their own mentor."))

    @api.depends('license_date')  # Обчислювальне поле
    def _compute_experience_years(self):
        """Computes the doctor's experience based on license issue date."""
        for record in self:
            if record.license_date and record.license_date <= fields.Date.today():
                record.experience_years = \
                    (fields.Date.today() - record.license_date).days // 365
            else:
                record.experience_years = 0

    @api.onchange('is_intern')  # Onchange
    def _onchange_is_intern(self):
        """If a doctor is set as 'not an intern', clear mentor."""
        if not self.is_intern:
            self.mentor_id = False

    @api.depends('full_name', 'specialty_id.name')
    def _compute_display_name(self):
        """Computes the display name to show 'Name (Speciality)'."""
        for record in self:
            name = record.full_name
            if record.specialty_id:
                name = f"{name} ({record.specialty_id.name})"
            record.display_name = name

    def action_archive(self):  # Override
        """Check for active visits before archiving."""
        active_visits = self.env['hr.hospital.patient.visit'].search([
            ('doctor_id', 'in', self.ids),
            ('status', '=', 'planned')
        ])
        if active_visits:
            raise ValidationError(
                self.env._("Cannot archive doctors with planned visits."))
        return super().action_archive()

    def action_view_patients_by_language(self):
        """
        Повертає дію для відкриття списку пацієнтів,
        які розмовляють тією ж мовою, що і лікар.
        """
        self.ensure_one()

        if not self.language_id:
            raise UserError(self.env._("У цього лікаря не вказана мова спілкування."))

        domain = [('language_id', '=', self.language_id.id)]

        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Пацієнти (%s)', self.language_id.name),
            'res_model': 'hr.hospital.patient',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'default_language_id': self.language_id.id
            }
        }

    def action_create_new_visit(self):
        """Button action for Kanban to create a new visit."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('New Visit'),
            'res_model': 'hr.hospital.patient.visit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_doctor_id': self.id,
            }
        }
