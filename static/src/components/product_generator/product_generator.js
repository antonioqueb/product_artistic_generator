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
            finishes: [],
            thicknesses: [],
            filteredFinishes: [],
            filteredThicknesses: [],
            showFinishDropdown: false,
            showThicknessDropdown: false,
            subCategories: [],
            selection: {
                artistic_name: '',
                finish_id: null,
                thickness_id: null,
                category_id: null
            }
        });

        onWillStart(async () => {
            this.state.finishes = await this.orm.searchRead("product.finish", [], ["name"]);
            this.state.thicknesses = await this.orm.searchRead("product.thickness", [], ["name"]);
            this.state.filteredFinishes = [...this.state.finishes];
            this.state.filteredThicknesses = [...this.state.thicknesses];
        });

        // Cerrar dropdowns al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.o_searchable_select')) {
                this.state.showFinishDropdown = false;
                this.state.showThicknessDropdown = false;
            }
        });
    }

    getFinishName() {
        const f = this.state.finishes.find(x => x.id == this.state.selection.finish_id);
        return f ? f.name.toUpperCase() : '';
    }

    getThicknessName() {
        const t = this.state.thicknesses.find(x => x.id == this.state.selection.thickness_id);
        return t ? t.name.toUpperCase() : '';
    }

    filterFinishes(ev) {
        const val = ev.target.value.toLowerCase();
        this.state.filteredFinishes = this.state.finishes.filter(f => 
            f.name.toLowerCase().includes(val)
        );
        this.state.showFinishDropdown = true;
        // Limpiar selección si está escribiendo
        this.state.selection.finish_id = null;
    }

    filterThicknesses(ev) {
        const val = ev.target.value.toLowerCase();
        this.state.filteredThicknesses = this.state.thicknesses.filter(t => 
            t.name.toLowerCase().includes(val)
        );
        this.state.showThicknessDropdown = true;
        this.state.selection.thickness_id = null;
    }

    selectFinish(f) {
        this.state.selection.finish_id = f.id;
        this.state.showFinishDropdown = false;
    }

    selectThickness(t) {
        this.state.selection.thickness_id = t.id;
        this.state.showThicknessDropdown = false;
    }

    async selectType(typeName) {
        const searchName = "Bienes / " + typeName;
        const categories = await this.orm.searchRead("product.category", 
            [['display_name', 'ilike', searchName]], 
            ["display_name"]
        );
        this.state.subCategories = categories.filter(c => c.display_name !== searchName);
        this.state.step = 3;
    }

    async createProduct() {
        if (!this.state.selection.category_id) {
            this.notification.add("Debe elegir una categoría final", { type: 'danger' });
            return;
        }

        const finish = this.state.finishes.find(f => f.id == this.state.selection.finish_id)?.name || '';
        const thickness = this.state.thicknesses.find(t => t.id == this.state.selection.thickness_id)?.name || '';

        const resId = await this.orm.call("product.template", "create_artistic_product", [{
            'artistic_name': this.state.selection.artistic_name,
            'finish': finish,
            'thickness': thickness,
            'category_id': parseInt(this.state.selection.category_id)
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