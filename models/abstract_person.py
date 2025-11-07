# -*- coding: utf-8 -*-
"""Defines the Abstract Person model."""

import re
from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AbstractPerson(models.AbstractModel):
    """Abstract model for a person."""
    _name = 'abstract.person'
    _description = 'Abstract Person'
    _inherit = ['image.mixin']

    first_name = fields.Char(required=True)
    last_name = fields.Char(required=True)
    middle_name = fields.Char()
    full_name = fields.Char(
        compute='_compute_full_name',
        store=True
    )

    name = fields.Char(
        string='Name (Internal)',
        related='full_name',
        store=False,
        readonly=True
    )

    phone = fields.Char()
    email = fields.Char()
    gender = fields.Selection(
        selection=[
            ('male', 'Чоловік'),
            ('female', 'Жінка'),
            ('other', 'Інше'),
        ]
    )
    birthday = fields.Date()
    age = fields.Integer(
        compute='_compute_age',
        store=True
    )
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country of Citizenship'
    )
    language_id = fields.Many2one(
        comodel_name='res.lang',
        string='Communication Language'
    )

    @api.depends('birthday')
    def _compute_age(self):
        """Computes the age based on birthday."""
        for record in self:
            if record.birthday:
                today = date.today()
                record.age = today.year - record.birthday.year - \
                             ((today.month, today.day) <
                              (record.birthday.month, record.birthday.day))
            else:
                record.age = 0

    @api.depends('first_name', 'last_name', 'middle_name')
    def _compute_full_name(self):
        """Concatenates name fields into a full name."""
        for record in self:
            parts = [record.last_name, record.first_name, record.middle_name]
            record.full_name = ' '.join(part for part in parts if part)

    @api.constrains('birthday')  # Валідатор Python
    def _check_age(self):
        """Validator: Ensures age is positive."""
        for record in self:
            if record.birthday and record.birthday > fields.Date.today():
                raise ValidationError(_("Birthday cannot be in the future!"))

    @api.constrains('phone')  # Валідатор Python
    def _check_phone(self):
        """Validator: Ensures phone format is (somewhat) valid."""
        for record in self:
            if record.phone and not re.match(r'^\+?[\d\s\-\(\)]{7,20}$',
                                             record.phone):
                raise ValidationError(_("Invalid phone number format."))

    @api.onchange('country_id')
    def _onchange_country_set_lang(self):
        """Suggests the country's language when citizenship is changed."""
        if self.country_id:
            lang = self.env['res.lang'].search([
                ('country_id', '=', self.country_id.id)
            ], limit=1)
            self.language_id = lang.id if lang else False
        else:
            self.language_id = False
