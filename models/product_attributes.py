from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductFinish(models.Model):
    _name = 'product.finish'
    _description = 'Acabado de Producto'
    _order = 'name'
    
    name = fields.Char(string='Nombre del Acabado', required=True)


class ProductThickness(models.Model):
    _name = 'product.thickness'
    _description = 'Espesor de Producto'
    _order = 'name'
    
    name = fields.Char(string='Nombre del Espesor', required=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create_artistic_product(self, vals):
        """
        Crea un producto basado en parámetros artísticos.
        Forzando: Mayúsculas, Unidad m2, Seguimiento por Lote y Tipo Almacenable.
        """
        artistic_name = vals.get('artistic_name', '').strip()
        finish = vals.get('finish', '').strip()
        thickness = vals.get('thickness', '').strip()
        
        full_name = f"{artistic_name} {finish} {thickness}".upper()

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