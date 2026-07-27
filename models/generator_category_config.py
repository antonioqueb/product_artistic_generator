from odoo import models, fields, api, _


class GeneratorCategoryConfig(models.Model):
    _name = 'generator.category.config'
    _description = 'Configuración de Categorías por Tipo de Producto'
    _order = 'product_type'

    product_type = fields.Selection([
        ('placa_natural', 'Placa Natural'),
        ('placa_sintetica', 'Placa Sintética'),
        ('formato', 'Formato'),
        ('pieza', 'Pieza'),
    ], string='Tipo de Producto', required=True)
    category_ids = fields.Many2many(
        'product.category',
        'generator_config_category_rel',
        'config_id',
        'category_id',
        string='Categorías Disponibles',
    )

    # Odoo 19: models.Constraint reemplaza a _sql_constraints (que ya no se
    # aplica).
    _product_type_unique = models.Constraint(
        'unique(product_type)',
        'Ya existe una configuración para este tipo de producto.',
    )

    @api.model
    def get_categories_for_type(self, product_type):
        """Retorna las categorías configuradas para un tipo de producto."""
        config = self.search([('product_type', '=', product_type)], limit=1)
        if not config:
            return []
        return [{
            'id': c.id,
            'display_name': c.display_name,
            'short_name': c.display_name.split(' / ')[-1],
        } for c in config.category_ids]