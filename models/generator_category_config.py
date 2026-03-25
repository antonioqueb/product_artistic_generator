from odoo import models, fields, api, _


class GeneratorCategoryConfig(models.Model):
    _name = 'generator.category.config'
    _description = 'Configuración de Categorías por Tipo de Producto'
    _order = 'product_type, sequence'

    product_type = fields.Selection([
        ('placa_natural', 'Placa Natural'),
        ('placa_sintetica', 'Placa Sintética'),
        ('formato', 'Formato'),
    ], string='Tipo de Producto', required=True)
    category_id = fields.Many2one('product.category', string='Categoría', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)

    _sql_constraints = [
        ('type_category_unique', 'unique(product_type, category_id)',
         'Esta categoría ya está configurada para este tipo de producto.')
    ]

    @api.model
    def get_categories_for_type(self, product_type):
        """Retorna las categorías configuradas para un tipo de producto."""
        configs = self.search([('product_type', '=', product_type)])
        return [{
            'id': c.category_id.id,
            'display_name': c.category_id.display_name,
            'short_name': c.category_id.display_name.split(' / ')[-1],
        } for c in configs]