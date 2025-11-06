# -*- coding: utf-8 -*-
"""Defines the Patient Card Export Wizard."""

import base64
import json
import csv
import io

from odoo import models, fields, api
from odoo.exceptions import UserError


class PatientCardExportWizard(models.TransientModel):
    """Wizard for exporting a patient's medical card."""
    _name = 'patient.card_export_wizard'
    _description = 'Patient Card Export Wizard'

    patient_id = fields.Many2one('hr.hospital.patient', required=True)
    date_start = fields.Date()
    date_end = fields.Date()
    include_diagnoses = fields.Boolean(default=True)
    include_recommendations = fields.Boolean(default=True)
    language_id = fields.Many2one(
        comodel_name='res.lang',
        default=lambda self: self.env.user.lang_id
    )
    export_format = fields.Selection(
        selection=[('json', 'JSON'), ('csv', 'CSV')],
        default='json', required=True
    )

    file_name = fields.Char()
    file_data = fields.Binary(string='File to Download', readonly=True)

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id and self.patient_id.language_id:
            self.language_id = self.patient_id.language_id

    def _prepare_export_data(self):
        """Data for export."""
        self.ensure_one()
        visit_domain = [('patient_id', '=', self.patient_id.id)]
        if self.date_start:
            visit_domain.append(('visit_date', '>=', self.date_start))
        if self.date_end:
            visit_domain.append(('visit_date', '<=', self.date_end))

        visits = self.env['hr.hospital.patient.visit'].search(visit_domain)

        patient_data = self.patient_id.read(
            ['full_name', 'birthday', 'age', 'blood_type', 'allergies']
        )
        export_data = {
            'patient_info': patient_data[0] if patient_data else {},
            'visits': []
        }

        for visit in visits:
            visit_data = {
                'visit_info': visit.read(
                    ['visit_date', 'status', 'cost', 'actual_visit_date']
                )[0],
                'doctor': visit.doctor_id.display_name,
            }
            if self.include_diagnoses:
                diag_data = visit.diagnosis_ids.read(
                    ['disease_id', 'description', 'treatment', 'severity']
                )
                visit_data['diagnoses'] = diag_data

            if self.include_recommendations:
                visit_data['recommendations'] = visit.recommendations

            export_data['visits'].append(visit_data)

        return export_data

    def action_export_card(self):
        """
        'file_data' and 'file_name'.
        """
        self.ensure_one()
        export_data = self._prepare_export_data()

        file_content = False
        file_name = f"patient_card_{self.patient_id.id}_{fields.Date.today()}.{self.export_format}"

        if self.export_format == 'json':
            # JSON
            file_content = json.dumps(
                export_data,
                indent=2,
                ensure_ascii=False,
                default=str
            ).encode('utf-8')

        elif self.export_format == 'csv':
            # CSV
            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow([
                'Patient', 'VisitDate', 'Doctor',
                'Diagnosis', 'Severity', 'Description', 'Treatment'
            ])

            # Дані
            for visit in export_data['visits']:
                visit_info = visit['visit_info']
                if not visit.get('diagnoses'):
                    writer.writerow([
                        export_data['patient_info'].get('full_name', 'N/A'),
                        visit_info.get('visit_date', 'N/A'),
                        visit.get('doctor', 'N/A'),
                        'N/A', 'N/A', 'N/A', 'N/A'
                    ])
                else:
                    for diag in visit['diagnoses']:
                        writer.writerow([
                            export_data['patient_info'].get('full_name', 'N/A'),
                            visit_info.get('visit_date', 'N/A'),
                            visit.get('doctor', 'N/A'),
                            diag['disease_id'][1] if diag.get('disease_id') else 'N/A',
                            diag.get('severity', 'N/A'),
                            diag.get('description', 'N/A'),
                            diag.get('treatment', 'N/A')
                        ])
            file_content = output.getvalue().encode('utf-8')

        if not file_content:
            raise UserError(self.env._("Неможливо згенерувати файл."))

        self.write({
            'file_data': base64.b64encode(file_content),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
