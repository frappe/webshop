<template>
    <div class="wrapper">
        <div class="foreground delete">
            <button
                @click="deleteImage"
                v-html="frappe.utils.icon('delete', 'sm')"
            ></button>
        </div>
        <img class="image-preview" :src="image" alt="" />
    </div>
</template>

<script setup>
import { defineProps } from "vue";
let props = defineProps({
    image: String,
    item_code: String,
});

let emit = defineEmits(["delete"]);
async function deleteImage() {
    let dialog = new frappe.ui.Dialog({
        title: "Confirm Deletion",
        fields: [
            {
                fieldtype: "HTML",
                options: `<p>Are you sure you want to delete this image?</p>`,
            },
        ],
        primary_action_label: "Delete",
        primary_action: async () => {
            console.log("Delete image:", props.image);
            let resp = await frappe.call({
                method: "webshop.webshop.api.delete_from_slideshow",
                type: "POST",
                args: {
                    name: `${props.item_code}-webshop-generated`,
                    image_url: props.image,
                },
            });
            console.log("Delete response:", resp);
            emit("delete");
            dialog.hide();
        },
    }).show();
}
</script>

<style scoped>
.wrapper {
    position: relative;
    width: 125px;
    height: 125px;
    overflow: hidden;
    border-radius: 10px;
    border: 2px solid var(--border-color);
}
.foreground {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    opacity: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1;
}
.foreground:hover {
    opacity: 1;
    transition: opacity 0.3s ease-in-out;
}
.image-preview {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 125px;
    height: 125px;
    border-radius: 10px;
}
button {
    background: transparent;
    border: none;
}
</style>
