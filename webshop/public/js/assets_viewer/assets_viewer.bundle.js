import { createApp } from "vue";
import AssetViewerComponent from "./AssetViewer.vue";
import { watch } from "vue";

class AssetViewer {
	constructor({
		wrapper,
		frm,
		item_code
	} = {}) {
        console.log(frm.doc.assets, "Assets")
		if (!wrapper) {
			console.warn("FileUploaderNew: No wrapper provided, creating a dialog.");
			this.make_dialog(dialog_title);
		} else {
			this.wrapper = wrapper.get ? wrapper.get(0) : wrapper;
		}

		let app = createApp(AssetViewerComponent, {
			rows: frm.doc.assets,
			frm: frm,
			item_code: item_code
		});
		SetVueGlobals(app);
		this.viewer = app.mount(this.wrapper);

		if (!this.dialog) {
			this.viewer.wrapper_ready = true;
		}
    }
}

frappe.provide("frappe.ui.custom");
frappe.ui.custom.AssetViewer = AssetViewer;
console.log("AssetViewer initialized");
export default AssetViewer;
