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
            subCategories: [],
            selection: {
                artistic_name: '',
                finish_id: null,
                thickness_id: null,
                category_id: null
            }
        });

        onWillStart(async () => {
            // Cargar maestros
            this.state.finishes = await this.orm.searchRead("product.finish", [], ["name"]);
            this.state.thicknesses = await this.orm.searchRead("product.thickness", [], ["name"]);
        });
    }

    async selectType(typeName) {
        // Buscamos categorías que cuelguen de "Bienes / Placas" o "Bienes / Formatos"
        // Usamos display_name para filtrar por la ruta completa
        const searchName = "Bienes / " + typeName;
        const categories = await this.orm.searchRead("product.category", 
            [['display_name', 'ilike', searchName]], 
            ["display_name"]
        );
        
        // Filtramos para no incluir la categoría padre misma si aparece
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
        
        // Ir al producto creado
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