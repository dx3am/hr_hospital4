# -*- coding: utf-8 -*-
"""This file defines the Disease model."""

from odoo import models, fields


class Disease(models.Model):
    """
    Defines the Disease model for storing disease records.
    """
    _name = 'hr.hospital.disease'
    _description = 'Disease'
    _rec_name = 'name'

    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one(  # Ієрархія (на себе)
        comodel_name='hr.hospital.disease',
        string='Parent Disease',
        ondelete='restrict'
    )
    child_ids = fields.One2many(
        comodel_name='hr.hospital.disease',
        inverse_name='parent_id',
        string='Child Diseases'
    )
    code_icd10 = fields.Char(string='ICD-10 Code', size=10)
    danger_level = fields.Selection(
        selection=[
            ('low', 'Низький'),
            ('medium', 'Середній'),
            ('high', 'Високий'),
            ('critical', 'Критичний')
        ]
    )
    is_contagious = fields.Boolean(string='Contagious')
    symptoms = fields.Text()
    spread_region_ids = fields.Many2many(  # Зв'язок Many2many
        comodel_name='res.country',
        relation='disease_country_spread_rel',
        column1='disease_id',
        column2='country_id',
        string='Spread Region'
    )
