<template>
    <div class="asset-group-row">
        <div class="column-images">
            <div
                v-if="slideshowImages && slideshowImages.length"
                class="image-previews"
            >
                <div
                    v-for="image in slideshowImages"
                    :key="image.name"
                    class="image-thumbnail"
                >
                    <img :src="image.image" :alt="image.alt" />
                </div>
            </div>
            <div v-else class="no-images-placeholder">
                <p>No images in this group.</p>
            </div>
        </div>
        <div class="column-attributes">
            <div class="variant-attributes">
                <span
                    v-for="(value, index) in variantAttribute"
                    :key="value.id"
                    class="attribute-tag"
                >
                    {{ value.attribute_value
                    }}<span v-if="index !== variantAttribute.length - 1"
                        >,</span
                    >
                </span>
            </div>
        </div>
        <div class="column-actions">
            <button
                class="btn btn-sm"
                @click="editGroup"
                v-html="frappe.utils.icon('edit', 'sm')"
            ></button>
            <button
                class="btn btn-sm"
                @click="deleteGroup"
                v-html="frappe.utils.icon('delete', 'sm')"
            ></button>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
let props = defineProps({
    for_attribute: String,
    slideshow: String,
});

let variantAttribute = ref(null);
let slideshowImages = ref(null);

async function fetchVariantAttribute() {
    let resp = await frappe.db.get_doc("Variant Selection", props.for_attribute);
    console.log("Fetched Variant Attribute:", resp);
    variantAttribute.value = resp.item_variant_selection;
}

async function fetchSlideshow() {
    let resp = await frappe.db.get_doc("Website Slideshow", props.slideshow);
    console.log("Fetched Slideshow:", resp);
    slideshowImages.value = resp.slideshow_items;
}

function editGroup() {
    console.log("Edit group clicked");
    // TODO: Implement edit functionality
}

function deleteGroup() {
    console.log("Delete group clicked");
    // TODO: Implement delete functionality
}

onMounted(() => {
    console.log("AssetViewerItem mounted");
    fetchVariantAttribute();
    fetchSlideshow();
});
</script>

<style scoped>
.asset-group-row {
    display: flex;
    align-items: center;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    margin-bottom: 1rem;
    background-color: var(--card-bg);
    box-shadow: var(--shadow-sm);
    padding: 0.75rem 1rem;
}

.column-images {
    flex: 1;
    min-width: 0;
}

.column-attributes {
    flex: 1;
    padding: 0 1rem;
    min-width: 0;
}

.column-actions {
    display: flex;
    gap: 0.5rem;
}

.variant-attributes {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.card-actions {
    display: flex;
    gap: 0.5rem;
}

.image-previews {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.image-thumbnail {
    position: relative;
    width: 60px;
    height: 60px;
    border-radius: var(--border-radius);
    overflow: hidden;
    border: 1px solid var(--border-color);
}

.image-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.no-images-placeholder {
    text-align: center;
    padding: 2rem;
    color: var(--text-muted);
}
</style>
