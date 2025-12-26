from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductFinish(models.Model):
    _name = 'product.finish'
    _description = 'Acabado de Producto'
    _order = 'sequence, name'
    
    name = fields.Char(string='Nombre del Acabado', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductThickness(models.Model):
    _name = 'product.thickness'
    _description = 'Espesor de Producto'
    _order = 'sequence, name'
    
    name = fields.Char(string='Nombre del Espesor', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductGenericName(models.Model):
    _name = 'product.generic.name'
    _description = 'Nombre Genérico de Producto'
    _order = 'sequence, name'
    
    name = fields.Char(string='Nombre Genérico', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductDimension(models.Model):
    _name = 'product.dimension'
    _description = 'Dimensión de Producto'
    _order = 'sequence, name'
    
    name = fields.Char(string='Dimensión', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create_artistic_product(self, vals):
        """
        Crea un producto basado en parámetros artísticos.
        Forzando: Mayúsculas, Unidad m2, Seguimiento por Lote y Tipo Almacenable.
        """
        artistic_name = vals.get('artistic_name', '').strip()
        generic_name = vals.get('generic_name', '').strip()
        finish = vals.get('finish', '').strip()
        thickness = vals.get('thickness', '').strip()
        dimension = vals.get('dimension', '').strip()
        
        # Construir nombre según tipo
        if dimension:
            full_name = f"{generic_name} {artistic_name} {finish} {thickness} {dimension}".upper()
        else:
            full_name = f"{generic_name} {artistic_name} {finish} {thickness}".upper()
        
        # Limpiar espacios múltiples
        full_name = ' '.join(full_name.split())

        uom_m2 = self.env.ref('uom.product_uom_m2', raise_if_not_found=False)
        if not uom_m2:
            uom_m2 = self.env['uom.uom'].search([('name', 'ilike', 'm²')], limit=1)
        
        if not uom_m2:
            raise UserError(_("No se encontró la unidad de medida 'm²' en el sistema."))

        product_template = self.env['product.template'].sudo().create({
            'name': full_name,
            'is_storable': True,
            'tracking': 'lot',
            'categ_id': vals.get('category_id'),
            'uom_id': uom_m2.id,
            'purchase_method': 'purchase',
            'list_price': 0.0,
            'sale_ok': True,
            'purchase_ok': True,
        })

        return product_template.id