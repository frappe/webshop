<template>
    <div class="asset-group-row">
        <h4 style="font-weight: 400">Images:</h4>
        <div class="image-previews">
            <MainAssetsViewer
                v-for="value in all_main_images"
                :key="value.name"
                :image="value.image"
            />
            <div class="add-new-image">
                <button
                    @click="addImage"
                    v-html="frappe.utils.icon('add', 'sm')"
                ></button>
            </div>
        </div>
    </div>
    <div v-if="Object.keys(attribute_data).length" class="asset-group-row">
        <h4
            style="
                font-weight: 400;
                display: flex;
                justify-content: space-between;
                align-items: center;
            "
        >
            <span>Attribute Images:</span>
            <button
                class="btn btn-sm"
                @click="addGroup"
                v-html="frappe.utils.icon('add', 'sm')"
            ></button>
        </h4>
        <div v-if="rows && rows.length" v-for="value in rows" :key="value.id">
            <AssetViewerItem
                :for_attribute="value.for_attribute"
                :slideshow="value.slideshow"
            />
        </div>
        <div v-else class="no-rows-placeholder">
            <p>No attribute images available.</p>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import AssetViewerItem from "./AttributesAssetViewerItem.vue";
import MainAssetsViewer from "./MainAssetsViewer.vue";
let props = defineProps({
    rows: Array,
    frm: Object,
    item_code: String,
});

let loading_attribute_details = ref(false);
let attribute_data = ref({});
let all_main_images = ref([]);

function addGroup() {
    let frm = props.frm;
    console.log("Add group clicked");
    new frappe.ui.custom.FileUploader({
        item_code: frm.doc.item_code,
        // on_success: () => onSuccess(frm),
        make_attachments_public: true,
        add_to_table: (variant_selection_table_name, slideshow_name) => {
            console.log(
                "Adding to table",
                variant_selection_table_name,
                slideshow_name
            );
            frm.add_child("assets", {
                for_attribute: variant_selection_table_name,
                slideshow: slideshow_name,
            });
            frm.refresh_field("assets");
            frm.save();
        },
    });
}

function addImage() {
    let frm = props.frm;
    console.log("Add image clicked");
    new frappe.ui.custom.FileUploader({
        item_code: frm.doc.item_code,
        make_attachments_public: true,
        frm,
        for_main: true,
        main_assets: frm.doc.main_assets,
        main_asset_images: all_main_images.value.map((item) => item.image),
        set_main: (name) => {
            frm.set_value("main_assets", name);
            frm.refresh();
        },
    });
}

async function fetchAllAttributeDetails() {
    console.log("Fetching attribute details for code:", props.item_code);
    let attribute_details = {};
    try {
        let resp = await frappe.call({
            method: "webshop.webshop.api.get_item_attribute_details",
            args: {
                item_code: props.item_code,
            },
        });
        if (resp.message) {
            attribute_details = resp.message;
            console.log("Fetched attribute details:", attribute_details);
            loading_attribute_details.value = false;
            attribute_data.value = attribute_details;
            console.log(
                "Attribute data:",
                Object.keys(attribute_data.value).length
            );
        }
    } catch (error) {
        console.error("Error fetching attribute details:", error);
        loading_attribute_details.value = false;
    }
    return attribute_details;
}

async function getMainSlideshow() {
    let website_slideshow_name = props.frm.doc.main_assets;
    if (website_slideshow_name) {
        let resp = await frappe.db.get_doc(
            "Website Slideshow",
            website_slideshow_name
        );
        console.log("Fetched Main Slideshow:", resp);
        all_main_images.value = resp.slideshow_items;
    } else {
        console.warn("No main slideshow found for item code:", props.item_code);
        all_main_images.value = [];
    }
}

async function addToMainSlideshow() {
    let slideshow_items = await getMainSlideshow();
    console.log("Adding to Main Slideshow:", slideshow_items);
}

onMounted(() => {
    fetchAllAttributeDetails();
    getMainSlideshow();
});
</script>
<style scoped>
.asset-group-row {
    margin-bottom: 1rem;
}

.add-new-image {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 125px;
    height: 125px;
    border: 2px dashed var(--border-color);
    border-radius: 10px;
}

.image-previews {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(125px, 1fr));
    gap: 1rem;
}

.add-new-image button {
    background: transparent;
    border: none;
}
</style>
