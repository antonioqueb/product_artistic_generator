from odoo import models, fields, api

class ProductFinish(models.Model):
    _name = 'product.finish'
    _description = 'Acabado de Producto'
    name = fields.Char(string='Nombre del Acabado', required=True)

class ProductThickness(models.Model):
    _name = 'product.thickness'
    _description = 'Espesor de Producto'
    name = fields.Char(string='Nombre del Espesor', required=True)

class ProductArtisticName(models.Model):
    _name = 'product.artistic.name'
    _description = 'Nombres Artísticos Base'
    name = fields.Char(string='Nombre Base', required=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create_artistic_product(self, vals):
        # Lógica de creación forzando mayúsculas y políticas
        name = f"{vals['artistic_name']} {vals['base_name']} {vals['finish']} {vals['thickness']}".upper()
        
        product_vals = {
            'name': name,
            'type': 'product', # Bienes (Almacenable)
            'tracking': 'lot', # Rastreo por lotes
            'categ_id': vals['category_id'],
            'purchase_method': 'purchase', # Cantidades recibidas/ordenadas
            'list_price': 1.0,
        }
        return self.create(product_vals).id
