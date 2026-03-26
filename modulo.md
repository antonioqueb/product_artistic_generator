## ./__init__.py
```py
from . import models
```

## ./__manifest__.py
```py
{
    'name': 'Generador de Productos',
    'version': '1.2',
    'category': 'Inventory',
    'summary': 'Interfaz dinámica para creación de productos con lógica de ramificación',
    'description': """
Generador de Productos
==========================================================================
Módulo avanzado para la creación dinámica de productos basados en atributos.
    """,
    'author': 'Alphaqueb Consulting',
    'website': 'https://www.alphaqueb.com',
    'license': 'AGPL-3',

    'depends': ['base', 'stock', 'purchase', 'product'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_attribute_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_artistic_generator/static/src/components/product_generator/product_generator.js',
            'product_artistic_generator/static/src/components/product_generator/product_generator.xml',
            'product_artistic_generator/static/src/components/product_generator/product_generator.scss',
        ],
    },
    'installable': True,
    'application': True,
}```

## ./models/__init__.py
```py
from . import product_attributes
from . import generator_category_config```

## ./models/generator_category_config.py
```py
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

    _sql_constraints = [
        ('product_type_unique', 'unique(product_type)',
         'Ya existe una configuración para este tipo de producto.')
    ]

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
        } for c in config.category_ids]```

## ./models/product_attributes.py
```py
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
            # Pieza: solo NOMBRE_COMERCIAL - MARCA
            full_name = commercial_name.upper()
        else:
            # Placas y formatos: NOMBRE_COMERCIAL ACABADO DIMENSION ESPESOR
            parts = [commercial_name, finish]
            if dimension:
                parts.append(dimension)
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

        # Escribir x_unidad_del_producto si el campo existe
        unidad_valor = unidad_map.get(product_type, '')
        if unidad_valor and 'x_unidad_del_producto' in self.env['product.template']._fields:
            product_vals['x_unidad_del_producto'] = unidad_valor

        # Escribir x_color si el campo existe y se proporcionó valor (no aplica a pieza)
        if color and product_type != 'pieza' and 'x_color' in self.env['product.template']._fields:
            product_vals['x_color'] = color.upper()

        # Escribir x_marca si el campo existe y se proporcionó valor
        if marca and 'x_marca' in self.env['product.template']._fields:
            product_vals['x_marca'] = marca.upper()

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

        return product_template.id```

## ./security/security.xml
```xml
<odoo>
    <record id="group_product_generator" model="res.groups">
        <field name="name">Generador de Productos</field>
    </record>
</odoo>```

