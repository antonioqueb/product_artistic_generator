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

    // Finish
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

    // Thickness
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

    // Dimension (solo formato)
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

    // Supplier
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

    // Selección de tipo (paso 1)
    async selectType(typeName) {
        this.state.productType = typeName.toLowerCase() === 'placas' ? 'placa' : 'formato';

        const searchName = "Bienes / " + typeName;
        const categories = await this.orm.searchRead("product.category",
            [['display_name', 'ilike', searchName]],
            ["display_name"]
        );
        this.state.subCategories = categories
            .filter(c => c.display_name !== searchName)
            .map(c => ({
                id: c.id,
                display_name: c.display_name,
                short_name: c.display_name.split(' / ').pop()
            }));
        this.state.step = 2;
    }

    goBackToType() {
        this.state.step = 1;
        this.state.productType = null;
        this.state.selection = {
            commercial_name: '',
            origin_name: '',
            color: '',
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
            'finish': finish,
            'thickness': thickness,
            'dimension': this.state.productType === 'formato' ? dimension : '',
            'category_id': parseInt(this.state.selection.category_id),
            'supplier_id': this.state.selection.supplier_id || false,
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