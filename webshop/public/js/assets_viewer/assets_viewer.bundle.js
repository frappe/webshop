import { createApp } from "vue";
import AssetViewerComponent from "./AssetViewer.vue";
import { watch } from "vue";

// TODO: add try...catch
class AssetViewer {
    constructor({ wrapper, frm, item_code } = {}) {
        console.log(frm.doc.assets, "Assets");
        if (!wrapper) {
            console.warn(
                "FileUploaderNew: No wrapper provided, creating a dialog."
            );
            this.make_dialog(dialog_title);
        } else {
            this.wrapper = wrapper.get ? wrapper.get(0) : wrapper;
        }

        let app = createApp(AssetViewerComponent, {
            rows: frm.doc.assets,
            frm: frm,
            item_code,
            deleteFromAssetTable: this.deleteFromAssetTable.bind(this),
        });
        SetVueGlobals(app);
        this.frm = frm;
        this.viewer = app.mount(this.wrapper);

        if (!this.dialog) {
            this.viewer.wrapper_ready = true;
        }
    }
    async deleteFromAssetTable(name) {
        let frm = this.frm;
        console.log("Deleting from asset table:", name, frm);
        let slideshow_name = frm.doc.assets.find(
            (asset) => asset.for_attribute === name
        )?.slideshow;
        frm.set_value(
            "assets",
            frm.doc.assets.filter((asset) => asset.for_attribute !== name)
                .length
                ? frm.doc.assets.filter((asset) => asset.for_attribute !== name)
                : null
        );
        // TODO: add confirmation
        frm.refresh_field("assets");
        await frm.save();
        await frm.refresh();
        setTimeout(async () => {
            await this.deleteVariantSelection(name);
            await this.deleteSlideshow(slideshow_name);
        }, 1);
    }

    async deleteVariantSelection(name) {
        let resp = await frappe.call({
            method: "webshop.webshop.api.delete_variant_selection",
            type: "POST",
            args: {
                name: name,
            },
        });
        console.log("Response from delete_variant_selection:", resp);
    }

    async deleteSlideshow(name) {
        let resp = await frappe.call({
            method: "webshop.webshop.api.delete_slideshow",
            type: "POST",
            args: {
                name: name,
            },
        });
        console.log("Response from delete_slideshow:", resp);
    }
}

frappe.provide("frappe.ui.custom");
frappe.ui.custom.AssetViewer = AssetViewer;
console.log("AssetViewer initialized");
export default AssetViewer;