## ./static/src/components/product_generator/product_generator.js
```js
/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ArtisticGenerator extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            step: 1,
            productType: null,
            finishes: [],
            thicknesses: [],
            dimensions: [],
            suppliers: [],
            brands: [],
            filteredFinishes: [],
            filteredThicknesses: [],
            filteredDimensions: [],
            filteredSuppliers: [],
            filteredBrands: [],
            showFinishDropdown: false,
            showThicknessDropdown: false,
            showDimensionDropdown: false,
            showSupplierDropdown: false,
            showBrandDropdown: false,
            finishSearch: '',
            thicknessSearch: '',
            dimensionSearch: '',
            supplierSearch: '',
            brandSearch: '',
            subCategories: [],
            selection: {
                commercial_name: '',
                origin_name: '',
                color: '',
                brand_id: null,
                finish_id: null,
                thickness_id: null,
                dimension_id: null,
                supplier_id: null,
                category_id: null
            }
        });

        onWillStart(async () => {
            this.state.finishes = await this.orm.searchRead("product.finish", [], ["name"]);
            this.state.thicknesses = await this.orm.searchRead("product.thickness", [], ["name"]);
            this.state.dimensions = await this.orm.searchRead("product.dimension", [], ["name"]);
            this.state.suppliers = await this.orm.searchRead("res.partner", [['supplier_rank', '>', 0]], ["name"]);
            this.state.brands = await this.orm.searchRead("product.brand", [], ["name"]);
            this.state.filteredFinishes = [...this.state.finishes];
            this.state.filteredThicknesses = [...this.state.thicknesses];
            this.state.filteredDimensions = [...this.state.dimensions];
            this.state.filteredSuppliers = [...this.state.suppliers];
            this.state.filteredBrands = [...this.state.brands];
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.o_searchable_select')) {
                this.state.showFinishDropdown = false;
                this.state.showThicknessDropdown = false;
                this.state.showDimensionDropdown = false;
                this.state.showSupplierDropdown = false;
                this.state.showBrandDropdown = false;
            }
        });
    }

    // ---- Searchable dropdown handlers ----

    onFinishFocus() {
        this.state.showFinishDropdown = true;
        this.state.finishSearch = '';
        this.state.filteredFinishes = [...this.state.finishes];
    }
    filterFinishes(ev) {
        const val = ev.target.value;
        this.state.finishSearch = val;
        this.state.filteredFinishes = this.state.finishes.filter(f =>
            f.name.toLowerCase().includes(val.toLowerCase())
        );
        this.state.showFinishDropdown = true;
        this.state.selection.finish_id = null;
    }
    selectFinish(f) {
        this.state.selection.finish_id = f.id;
        this.state.finishSearch = f.name.toUpperCase();
        this.state.showFinishDropdown = false;
    }

    onThicknessFocus() {
        this.state.showThicknessDropdown = true;
        this.state.thicknessSearch = '';
        this.state.filteredThicknesses = [...this.state.thicknesses];
    }
    filterThicknesses(ev) {
        const val = ev.target.value;
        this.state.thicknessSearch = val;
        this.state.filteredThicknesses = this.state.thicknesses.filter(t =>
            t.name.toLowerCase().includes(val.toLowerCase())
        );
        this.state.showThicknessDropdown = true;
        this.state.selection.thickness_id = null;
    }
    selectThickness(t) {
        this.state.selection.thickness_id = t.id;
        this.state.thicknessSearch = t.name.toUpperCase();
        this.state.showThicknessDropdown = false;
    }

    onDimensionFocus() {
        this.state.showDimensionDropdown = true;
        this.state.dimensionSearch = '';
        this.state.filteredDimensions = [...this.state.dimensions];
    }
    filterDimensions(ev) {
        const val = ev.target.value;
        this.state.dimensionSearch = val;
        this.state.filteredDimensions = this.state.dimensions.filter(d =>
            d.name.toLowerCase().includes(val.toLowerCase())
        );
        this.state.showDimensionDropdown = true;
        this.state.selection.dimension_id = null;
    }
    selectDimension(d) {
        this.state.selection.dimension_id = d.id;
        this.state.dimensionSearch = d.name.toUpperCase();
        this.state.showDimensionDropdown = false;
    }

    onSupplierFocus() {
        this.state.showSupplierDropdown = true;
        this.state.supplierSearch = '';
        this.state.filteredSuppliers = [...this.state.suppliers];
    }
    filterSuppliers(ev) {
        const val = ev.target.value;
        this.state.supplierSearch = val;
        this.state.filteredSuppliers = this.state.suppliers.filter(s =>
            s.name.toLowerCase().includes(val.toLowerCase())
        );
        this.state.showSupplierDropdown = true;
        this.state.selection.supplier_id = null;
    }
    selectSupplier(s) {
        this.state.selection.supplier_id = s.id;
        this.state.supplierSearch = s.name;
        this.state.showSupplierDropdown = false;
    }

    onBrandFocus() {
        this.state.showBrandDropdown = true;
        this.state.brandSearch = '';
        this.state.filteredBrands = [...this.state.brands];
    }
    filterBrands(ev) {
        const val = ev.target.value;
        this.state.brandSearch = val;
        this.state.filteredBrands = this.state.brands.filter(b =>
            b.name.toLowerCase().includes(val.toLowerCase())
        );
        this.state.showBrandDropdown = true;
        this.state.selection.brand_id = null;
    }
    selectBrand(b) {
        this.state.selection.brand_id = b.id;
        this.state.brandSearch = b.name.toUpperCase();
        this.state.showBrandDropdown = false;
    }

    // ---- Helpers: visibilidad por tipo ----

    get isPieza() {
        return this.state.productType === 'pieza';
    }

    get showAcabado() {
        return !this.isPieza;
    }

    get showEspesor() {
        return !this.isPieza;
    }

    get showColor() {
        return !this.isPieza;
    }

    get showDimension() {
        return this.state.productType === 'formato' || this.state.productType === 'placa_sintetica';
    }

    get showMarca() {
        return this.state.productType === 'formato'
            || this.state.productType === 'placa_sintetica'
            || this.state.productType === 'pieza';
    }

    get typeLabel() {
        const labels = {
            'placa_natural': 'NUEVA PLACA NATURAL',
            'placa_sintetica': 'NUEVA PLACA SINTÉTICA',
            'formato': 'NUEVO FORMATO',
            'pieza': 'NUEVA PIEZA',
        };
        return labels[this.state.productType] || 'NUEVO PRODUCTO';
    }

    // ---- Navigation ----

    async selectType(typeName) {
        this.state.productType = typeName;

        const categories = await this.orm.call(
            "generator.category.config",
            "get_categories_for_type",
            [typeName]
        );
        this.state.subCategories = categories;
        this.state.step = 2;
    }

    goBackToType() {
        this.state.step = 1;
        this.state.productType = null;
        this.state.selection = {
            commercial_name: '',
            origin_name: '',
            color: '',
            brand_id: null,
            finish_id: null,
            thickness_id: null,
            dimension_id: null,
            supplier_id: null,
            category_id: null
        };
        this.state.finishSearch = '';
        this.state.thicknessSearch = '';
        this.state.dimensionSearch = '';
        this.state.supplierSearch = '';
        this.state.brandSearch = '';
    }

    // ---- Create ----

    async createProduct() {
        if (!this.state.selection.category_id) {
            this.notification.add("Debe elegir una categoría final", { type: 'danger' });
            return;
        }

        const finish = this.showAcabado
            ? (this.state.finishes.find(f => f.id == this.state.selection.finish_id)?.name || '')
            : '';
        const thickness = this.showEspesor
            ? (this.state.thicknesses.find(t => t.id == this.state.selection.thickness_id)?.name || '')
            : '';
        const dimension = this.showDimension
            ? (this.state.dimensions.find(d => d.id == this.state.selection.dimension_id)?.name || '')
            : '';
        const brand = this.showMarca
            ? (this.state.brands.find(b => b.id == this.state.selection.brand_id)?.name || '')
            : '';

        const resId = await this.orm.call("product.template", "create_artistic_product", [{
            'commercial_name': this.state.selection.commercial_name,
            'origin_name': this.state.selection.origin_name,
            'color': this.showColor ? this.state.selection.color : '',
            'marca': brand,
            'finish': finish,
            'thickness': thickness,
            'dimension': dimension,
            'category_id': parseInt(this.state.selection.category_id),
            'supplier_id': this.state.selection.supplier_id || false,
            'product_type': this.state.productType,
        }]);

        this.notification.add("¡Producto generado exitosamente!", { type: 'success' });

        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            res_id: resId,
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

ArtisticGenerator.template = "product_artistic_generator.GeneratorTemplate";
registry.category("actions").add("artistic_product_generator", ArtisticGenerator);```

