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
            productType: null, // 'placa_natural', 'placa_sintetica', 'formato'
            finishes: [],
            thicknesses: [],
            dimensions: [],
            suppliers: [],
            filteredFinishes: [],
            filteredThicknesses: [],
            filteredDimensions: [],
            filteredSuppliers: [],
            showFinishDropdown: false,
            showThicknessDropdown: false,
            showDimensionDropdown: false,
            showSupplierDropdown: false,
            finishSearch: '',
            thicknessSearch: '',
            dimensionSearch: '',
            supplierSearch: '',
            subCategories: [],
            selection: {
                commercial_name: '',
                origin_name: '',
                color: '',
                marca: '',
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
            this.state.filteredFinishes = [...this.state.finishes];
            this.state.filteredThicknesses = [...this.state.thicknesses];
            this.state.filteredDimensions = [...this.state.dimensions];
            this.state.filteredSuppliers = [...this.state.suppliers];
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.o_searchable_select')) {
                this.state.showFinishDropdown = false;
                this.state.showThicknessDropdown = false;
                this.state.showDimensionDropdown = false;
                this.state.showSupplierDropdown = false;
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

    // ---- Helpers ----

    get showDimension() {
        return this.state.productType === 'formato' || this.state.productType === 'placa_sintetica';
    }

    get typeLabel() {
        const labels = {
            'placa_natural': 'NUEVA PLACA NATURAL',
            'placa_sintetica': 'NUEVA PLACA SINTÉTICA',
            'formato': 'NUEVO FORMATO',
        };
        return labels[this.state.productType] || 'NUEVO PRODUCTO';
    }

    get showMarca() {
        return this.state.productType === 'formato' || this.state.productType === 'placa_sintetica';
    }

    // ---- Navigation ----

    async selectType(typeName) {
        this.state.productType = typeName;

        // Cargar categorías desde configuración
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
            marca: '',
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
    }

    // ---- Create ----

    async createProduct() {
        if (!this.state.selection.category_id) {
            this.notification.add("Debe elegir una categoría final", { type: 'danger' });
            return;
        }

        const finish = this.state.finishes.find(f => f.id == this.state.selection.finish_id)?.name || '';
        const thickness = this.state.thicknesses.find(t => t.id == this.state.selection.thickness_id)?.name || '';
        const dimension = this.state.dimensions.find(d => d.id == this.state.selection.dimension_id)?.name || '';

        const resId = await this.orm.call("product.template", "create_artistic_product", [{
            'commercial_name': this.state.selection.commercial_name,
            'origin_name': this.state.selection.origin_name,
            'color': this.state.selection.color,
            'marca': this.showMarca ? this.state.selection.marca : '',
            'finish': finish,
            'thickness': thickness,
            'dimension': this.showDimension ? dimension : '',
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
registry.category("actions").add("artistic_product_generator", ArtisticGenerator);