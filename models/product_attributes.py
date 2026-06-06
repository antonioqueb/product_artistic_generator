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


class ProductDimension(models.Model):
    _name = 'product.dimension'
    _description = 'Dimensión de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Dimensión', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Marca Comercial de Producto'
    _order = 'sequence, name'

    name = fields.Char(string='Marca', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create_artistic_product(self, vals):
        """
        Crea un producto basado en parámetros.
        Forzando: Mayúsculas, Seguimiento por Lote y Tipo Almacenable.
        UdM y x_unidad_del_producto según tipo.
        """
        if not self.env.user.has_group('product_artistic_generator.group_product_generator'):
            raise UserError(_("No tiene permisos para generar productos."))

        commercial_name = vals.get('commercial_name', '').strip()
        finish = vals.get('finish', '').strip()
        thickness = vals.get('thickness', '').strip()
        dimension = vals.get('dimension', '').strip()
        color = vals.get('color', '').strip()
        marca = vals.get('marca', '').strip()
        origin_name = vals.get('origin_name', '').strip()
        supplier_id = vals.get('supplier_id')
        product_type = vals.get('product_type', '')

        # Construir nombre según tipo
        if product_type == 'pieza':
            # Pieza: solo NOMBRE_COMERCIAL - MARCA (sin palabra de tipo)
            full_name = commercial_name.upper()
        else:
            # Placas y formatos: NOMBRE_COMERCIAL ACABADO DIMENSION [PLACA] ESPESOR
            parts = [commercial_name, finish]
            if dimension:
                parts.append(dimension)
            # Solo las placas llevan la palabra "PLACA" en el nombre, justo
            # antes del grosor. Los formatos no añaden palabra de tipo.
            if product_type in ('placa_natural', 'placa_sintetica'):
                parts.append('PLACA')
            parts.append(thickness)
            full_name = ' '.join(p for p in parts if p).upper()

        # Limpiar espacios múltiples
        full_name = ' '.join(full_name.split())

        # Agregar marca con separador guion
        if marca:
            full_name = f"{full_name} - {marca.upper()}"

        # Verificar que no exista un producto con el mismo nombre
        existing = self.env['product.template'].sudo().search([
            ('name', '=ilike', full_name)
        ], limit=1)
        if existing:
            raise UserError(_(
                "Ya existe un producto con el nombre '%(name)s' (ID: %(id)s). "
                "No se puede crear un producto duplicado.",
                name=full_name, id=existing.id
            ))

        # Determinar UdM según tipo
        if product_type == 'pieza':
            uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            if not uom:
                uom = self.env['uom.uom'].search([('name', 'ilike', 'Unidades')], limit=1)
            if not uom:
                raise UserError(_("No se encontró la unidad de medida 'Unidades' en el sistema."))
        else:
            uom = self.env.ref('uom.product_uom_m2', raise_if_not_found=False)
            if not uom:
                uom = self.env['uom.uom'].search([('name', 'ilike', 'm²')], limit=1)
            if not uom:
                raise UserError(_("No se encontró la unidad de medida 'm²' en el sistema."))

        # Determinar x_unidad_del_producto
        unidad_map = {
            'placa_natural': 'Placa',
            'placa_sintetica': 'Placa',
            'formato': 'Formato',
            'pieza': 'Pieza',
        }

        product_vals = {
            'name': full_name,
            'is_storable': True,
            'tracking': 'lot',
            'categ_id': vals.get('category_id'),
            'uom_id': uom.id,
            'purchase_method': 'purchase',
            'list_price': 0.0,
            'sale_ok': True,
            'purchase_ok': True,
        }

        # Propagar los atributos a los campos de product.template definidos en
        # el módulo stock_lot_dimensions (pestaña "Atributos"). Cada campo se
        # escribe solo si existe en el modelo, para no romper si ese módulo no
        # estuviera instalado.
        tmpl_fields = self.env['product.template']._fields

        # Unidad del Producto: SIEMPRE se llena según el tipo
        # (Placa / Formato / Pieza).
        unidad_valor = unidad_map.get(product_type, '')
        if unidad_valor and 'x_unidad_del_producto' in tmpl_fields:
            product_vals['x_unidad_del_producto'] = unidad_valor

        # Color Estándar (no aplica a pieza)
        if color and product_type != 'pieza' and 'x_color' in tmpl_fields:
            product_vals['x_color'] = color.upper()

        # Marca Comercial
        if marca and 'x_marca' in tmpl_fields:
            product_vals['x_marca'] = marca.upper()

        # Acabado Superficial (no aplica a pieza)
        if finish and product_type != 'pieza' and 'x_acabado' in tmpl_fields:
            product_vals['x_acabado'] = finish.upper()

        # Grosor Nominal (no aplica a pieza)
        if thickness and product_type != 'pieza' and 'x_grosor' in tmpl_fields:
            product_vals['x_grosor'] = thickness.upper()

        # Dimensiones = dimensión + grosor (no aplica a pieza)
        if product_type != 'pieza' and 'x_dimensiones' in tmpl_fields:
            dim_parts = [p for p in (dimension, thickness) if p]
            if dim_parts:
                product_vals['x_dimensiones'] = ' '.join(dim_parts).upper()

        product_template = self.env['product.template'].sudo().create(product_vals)

        # Crear nombre de origen si se proporcionó y el modelo existe
        if origin_name and 'product.origin.name' in self.env:
            origin_vals = {
                'name': origin_name,
                'product_tmpl_id': product_template.id,
                'sequence': 10,
            }
            if supplier_id:
                origin_vals['partner_id'] = supplier_id
            self.env['product.origin.name'].sudo().create(origin_vals)

        return product_template.id