## ./static/src/components/product_generator/product_generator.scss
```scss
// Forzar scroll en contenedores padre de Odoo que bloquean overflow
.o_action_manager .o_action.o_client_action,
.o_action_manager .o_action {
    overflow-y: auto !important;
    height: 100% !important;
}

.o_artistic_wrapper {
    background-color: #f8f9fa;
    min-height: 100%;
    height: auto;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 40px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;

    .o_main_card {
        background: white;
        padding: 60px 70px;
        border-radius: 20px;
        box-shadow: 0 15px 50px rgba(113, 75, 103, 0.18);
        width: 100%;
        max-width: 900px;

        .o_title {
            color: #714B67;
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 35px;
            text-align: center;
            border-bottom: 3px solid #f1f1f1;
            padding-bottom: 20px;
        }

        .o_primary_color { color: #714B67; }

        .o_label {
            font-size: 0.875rem;
            font-weight: 800;
            color: #8F8F8F;
            margin-bottom: 10px;
            display: block;
        }

        .o_input, .o_select {
            border: 2px solid #eee;
            border-radius: 10px;
            padding: 16px 18px;
            width: 100%;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s;
            // Prevenir zoom en iOS al hacer focus
            @media (max-width: 767px) {
                font-size: 16px;
            }
            &:focus {
                border-color: #017E84;
                outline: none;
                box-shadow: 0 0 0 4px rgba(1, 126, 132, 0.1);
            }
        }

        .o_searchable_select {
            position: relative;

            .o_dropdown_list {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 2px solid #eee;
                border-top: none;
                border-radius: 0 0 10px 10px;
                max-height: 250px;
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
                z-index: 100;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);

                .o_dropdown_item {
                    padding: 14px 18px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 1rem;
                    // Área táctil más grande en móvil
                    @media (max-width: 767px) {
                        padding: 16px 18px;
                        min-height: 48px;
                        display: flex;
                        align-items: center;
                    }
                    &:hover {
                        background: #f0f7f7;
                        color: #017E84;
                    }
                    &:active {
                        background: #e0f0f0;
                        color: #017E84;
                    }
                }

                .o_dropdown_empty {
                    padding: 14px 18px;
                    color: #999;
                    font-style: italic;
                }
            }
        }

        .o_btn_primary {
            background-color: #714B67;
            color: white;
            border: none;
            padding: 16px 40px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.1rem;
            cursor: pointer;
            &:hover { background-color: #5a3c52; }
            &:active { background-color: #4a2f42; }
        }

        .o_btn_success {
            background-color: #21B799;
            color: white;
            border: none;
            padding: 16px 40px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.1rem;
            cursor: pointer;
            &:hover { background-color: #1a927a; }
            &:active { background-color: #15806a; }
        }

        .o_choice_card {
            border: 2px solid #eee;
            padding: 50px 40px;
            border-radius: 16px;
            width: 220px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;

            span {
                font-weight: 700;
                color: #714B67;
                font-size: 1.2rem;
            }

            .o_icon_placa {
                width: 80px;
                height: 65px;
                display: flex;
                align-items: center;
                justify-content: center;

                .o_slab {
                    width: 75px;
                    height: 60px;
                    background: linear-gradient(135deg, #d4d4d4 0%, #a8a8a8 50%, #c0c0c0 100%);
                    border-radius: 6px;
                    border: 3px solid #8F8F8F;
                    box-shadow: 3px 3px 0 #999;

                    &.o_slab_natural {
                        background: linear-gradient(135deg, #e8d5b7 0%, #c4a882 40%, #d4b896 70%, #bfa07a 100%);
                        border-color: #a08060;
                        box-shadow: 3px 3px 0 #9a7a5a;
                    }

                    &.o_slab_sintetica {
                        background: linear-gradient(135deg, #c8d8e8 0%, #9ab0c8 40%, #b0c4d8 70%, #8aa0b8 100%);
                        border-color: #7090a8;
                        box-shadow: 3px 3px 0 #6a8a9a;
                    }
                }
            }

            .o_icon_formato {
                width: 80px;
                height: 65px;
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                grid-template-rows: repeat(2, 1fr);
                gap: 4px;

                .o_tile {
                    background: linear-gradient(135deg, #d4d4d4 0%, #a8a8a8 50%, #c0c0c0 100%);
                    border-radius: 3px;
                    border: 2px solid #8F8F8F;
                }
            }

            // Icono PLACA SINTÉTICA - Placa con patrón
            .o_icon_placa_sintetica {
                width: 80px;
                height: 65px;
                display: flex;
                align-items: center;
                justify-content: center;

                .o_slab_sint {
                    width: 75px;
                    height: 60px;
                    background: linear-gradient(135deg, #b8d4e3 0%, #8bb8cc 50%, #a0c8d8 100%);
                    border-radius: 6px;
                    border: 3px solid #7aa8b8;
                    box-shadow: 3px 3px 0 #6998a8;
                    position: relative;
                    overflow: hidden;

                    &::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: repeating-linear-gradient(
                            45deg,
                            transparent,
                            transparent 8px,
                            rgba(255,255,255,0.15) 8px,
                            rgba(255,255,255,0.15) 10px
                        );
                    }
                }
            }

            // Icono PIEZA - Cubo
            .o_icon_pieza {
                width: 80px;
                height: 65px;
                display: flex;
                align-items: center;
                justify-content: center;

                .o_cube {
                    width: 50px;
                    height: 50px;
                    background: linear-gradient(135deg, #c8b8d8 0%, #a090b8 50%, #b8a8c8 100%);
                    border-radius: 8px;
                    border: 3px solid #9080a8;
                    box-shadow: 3px 3px 0 #807098;
                }
            }

            &:hover, &:active {
                transform: translateY(-10px);
                border-color: #E4A900;
                box-shadow: 0 12px 30px rgba(228, 169, 0, 0.25);

                .o_icon_placa .o_slab,
                .o_icon_formato .o_tile {
                    background: linear-gradient(135deg, #f5e6a3 0%, #E4A900 50%, #d4a000 100%);
                    border-color: #c49500;
                    box-shadow: 3px 3px 0 #b08500;
                }

                .o_icon_placa_sintetica .o_slab_sint {
                    background: linear-gradient(135deg, #f5e6a3 0%, #E4A900 50%, #d4a000 100%);
                    border-color: #c49500;
                    box-shadow: 3px 3px 0 #b08500;
                }

                .o_icon_pieza .o_cube {
                    background: linear-gradient(135deg, #f5e6a3 0%, #E4A900 50%, #d4a000 100%);
                    border-color: #c49500;
                    box-shadow: 3px 3px 0 #b08500;
                }
            }
        }

        h3 {
            font-size: 1.5rem;
        }

        .btn-secondary {
            padding: 16px 40px;
            font-weight: 700;
            font-size: 1.1rem;
            border-radius: 10px;
        }

        .btn-link {
            font-size: 1rem;
            font-weight: 600;
        }

        .row.g-3 {
            row-gap: 1.5rem !important;
        }

        .mt-4 {
            margin-top: 2.5rem !important;
        }

        .mb-4 {
            margin-bottom: 2rem !important;
        }
    }
}

// =============================================
// TABLET (768px - 1024px)
// =============================================
@media (max-width: 1024px) {
    .o_artistic_wrapper {
        padding: 24px;

        .o_main_card {
            padding: 40px 36px;
        }
    }
}

// =============================================
// MÓVIL (< 768px)
// =============================================
@media (max-width: 767px) {
    // Forzar scroll en toda la cadena de contenedores Odoo
    .o_action_manager,
    .o_action_manager .o_action,
    .o_action_manager .o_action.o_client_action {
        overflow-y: auto !important;
        height: auto !important;
        min-height: 100% !important;
    }

    .o_artistic_wrapper {
        padding: 12px;
        align-items: flex-start;
        min-height: auto;
        height: auto;
        overflow-y: visible;
        padding-bottom: 40px;

        .o_main_card {
            padding: 28px 20px;
            border-radius: 14px;
            box-shadow: 0 8px 30px rgba(113, 75, 103, 0.14);

            .o_title {
                font-size: 1.4rem;
                margin-bottom: 20px;
                padding-bottom: 14px;
            }

            h3 {
                font-size: 1.15rem;
            }

            .o_label {
                font-size: 0.8rem;
                margin-bottom: 6px;
            }

            .o_input, .o_select {
                padding: 13px 14px;
                border-radius: 8px;
                font-size: 16px; // Previene zoom en iOS
            }

            // Tarjetas de selección tipo - 4 tarjetas en grid 2x2
            .o_choice_card {
                width: calc(50% - 6px);
                max-width: 160px;
                padding: 20px 14px;
                gap: 10px;

                span {
                    font-size: 0.85rem;
                    text-align: center;
                    line-height: 1.2;
                }

                .o_icon_placa {
                    width: 50px;
                    height: 42px;

                    .o_slab {
                        width: 46px;
                        height: 38px;
                    }
                }

                .o_icon_placa_sintetica {
                    width: 50px;
                    height: 42px;

                    .o_slab_sint {
                        width: 46px;
                        height: 38px;
                    }
                }

                .o_icon_formato {
                    width: 50px;
                    height: 42px;
                    gap: 2px;
                }

                .o_icon_pieza {
                    width: 50px;
                    height: 42px;

                    .o_cube {
                        width: 38px;
                        height: 38px;
                    }
                }

                &:hover, &:active {
                    transform: translateY(-5px);
                }
            }

            .d-flex.justify-content-center.gap-4 {
                gap: 10px !important;
                flex-wrap: wrap;
            }

            // Forzar columnas a full width en móvil
            .row.g-3 {
                row-gap: 1rem !important;

                .col-md-6 {
                    flex: 0 0 100%;
                    max-width: 100%;
                }
            }

            // Botones
            .o_btn_primary,
            .o_btn_success,
            .btn-secondary {
                padding: 14px 24px;
                font-size: 1rem;
                width: 100%;
                text-align: center;
            }

            // Stack de botones en móvil
            .d-flex.justify-content-between.mt-4 {
                flex-direction: column-reverse;
                gap: 12px;

                .btn-secondary,
                .o_btn_success {
                    width: 100%;
                }
            }

            // Dropdown ajustado
            .o_searchable_select .o_dropdown_list {
                max-height: 200px;
                border-radius: 0 0 8px 8px;
            }

            .mt-4 {
                margin-top: 1.5rem !important;
            }

            .mb-4 {
                margin-bottom: 1.2rem !important;
            }
        }
    }
}

// =============================================
// MÓVIL PEQUEÑO (< 400px)
// =============================================
@media (max-width: 399px) {
    .o_artistic_wrapper {
        padding: 8px;

        .o_main_card {
            padding: 20px 14px;
            border-radius: 10px;

            .o_title {
                font-size: 1.2rem;
                margin-bottom: 16px;
            }

            h3 {
                font-size: 1rem;
            }

            .o_choice_card {
                width: calc(50% - 4px);
                max-width: 140px;
                padding: 14px 8px;
                gap: 6px;

                span {
                    font-size: 0.7rem;
                }
            }

            .d-flex.justify-content-center.gap-4 {
                gap: 6px !important;
                flex-wrap: wrap;
            }
        }
    }
}

// =============================================
// ANIMACIONES
// =============================================
.o_fade_in {
    animation: fadeInRight 0.4s ease-out;
}

@keyframes fadeInRight {
    from { opacity: 0; transform: translateX(30px); }
    to { opacity: 1; transform: translateX(0); }
}

// Reducir animación en móvil para rendimiento
@media (max-width: 767px) {
    .o_fade_in {
        animation: fadeInUp 0.3s ease-out;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
}```

