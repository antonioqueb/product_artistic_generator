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
        # 1. Generar Nombre en Mayúsculas
        artistic_name = vals.get('artistic_name', '').strip()
        finish = vals.get('finish', '').strip()
        thickness = vals.get('thickness', '').strip()
        
        full_name = f"{artistic_name} {finish} {thickness}".upper()

        # 2. Obtener la Unidad de Medida: Metros Cuadrados (m2)
        # El ID estándar en Odoo para m2 es uom.product_uom_m2
        uom_m2 = self.env.ref('uom.product_uom_m2', raise_if_not_found=False)
        
        if not uom_m2:
            # Búsqueda de respaldo si el ID externo no existe
            uom_m2 = self.env['uom.uom'].search([('name', 'ilike', 'm²')], limit=1)
        
        if not uom_m2:
            raise UserError(_("No se encontró la unidad de medida 'm²' en el sistema. Por favor, asegúrese de que el módulo de Unidades de Medida esté instalado."))

        # 3. Crear el producto usando sudo() para evitar errores de permisos en la UI
        # 'type': 'product' es indispensable para que el 'tracking': 'lot' sea válido.
        product_template = self.env['product.template'].sudo().create({
            'name': full_name,
            'type': 'consu',               # Bienes (Almacenable/Storable)
            'tracking': 'lot',               # Seguimiento por lote ACTIVO
            'categ_id': vals.get('category_id'),
            'uom_id': uom_m2.id,             # Unidad de medida m2
            'uom_po_id': uom_m2.id,          # Unidad de compra m2
            'purchase_method': 'purchase',   # Política: Sobre cantidades ordenadas
            'list_price': 0.0,
            'sale_ok': True,
            'purchase_ok': True,
        })

        return product_template.id