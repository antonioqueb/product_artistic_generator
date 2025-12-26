from odoo import models, fields, api

class ProductFinish(models.Model):
    _name = 'product.finish'
    _description = 'Acabado'
    _order = 'name'
    name = fields.Char(string='Acabado', required=True)

class ProductThickness(models.Model):
    _name = 'product.thickness'
    _description = 'Espesor'
    _order = 'name'
    name = fields.Char(string='Espesor', required=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create_artistic_product(self, vals):
        # Concatenación y MAYÚSCULAS
        full_name = f"{vals['artistic_name']} {vals['finish']} {vals['thickness']}".upper()
        
        return self.create({
            'name': full_name,
            'type': 'product',           # Bienes (Almacenable)
            'tracking': 'lot',           # Rastreo por lotes
            'categ_id': vals['category_id'],
            'purchase_method': 'purchase', # Facturas sobre cantidades ordenadas
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'list_price': 0.0,
        }).id