## ./static/src/components/product_generator/product_generator.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="product_artistic_generator.GeneratorTemplate" owl="1">
        <div class="o_artistic_wrapper">
            <div class="o_main_card">
                <!-- PASO 1: SELECCIÓN DE TIPO -->
                <div t-if="state.step === 1" class="o_fade_in text-center">
                    <h2 class="o_title">NUEVO PRODUCTO</h2>
                    <h3 class="mb-4 text-muted">SELECCIONE EL TIPO</h3>
                    <div class="d-flex justify-content-center gap-4 flex-wrap">
                        <div class="o_choice_card" t-on-click="() => this.selectType('placa_natural')">
                            <div class="o_icon_placa">
                                <div class="o_slab"></div>
                            </div>
                            <span>PLACA NATURAL</span>
                        </div>
                        <div class="o_choice_card" t-on-click="() => this.selectType('placa_sintetica')">
                            <div class="o_icon_placa_sintetica">
                                <div class="o_slab_sint"></div>
                            </div>
                            <span>PLACA SINTÉTICA</span>
                        </div>
                        <div class="o_choice_card" t-on-click="() => this.selectType('formato')">
                            <div class="o_icon_formato">
                                <div class="o_tile"></div>
                                <div class="o_tile"></div>
                                <div class="o_tile"></div>
                                <div class="o_tile"></div>
                                <div class="o_tile"></div>
                                <div class="o_tile"></div>
                            </div>
                            <span>FORMATO</span>
                        </div>
                        <div class="o_choice_card" t-on-click="() => this.selectType('pieza')">
                            <div class="o_icon_pieza">
                                <div class="o_cube"></div>
                            </div>
                            <span>PIEZA</span>
                        </div>
                    </div>
                </div>

                <!-- PASO 2: FORMULARIO -->
                <div t-if="state.step === 2" class="o_fade_in">
                    <h2 class="o_title"><t t-esc="typeLabel"/></h2>
                    <div class="row g-3">
                        <!-- Nombre de Origen -->
                        <div class="col-md-6">
                            <label class="o_label">NOMBRE DE ORIGEN</label>
                            <input type="text" class="o_input" t-model="state.selection.origin_name" placeholder="Nombre del proveedor para este producto..."/>
                        </div>

                        <!-- Nombre Comercial -->
                        <div class="col-md-6">
                            <label class="o_label">NOMBRE COMERCIAL</label>
                            <input type="text" class="o_input" t-model="state.selection.commercial_name" placeholder="Ej: BLANCO CARRARA"/>
                        </div>

                        <!-- Acabado (NO pieza) -->
                        <div t-if="showAcabado" class="col-md-6">
                            <label class="o_label">ACABADO</label>
                            <div class="o_searchable_select">
                                <input type="text" class="o_input"
                                    t-model="state.finishSearch"
                                    t-on-input="filterFinishes"
                                    t-on-focus="onFinishFocus"
                                    placeholder="Buscar acabado..."/>
                                <div t-if="state.showFinishDropdown" class="o_dropdown_list">
                                    <t t-foreach="state.filteredFinishes" t-as="f" t-key="f.id">
                                        <div class="o_dropdown_item" t-on-click="() => this.selectFinish(f)">
                                            <t t-esc="f.name.toUpperCase()"/>
                                        </div>
                                    </t>
                                    <div t-if="state.filteredFinishes.length === 0" class="o_dropdown_empty">
                                        Sin resultados
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Espesor (NO pieza) -->
                        <div t-if="showEspesor" class="col-md-6">
                            <label class="o_label">ESPESOR</label>
                            <div class="o_searchable_select">
                                <input type="text" class="o_input"
                                    t-model="state.thicknessSearch"
                                    t-on-input="filterThicknesses"
                                    t-on-focus="onThicknessFocus"
                                    placeholder="Buscar espesor..."/>
                                <div t-if="state.showThicknessDropdown" class="o_dropdown_list">
                                    <t t-foreach="state.filteredThicknesses" t-as="t" t-key="t.id">
                                        <div class="o_dropdown_item" t-on-click="() => this.selectThickness(t)">
                                            <t t-esc="t.name.toUpperCase()"/>
                                        </div>
                                    </t>
                                    <div t-if="state.filteredThicknesses.length === 0" class="o_dropdown_empty">
                                        Sin resultados
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Color (NO pieza) -->
                        <div t-if="showColor" class="col-md-6">
                            <label class="o_label">COLOR</label>
                            <input type="text" class="o_input" t-model="state.selection.color" placeholder="Ej: BLANCO, GRIS, BEIGE..."/>
                        </div>

                        <!-- Marca Comercial (formato, placa sintética, pieza) -->
                        <div t-if="showMarca" class="col-md-6">
                            <label class="o_label">MARCA COMERCIAL</label>
                            <div class="o_searchable_select">
                                <input type="text" class="o_input"
                                    t-model="state.brandSearch"
                                    t-on-input="filterBrands"
                                    t-on-focus="onBrandFocus"
                                    placeholder="Buscar marca..."/>
                                <div t-if="state.showBrandDropdown" class="o_dropdown_list">
                                    <t t-foreach="state.filteredBrands" t-as="b" t-key="b.id">
                                        <div class="o_dropdown_item" t-on-click="() => this.selectBrand(b)">
                                            <t t-esc="b.name.toUpperCase()"/>
                                        </div>
                                    </t>
                                    <div t-if="state.filteredBrands.length === 0" class="o_dropdown_empty">
                                        Sin resultados
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Dimensión (formato y placa sintética, NO pieza) -->
                        <div t-if="showDimension" class="col-md-6">
                            <label class="o_label">DIMENSIÓN</label>
                            <div class="o_searchable_select">
                                <input type="text" class="o_input"
                                    t-model="state.dimensionSearch"
                                    t-on-input="filterDimensions"
                                    t-on-focus="onDimensionFocus"
                                    placeholder="Buscar dimensión..."/>
                                <div t-if="state.showDimensionDropdown" class="o_dropdown_list">
                                    <t t-foreach="state.filteredDimensions" t-as="d" t-key="d.id">
                                        <div class="o_dropdown_item" t-on-click="() => this.selectDimension(d)">
                                            <t t-esc="d.name.toUpperCase()"/>
                                        </div>
                                    </t>
                                    <div t-if="state.filteredDimensions.length === 0" class="o_dropdown_empty">
                                        Sin resultados
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Categoría -->
                        <div class="col-md-6">
                            <label class="o_label">CATEGORÍA</label>
                            <select class="o_select" t-model="state.selection.category_id">
                                <option value="">ELIJA CATEGORÍA...</option>
                                <t t-foreach="state.subCategories" t-as="sc" t-key="sc.id">
                                    <option t-att-value="sc.id"><t t-esc="sc.short_name.toUpperCase()"/></option>
                                </t>
                            </select>
                        </div>

                        <!-- Proveedor -->
                        <div class="col-md-6">
                            <label class="o_label">PROVEEDOR</label>
                            <div class="o_searchable_select">
                                <input type="text" class="o_input"
                                    t-model="state.supplierSearch"
                                    t-on-input="filterSuppliers"
                                    t-on-focus="onSupplierFocus"
                                    placeholder="Buscar proveedor..."/>
                                <div t-if="state.showSupplierDropdown" class="o_dropdown_list">
                                    <t t-foreach="state.filteredSuppliers" t-as="s" t-key="s.id">
                                        <div class="o_dropdown_item" t-on-click="() => this.selectSupplier(s)">
                                            <t t-esc="s.name"/>
                                        </div>
                                    </t>
                                    <div t-if="state.filteredSuppliers.length === 0" class="o_dropdown_empty">
                                        Sin resultados
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between mt-4">
                        <button class="btn btn-secondary" t-on-click="goBackToType">VOLVER</button>
                        <button class="o_btn_success" t-on-click="createProduct">CREAR PRODUCTO</button>
                    </div>
                </div>
            </div>
        </div>
    </t>
