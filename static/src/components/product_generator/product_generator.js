/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ArtisticGenerator extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            step: 1,
            names: [],
            finishes: [],
            thicknesses: [],
            categories: [],
            subCategories: [],
            selection: {
                artistic_name: '',
                base_name_id: null,
                finish_id: null,
                thickness_id: null,
                main_category: '', // Placa o Formato
                category_id: null
            }
        });

        onWillStart(async () => {
            await this._loadData();
        });
    }

    async _loadData() {
        this.state.names = await this.orm.searchRead("product.artistic.name", [], ["name"]);
        this.state.finishes = await this.orm.searchRead("product.finish", [], ["name"]);
        this.state.thicknesses = await this.orm.searchRead("product.thickness", [], ["name"]);
        
        // Cargar categorías que son hijas de "Bienes" (Simulado - ajusta el ID según tu DB)
        const categories = await this.orm.searchRead("product.category", [], ["name", "parent_id"]);
        this.state.categories = categories;
    }

    setMainCategory(type) {
        this.state.selection.main_category = type;
        this.state.subCategories = this.state.categories.filter(c => 
            c.parent_id && c.parent_id[1].includes(type)
        );
        this.state.step = 2;
    }

    async createProduct() {
        try {
            const baseName = this.state.names.find(n => n.id == this.state.selection.base_name_id).name;
            const finish = this.state.finishes.find(f => f.id == this.state.selection.finish_id).name;
            const thickness = this.state.thicknesses.find(t => t.id == this.state.selection.thickness_id).name;

            const resId = await this.orm.call("product.template", "create_artistic_product", [{
                'artistic_name': this.state.selection.artistic_name,
                'base_name': baseName,
                'finish': finish,
                'thickness': thickness,
                'category_id': parseInt(this.state.selection.category_id)
            }]);

            if (resId) {
                this.notification.add("¡Producto Creado con Éxito!", { type: 'success' });
                this.state.step = 1;
                this.state.selection = { artistic_name: '', base_name_id: null, finish_id: null, thickness_id: null, category_id: null };
            }
        } catch (e) {
            this.notification.add("Error al crear el producto", { type: 'danger' });
        }
    }
}

ArtisticGenerator.template = "product_artistic_generator.GeneratorTemplate";
registry.category("actions").add("artistic_product_generator", ArtisticGenerator);
