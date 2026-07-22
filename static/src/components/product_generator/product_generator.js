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
            // Empaque estandarizado (standard_pack_som): opcional, multilínea
            packModuleAvailable: false,
            packTypes: [],
            hasStandardPack: false,
            packLines: [],
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
            try {
                this.state.packTypes = await this.orm.searchRead(
                    "standard.pack.type", [], ["name", "icon"], { order: "sequence" }
                );
                this.state.packModuleAvailable = this.state.packTypes.length > 0;
            } catch (e) {
                // standard_pack_som no instalado: la sección no se muestra.
                this.state.packModuleAvailable = false;
            }
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

    // ---- Alta rápida de atributos (crear sin salir del generador) ----

    /**
     * Crea (o reutiliza) un atributo en el servidor y lo devuelve normalizado
     * en MAYÚSCULAS. No requiere refrescar: el registro se agrega al estado
     * local y queda seleccionado de inmediato.
     */
    async _quickCreate(model, value) {
        const name = (value || '').trim();
        if (!name) return null;
        return await this.orm.call(model, "quick_create_from_generator", [name]);
    }

    _exists(list, value) {
        const v = (value || '').trim().toUpperCase();
        return !!v && list.some(item => (item.name || '').toUpperCase() === v);
    }

    get canCreateFinish() {
        return !!this.state.finishSearch.trim() && !this._exists(this.state.finishes, this.state.finishSearch);
    }
    async createFinish() {
        const rec = await this._quickCreate("product.finish", this.state.finishSearch);
        if (!rec) return;
        if (!this.state.finishes.some(f => f.id === rec.id)) {
            this.state.finishes.push(rec);
        }
        this.state.filteredFinishes = [...this.state.finishes];
        this.selectFinish(rec);
    }

    get canCreateThickness() {
        return !!this.state.thicknessSearch.trim() && !this._exists(this.state.thicknesses, this.state.thicknessSearch);
    }
    async createThickness() {
        const rec = await this._quickCreate("product.thickness", this.state.thicknessSearch);
        if (!rec) return;
        if (!this.state.thicknesses.some(t => t.id === rec.id)) {
            this.state.thicknesses.push(rec);
        }
        this.state.filteredThicknesses = [...this.state.thicknesses];
        this.selectThickness(rec);
    }

    /**
     * Replica la normalización del servidor para previsualizar la dimensión:
     * '10x20' -> '10 X 20 X'. Mantiene la vista alineada con lo que se guarda.
     */
    get dimensionCreateLabel() {
        let s = this.state.dimensionSearch.trim().toUpperCase().replace(/\s+/g, ' ');
        if (!s) return '';
        s = s.replace(/\s*X\s*/g, 'X').replace(/X+$/g, '');
        const partes = s.split('X').filter(Boolean);
        return partes.length ? partes.join(' X ') + ' X' : 'X';
    }
    get canCreateDimension() {
        const label = this.dimensionCreateLabel;
        return !!label && !this.state.dimensions.some(d => (d.name || '').toUpperCase() === label);
    }
    async createDimension() {
        const rec = await this._quickCreate("product.dimension", this.state.dimensionSearch);
        if (!rec) return;
        if (!this.state.dimensions.some(d => d.id === rec.id)) {
            this.state.dimensions.push(rec);
        }
        this.state.filteredDimensions = [...this.state.dimensions];
        this.selectDimension(rec);
    }

    get canCreateBrand() {
        return !!this.state.brandSearch.trim() && !this._exists(this.state.brands, this.state.brandSearch);
    }
    async createBrand() {
        const rec = await this._quickCreate("product.brand", this.state.brandSearch);
        if (!rec) return;
        if (!this.state.brands.some(b => b.id === rec.id)) {
            this.state.brands.push(rec);
        }
        this.state.filteredBrands = [...this.state.brands];
        this.selectBrand(rec);
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
        this.state.hasStandardPack = false;
        this.state.packLines = [];
    }

    // ---- Empaque estandarizado ----

    togglePack(ev) {
        this.state.hasStandardPack = ev.target.checked;
        if (this.state.hasStandardPack && this.state.packLines.length === 0) {
            this.addPackLine();
        }
    }

    addPackLine() {
        this.state.packLines.push({
            pack_type_id: this.state.packTypes.length === 1 ? String(this.state.packTypes[0].id) : "",
            qty_per_pack: "",
            is_default: this.state.packLines.length === 0,
        });
    }

    removePackLine(index) {
        const wasDefault = this.state.packLines[index] && this.state.packLines[index].is_default;
        this.state.packLines.splice(index, 1);
        if (wasDefault && this.state.packLines.length) {
            this.state.packLines[0].is_default = true;
        }
    }

    setDefaultPack(index) {
        this.state.packLines.forEach((l, i) => { l.is_default = i === index; });
    }

    get validPackLines() {
        return this.state.packLines.filter(
            l => l.pack_type_id && parseFloat(l.qty_per_pack) > 0
        );
    }

    packTypeName(id) {
        const t = this.state.packTypes.find(pt => String(pt.id) === String(id));
        return t ? t.name.toUpperCase() : "";
    }

    // ---- Create ----

    async createProduct() {
        if (!this.state.selection.category_id) {
            this.notification.add("Debe elegir una categoría final", { type: 'danger' });
            return;
        }

        if (this.state.hasStandardPack && this.validPackLines.length === 0) {
            this.notification.add(
                "Marcaste 'Contiene empaque estandarizado': define al menos un empaque con tipo y cantidad.",
                { type: 'danger' }
            );
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
            'standard_packs': this.state.hasStandardPack
                ? this.validPackLines.map(l => ({
                    pack_type_id: parseInt(l.pack_type_id),
                    qty_per_pack: parseFloat(l.qty_per_pack),
                    is_default: !!l.is_default,
                }))
                : [],
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