</templates>```

## ./views/menu_views.xml
```xml
<odoo>
    <record id="action_artistic_generator" model="ir.actions.client">
        <field name="name">Generador de Productos</field>
        <field name="tag">artistic_product_generator</field>
    </record>

    <menuitem id="menu_artistic_root" name="Generador" web_icon="product_artistic_generator,static/description/icon.png" groups="product_artistic_generator.group_product_generator"/>
    <menuitem id="menu_generator_action" name="Crear Producto" parent="menu_artistic_root" action="action_artistic_generator" sequence="10"/>
    <menuitem id="menu_config_root" name="Configuración" parent="menu_artistic_root" sequence="100"/>
    <menuitem id="menu_finish" name="Acabados" parent="menu_config_root" action="action_product_finish" sequence="10"/>
    <menuitem id="menu_thickness" name="Espesores" parent="menu_config_root" action="action_product_thickness" sequence="20"/>
    <menuitem id="menu_dimension" name="Dimensiones" parent="menu_config_root" action="action_product_dimension" sequence="40"/>
    <menuitem id="menu_brand" name="Marcas" parent="menu_config_root" action="action_product_brand" sequence="45"/>
    <menuitem id="menu_category_config" name="Categorías por Tipo" parent="menu_config_root" action="action_generator_category_config" sequence="50"/>
</odoo>```

## ./views/product_attribute_views.xml
```xml
<odoo>
    <record id="view_product_finish_list" model="ir.ui.view">
        <field name="name">product.finish.list</field>
        <field name="model">product.finish</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
            </list>
        </field>
    </record>

    <record id="action_product_finish" model="ir.actions.act_window">
        <field name="name">Acabados</field>
        <field name="res_model">product.finish</field>
        <field name="view_mode">list</field>
    </record>

    <record id="view_product_thickness_list" model="ir.ui.view">
        <field name="name">product.thickness.list</field>
        <field name="model">product.thickness</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
            </list>
        </field>
    </record>

    <record id="action_product_thickness" model="ir.actions.act_window">
        <field name="name">Espesores</field>
        <field name="res_model">product.thickness</field>
        <field name="view_mode">list</field>
    </record>

    <record id="view_product_dimension_list" model="ir.ui.view">
        <field name="name">product.dimension.list</field>
        <field name="model">product.dimension</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
            </list>
        </field>
    </record>

    <record id="action_product_dimension" model="ir.actions.act_window">
        <field name="name">Dimensiones</field>
        <field name="res_model">product.dimension</field>
        <field name="view_mode">list</field>
    </record>

    <!-- Marcas -->
    <record id="view_product_brand_list" model="ir.ui.view">
        <field name="name">product.brand.list</field>
        <field name="model">product.brand</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
            </list>
        </field>
    </record>

    <record id="action_product_brand" model="ir.actions.act_window">
        <field name="name">Marcas</field>
        <field name="res_model">product.brand</field>
        <field name="view_mode">list</field>
    </record>

    <!-- Categorías por Tipo - Lista -->
    <record id="view_generator_category_config_list" model="ir.ui.view">
        <field name="name">generator.category.config.list</field>
        <field name="model">generator.category.config</field>
        <field name="arch" type="xml">
            <list>
                <field name="product_type"/>
                <field name="category_ids" widget="many2many_tags"/>
            </list>
        </field>
    </record>

    <!-- Categorías por Tipo - Formulario -->
    <record id="view_generator_category_config_form" model="ir.ui.view">
        <field name="name">generator.category.config.form</field>
        <field name="model">generator.category.config</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="product_type"/>
                    </group>
                    <group string="Categorías Disponibles">
                        <field name="category_ids" widget="many2many_tags" nolabel="1"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_generator_category_config" model="ir.actions.act_window">
        <field name="name">Categorías por Tipo</field>
        <field name="res_model">generator.category.config</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>```

