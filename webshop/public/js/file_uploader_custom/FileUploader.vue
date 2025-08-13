<template>
    <div
        class="file-uploader"
        @dragover.prevent="dragover"
        @dragleave.prevent="dragleave"
        @drop.prevent="dropfiles"
    >
        <div
            class="file-upload-area"
            v-show="files.length === 0 && !show_file_browser && !show_web_link"
        >
            <div v-if="!is_dragging">
                <div class="text-center">
                    {{ __("Drag and drop files here or upload from") }}
                </div>
                <div class="mt-3 text-center">
                    <button class="btn btn-file-upload" @click="browse_files">
                        <svg
                            width="30"
                            height="30"
                            viewBox="0 0 30 30"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <circle
                                cx="15"
                                cy="15"
                                r="15"
                                fill="var(--subtle-fg)"
                            />
                            <path
                                d="M13.5 22V19"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M16.5 22V19"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M10.5 22H19.5"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M7.5 16H22.5"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M21 8H9C8.17157 8 7.5 8.67157 7.5 9.5V17.5C7.5 18.3284 8.17157 19 9 19H21C21.8284 19 22.5 18.3284 22.5 17.5V9.5C22.5 8.67157 21.8284 8 21 8Z"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                        </svg>
                        <div class="mt-1">{{ __("My Device") }}</div>
                    </button>
                    <input
                        type="file"
                        class="hidden"
                        ref="file_input"
                        @change="on_file_input"
                        :multiple="allow_multiple"
                        :accept="
                            (restrictions.allowed_file_types || []).join(', ')
                        "
                    />
                    <button
                        class="btn btn-file-upload"
                        v-if="!disable_file_browser"
                        @click="show_file_browser = true"
                    >
                        <svg
                            width="30"
                            height="30"
                            viewBox="0 0 30 30"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <circle
                                cx="15"
                                cy="15"
                                r="15"
                                fill="var(--subtle-fg)"
                            />
                            <path
                                d="M13.0245 11.5H8C7.72386 11.5 7.5 11.7239 7.5 12V20C7.5 21.1046 8.39543 22 9.5 22H20.5C21.6046 22 22.5 21.1046 22.5 20V14.5C22.5 14.2239 22.2761 14 22 14H15.2169C15.0492 14 14.8926 13.9159 14.8 13.776L13.4414 11.724C13.3488 11.5841 13.1922 11.5 13.0245 11.5Z"
                                stroke="var(--text-color)"
                                stroke-miterlimit="10"
                                stroke-linecap="square"
                            />
                            <path
                                d="M8.87939 9.5V8.5C8.87939 8.22386 9.10325 8 9.37939 8H20.6208C20.8969 8 21.1208 8.22386 21.1208 8.5V12"
                                stroke="var(--text-color)"
                                stroke-miterlimit="10"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                        </svg>
                        <div class="mt-1">{{ __("Library") }}</div>
                    </button>
                    <button
                        class="btn btn-file-upload"
                        v-if="allow_web_link"
                        @click="show_web_link = true"
                    >
                        <svg
                            width="30"
                            height="30"
                            viewBox="0 0 30 30"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <circle
                                cx="15"
                                cy="15"
                                r="15"
                                fill="var(--subtle-fg)"
                            />
                            <path
                                d="M12.0469 17.9543L17.9558 12.0454"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M13.8184 11.4547L15.7943 9.47873C16.4212 8.85205 17.2714 8.5 18.1578 8.5C19.0443 8.5 19.8945 8.85205 20.5214 9.47873V9.47873C21.1481 10.1057 21.5001 10.9558 21.5001 11.8423C21.5001 12.7287 21.1481 13.5789 20.5214 14.2058L18.5455 16.1818"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M11.4547 13.8184L9.47873 15.7943C8.85205 16.4212 8.5 17.2714 8.5 18.1578C8.5 19.0443 8.85205 19.8945 9.47873 20.5214V20.5214C10.1057 21.1481 10.9558 21.5001 11.8423 21.5001C12.7287 21.5001 13.5789 21.1481 14.2058 20.5214L16.1818 18.5455"
                                stroke="var(--text-color)"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                        </svg>
                        <div class="mt-1">{{ __("Link") }}</div>
                    </button>
                    <button
                        v-if="allow_take_photo"
                        class="btn btn-file-upload"
                        @click="capture_image"
                    >
                        <svg
                            width="30"
                            height="30"
                            viewBox="0 0 30 30"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <circle
                                cx="15"
                                cy="15"
                                r="15"
                                fill="var(--subtle-fg)"
                            />
                            <path
                                d="M11.5 10.5H9.5C8.67157 10.5 8 11.1716 8 12V20C8 20.8284 8.67157 21.5 9.5 21.5H20.5C21.3284 21.5 22 20.8284 22 20V12C22 11.1716 21.3284 10.5 20.5 10.5H18.5L17.3 8.9C17.1111 8.64819 16.8148 8.5 16.5 8.5H13.5C13.1852 8.5 12.8889 8.64819 12.7 8.9L11.5 10.5Z"
                                stroke="var(--text-color)"
                                stroke-linejoin="round"
                            />
                            <circle
                                cx="15"
                                cy="16"
                                r="2.5"
                                stroke="var(--text-color)"
                            />
                        </svg>
                        <div class="mt-1">{{ __("Camera") }}</div>
                    </button>
                    <button
                        v-if="
                            allow_google_drive && google_drive_settings.enabled
                        "
                        class="btn btn-file-upload"
                        @click="show_google_drive_picker"
                    >
                        <svg width="30" height="30">
                            <image
                                href="/assets/frappe/icons/social/google_drive.svg"
                                width="30"
                                height="30"
                            />
                        </svg>
                        <div class="mt-1">{{ __("Google Drive") }}</div>
                    </button>
                </div>
                <div class="mt-3 text-center" v-if="upload_notes">
                    {{ upload_notes }}
                </div>
            </div>
            <div v-else>
                {{ __("Drop files here") }}
            </div>
        </div>
        <div
            class="file-preview-area"
            v-show="files.length && !show_file_browser && !show_web_link"
        >
            <div class="file-preview-container" v-if="!show_image_cropper">
                <FilePreview
                    v-for="(file, i) in files"
                    :key="file.name"
                    :file="file"
                    :allow_toggle_private="allow_toggle_private"
                    :allow_toggle_optimize="allow_toggle_optimize"
                    @remove="remove_file(file)"
                    @toggle_private="file.private = !file.private"
                    @toggle_optimize="file.optimize = !file.optimize"
                    @toggle_image_cropper="toggle_image_cropper(i)"
                />
            </div>
            <div
                class="flex align-items-center justify-content-end"
                v-if="show_upload_button && currently_uploading === -1"
            >
                <button
                    class="btn btn-primary btn-sm margin-right"
                    @click="() => upload_files()"
                >
                    <span v-if="files.length === 1">
                        {{ __("Upload file") }}
                    </span>
                    <span v-else>
                        {{ __("Upload {0} files", [files.length]) }}
                    </span>
                </button>
            </div>
        </div>
        <ImageCropper
            v-if="show_image_cropper && wrapper_ready"
            :file="files[crop_image_with_index]"
            :fixed_aspect_ratio="restrictions.crop_image_aspect_ratio"
            @toggle_image_cropper="toggle_image_cropper(-1)"
            @upload_after_crop="trigger_upload = true"
        />
        <FileBrowser
            ref="file_browser"
            v-if="show_file_browser && !disable_file_browser"
            @hide-browser="show_file_browser = false"
        />
        <WebLink
            ref="web_link"
            v-if="show_web_link"
            @hide-web-link="show_web_link = false"
        />
    </div>
    <div v-if="!for_main">
        <div v-if="!loading_attribute_details" class="attribute-selection-area">
            <h5 class="attribute-heading">Product Attributes</h5>
            <div
                v-for="(values, attribute_name) in attribute_data"
                :key="attribute_name"
                class="attribute-group"
            >
                <div class="attribute-name">{{ attribute_name }}:</div>
                <div class="attribute-values">
                    <label
                        v-for="value in values"
                        :key="value.attribute_value"
                        class="attribute-value-option"
                        :class="{
                            disabled: isOptionDisabled(
                                attribute_name,
                                value.attribute_value
                            ),
                        }"
                    >
                        <input
                            type="checkbox"
                            :value="value.attribute_value"
                            v-model="selectedAttributes[attribute_name]"
                            @change="
                                (event) =>
                                    updateSelectedAttributes(
                                        attribute_name,
                                        value.attribute_value,
                                        value.abbr,
                                        event.target.checked
                                    )
                            "
                            :disabled="
                                isOptionDisabled(
                                    attribute_name,
                                    value.attribute_value
                                )
                            "
                        />
                        <span class="attribute-value-label">{{
                            value.attribute_value
                        }}</span>
                    </label>
                </div>
            </div>
            <!-- <div
            v-if="Object.keys(selectedAttributes).length > 0"
            class="selected-attributes"
        >
            <h6>Selected Attributes:</h6>
            <ul>
                <li
                    v-for="(values, attr) in selectedAttributes"
                    :key="attr"
                >
                    <strong>{{ attr }}:</strong> {{ values.join(', ') }}
                </li>
            </ul>
        </div> -->
        </div>
        <div v-else class="attribute-loading">
            <span>Loading attribute details...</span>
        </div>
    </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from "vue";
import FilePreview from "./FilePreview.vue";
import FileBrowser from "./FileBrowser.vue";
import WebLink from "./WebLink.vue";
import GoogleDrivePicker from "../integrations/google_drive_picker";
import ImageCropper from "./ImageCropper.vue";

// props
const props = defineProps({
    disable_file_browser: {
        default: false,
    },
    allow_multiple: {
        default: true,
    },
    as_dataurl: {
        default: false,
    },
    doctype: {
        default: null,
    },
    docname: {
        default: null,
    },
    fieldname: {
        default: null,
    },
    folder: {
        default: "Home",
    },
    method: {
        default: null,
    },
    on_success: {
        default: null,
    },
    make_attachments_public: {
        default: null,
    },
    restrictions: {
        default: () => ({
            max_file_size: null, // 2048 -> 2KB
            max_number_of_files: null,
            allowed_file_types: [], // ['image/*', 'video/*', '.jpg', '.gif', '.pdf'],
            crop_image_aspect_ratio: null, // 1, 16 / 9, 4 / 3, NaN (free)
        }),
    },
    attach_doc_image: {
        default: false,
    },
    upload_notes: {
        default: null, // "Images or video, upto 2MB"
    },
    allow_web_link: {
        default: true,
    },
    allow_take_photo: {
        default: true,
    },
    allow_toggle_private: {
        default: true,
    },
    allow_toggle_optimize: {
        default: true,
    },
    allow_google_drive: {
        default: true,
    },
    item_code: {
        type: String,
        required: true,
    },
    add_to_table: {
        type: Function,
    },
    dialog: {
        type: Object,
        required: true,
    },
    // TODO: fix names
    for_main: {
        type: Boolean,
        default: false,
    },
    main_assets: {
        type: String,
    },
    main_asset_images: {
        type: Array,
        default: () => [],
    },
    set_main: {
        type: Function,
    },
});

// variables
let files = ref([]);
let file_input = ref(null);
let file_browser = ref(null);
let web_link = ref(null);
let is_dragging = ref(false);
let currently_uploading = ref(-1);
let show_file_browser = ref(false);
let show_web_link = ref(false);
let show_image_cropper = ref(false);
let crop_image_with_index = ref(-1);
let trigger_upload = ref(false);
let close_dialog = ref(false);
let hide_dialog_footer = ref(false);
let allow_take_photo = ref(false);
let google_drive_settings = ref({
    enabled: false,
});
let wrapper_ready = ref(false);

let loading_attribute_details = ref(true);
let attribute_data = ref({});
let selectedAttributes = ref({});
let fileDocs = ref([]);
let variant_selection_name_list = ref([]);
// created
if (props.allow_take_photo) {
    allow_take_photo.value = window.navigator.mediaDevices;
}

if (frappe.user_id !== "Guest" && props.allow_google_drive) {
    frappe.call({
        // method only available after login
        method: "frappe.integrations.doctype.google_settings.google_settings.get_file_picker_settings",
        callback: (resp) => {
            if (!resp.exc) {
                google_drive_settings.value = resp.message;
            }
        },
    });
}
if (props.restrictions.max_file_size == null) {
    frappe.call("frappe.core.api.file.get_max_file_size").then((res) => {
        props.restrictions.max_file_size = Number(res.message);
    });
}
if (props.restrictions.max_number_of_files == null && props.doctype) {
    props.restrictions.max_number_of_files = frappe.get_meta(
        props.doctype
    )?.max_attachments;
}

// methods
function dragover() {
    is_dragging.value = true;
}
function dragleave() {
    is_dragging.value = false;
}
function dropfiles(e) {
    is_dragging.value = false;
    add_files(e.dataTransfer.files);
}
function browse_files() {
    file_input.value.click();
}
function on_file_input(e) {
    add_files(file_input.value.files);
}
function remove_file(file) {
    files.value = files.value.filter((f) => f !== file);
}
function toggle_image_cropper(index) {
    crop_image_with_index.value = show_image_cropper.value ? -1 : index;
    hide_dialog_footer.value = !show_image_cropper.value;
    show_image_cropper.value = !show_image_cropper.value;
}
function toggle_all_private() {
    let flag;
    let private_values = files.value.filter((file) => file.private);
    if (private_values.length < files.value.length) {
        // there are some private and some public
        // set all to private
        flag = true;
    } else {
        // all are private, set all to public
        flag = false;
    }
    files.value = files.value.map((file) => {
        file.private = flag;
        return file;
    });
}
function show_max_files_number_warning(file) {
    console.warn(
        `File skipped because it exceeds the allowed specified limit of ${max_number_of_files} uploads`,
        file
    );
    if (props.doctype) {
        MSG = __(
            'File "{0}" was skipped because only {1} uploads are allowed for DocType "{2}"',
            [file.name, max_number_of_files, props.doctype]
        );
    } else {
        MSG = __(
            'File "{0}" was skipped because only {1} uploads are allowed',
            [file.name, max_number_of_files]
        );
    }
    frappe.show_alert({
        message: MSG,
        indicator: "orange",
    });
}
function add_files(file_array) {
    let _files = Array.from(file_array)
        .filter(check_restrictions)
        .map((file) => {
            let is_image = file.type.startsWith("image");
            let size_kb = file.size / 1024;
            return {
                file_obj: file,
                cropper_file: file,
                crop_box_data: null,
                optimize:
                    size_kb > 200 && is_image && !file.type.includes("svg"),
                name: file.name,
                doc: null,
                progress: 0,
                total: 0,
                failed: false,
                request_succeeded: false,
                error_message: null,
                uploading: false,
                private: !props.make_attachments_public,
            };
        });

    // pop extra files as per FileUploader.restrictions.max_number_of_files
    max_number_of_files = props.restrictions.max_number_of_files;
    if (max_number_of_files && _files.length > max_number_of_files) {
        _files.slice(max_number_of_files).forEach((file) => {
            show_max_files_number_warning(file, props.doctype);
        });

        _files = _files.slice(0, max_number_of_files);
    }

    files.value = files.value.concat(_files);
    // if only one file is allowed and crop_image_aspect_ratio is set, open cropper immediately
    if (
        files.value.length === 1 &&
        !props.allow_multiple &&
        props.restrictions.crop_image_aspect_ratio != null
    ) {
        if (!files.value[0].file_obj.type.includes("svg")) {
            toggle_image_cropper(0);
        }
    }
}
function check_restrictions(file) {
    let { max_file_size, allowed_file_types = [] } = props.restrictions;

    let is_correct_type = true;
    let valid_file_size = true;

    if (allowed_file_types && allowed_file_types.length) {
        is_correct_type = allowed_file_types.some((type) => {
            // is this is a mime-type
            if (type.includes("/")) {
                if (!file.type) return false;
                return file.type.match(type);
            }

            // otherwise this is likely an extension
            if (type[0] === ".") {
                return file.name.toLowerCase().endsWith(type.toLowerCase());
            }
            return false;
        });
    }

    if (max_file_size && file.size != null) {
        valid_file_size = file.size < max_file_size;
    }

    if (!is_correct_type) {
        console.warn("File skipped because of invalid file type", file);
        frappe.show_alert({
            message: __('File "{0}" was skipped because of invalid file type', [
                file.name,
            ]),
            indicator: "orange",
        });
    }
    if (!valid_file_size) {
        console.warn(
            "File skipped because of invalid file size",
            file.size,
            file
        );
        frappe.show_alert({
            message: __('File "{0}" was skipped because size exceeds {1} MB', [
                file.name,
                max_file_size / (1024 * 1024),
            ]),
            indicator: "orange",
        });
    }

    return is_correct_type && valid_file_size;
}
function upload_files(dialog) {
    if (show_file_browser.value) {
        return upload_via_file_browser();
    }
    if (show_web_link.value) {
        return upload_via_web_link();
    }
    if (props.as_dataurl) {
        return return_as_dataurl();
    }
    if (!files.value.length) {
        frappe.msgprint(__("Please select a file first."));
        return Promise.reject();
    }

    dialog?.get_primary_btn().prop("disabled", true);
    dialog?.get_secondary_btn().prop("disabled", true);

    return frappe.run_serially(
        files.value.map((file, i) => () => upload_file(file, i))
    );
}
function upload_via_file_browser() {
    let selected_file = file_browser.value.selected_node;
    if (!selected_file.value) {
        frappe.msgprint(__("Click on a file to select it."));
        close_dialog.value = true;
        return Promise.reject();
    }
    close_dialog.value = true;
    return upload_file({
        library_file_name: selected_file.value,
    });
}
function upload_via_web_link() {
    let file_url = web_link.value.url;
    if (!file_url) {
        frappe.msgprint(__("Invalid URL"));
        close_dialog.value = true;
        return Promise.reject();
    }
    file_url = decodeURI(file_url);
    close_dialog.value = true;
    return upload_file({
        file_url,
    });
}
function return_as_dataurl() {
    let promises = files.value.map((file) =>
        frappe.dom.file_to_base64(file.file_obj).then((dataurl) => {
            file.dataurl = dataurl;
            props.on_success && props.on_success(file);
        })
    );
    close_dialog.value = true;
    return Promise.all(promises);
}
function upload_file(file, i) {
    currently_uploading.value = i;

    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.upload.addEventListener("loadstart", (e) => {
            file.uploading = true;
        });
        xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
                file.progress = e.loaded;
                file.total = e.total;
            }
        });
        xhr.upload.addEventListener("load", (e) => {
            file.uploading = false;
            resolve();
        });
        xhr.addEventListener("error", (e) => {
            file.failed = true;
            reject();
        });
        xhr.onreadystatechange = () => {
            if (xhr.readyState == XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    file.request_succeeded = true;
                    let r = null;
                    let file_doc = null;
                    try {
                        r = JSON.parse(xhr.responseText);
                        if (r.message.doctype === "File") {
                            file_doc = r.message;
                        }
                    } catch (e) {
                        r = xhr.responseText;
                    }

                    file.doc = file_doc;
                    fileDocs.value.push(file_doc);

                    if (props.on_success) {
                        props.on_success(file_doc, r);
                    }

                    if (
                        i == files.value.length - 1 &&
                        files.value.every((file) => file.request_succeeded)
                    ) {
                        // close_dialog.value = true;
                        console.log(
                            "All files uploaded successfully:",
                            fileDocs.value
                        );
                    }
                } else if (xhr.status === 403) {
                    file.failed = true;
                    let response = parse_error_response(xhr.responseText);
                    file.error_message = `Not permitted. ${
                        response.error_message || ""
                    }.`;
                    if (response.server_messages.length) {
                        file.error_message += `\n${response.server_messages.join(
                            "\n"
                        )}`;
                    }
                } else if (xhr.status === 413) {
                    file.failed = true;
                    file.error_message =
                        "Size exceeds the maximum allowed file size.";
                } else if (xhr.status === 417) {
                    // regular frappe.throw() in backend
                    file.failed = true;
                    file.error_message = null;
                    let response = parse_error_response(xhr.responseText);
                    if (response.server_messages.length) {
                        file.error_message =
                            response.server_messages.join("\n");
                    }
                } else {
                    file.failed = true;
                    file.error_message =
                        xhr.status === 0
                            ? "XMLHttpRequest Error"
                            : `${xhr.status} : ${xhr.statusText}`;

                    let error = null;
                    try {
                        error = JSON.parse(xhr.responseText);
                    } catch (e) {
                        // pass
                    }
                    frappe.request.cleanup({}, error);
                }
            }
        };
        xhr.open("POST", "/api/method/upload_file", true);
        xhr.setRequestHeader("Accept", "application/json");
        xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);

        let form_data = new FormData();
        if (file.file_obj) {
            form_data.append("file", file.file_obj, file.name);
        }
        form_data.append("is_private", +file.private);
        form_data.append("folder", props.folder);

        if (file.file_url) {
            form_data.append("file_url", file.file_url);
        }

        if (file.file_name) {
            form_data.append("file_name", file.file_name);
        }
        if (file.library_file_name) {
            form_data.append("library_file_name", file.library_file_name);
        }

        if (props.doctype) {
            form_data.append("doctype", props.doctype);
        }

        if (props.docname) {
            form_data.append("docname", props.docname);
        }

        if (props.fieldname) {
            form_data.append("fieldname", props.fieldname);
        }

        if (props.method) {
            form_data.append("method", props.method);
        }

        if (file.optimize) {
            form_data.append("optimize", true);
        }

        if (props.attach_doc_image) {
            form_data.append("max_width", 200);
            form_data.append("max_height", 200);
        }

        xhr.send(form_data);
    });
}
function parse_error_response(response_text) {
    let response = JSON.parse(response_text);
    let error_message = response._error_message;
    let server_messages = [];

    try {
        server_messages.push(
            ...JSON.parse(response._server_messages).map((m) => {
                let parsed = JSON.parse(m);
                return parsed.message;
            })
        );
    } catch (e) {
        console.warning("Failed to parse server message", e);
    }
    return {
        error_message,
        server_messages,
    };
}
function capture_image() {
    const capture = new frappe.ui.Capture({
        animate: false,
        error: true,
    });
    capture.show();
    capture.submit((data_urls) => {
        data_urls.forEach((data_url) => {
            let filename = `capture_${frappe.datetime
                .now_datetime()
                .replaceAll(/[: -]/g, "_")}.png`;
            url_to_file(data_url, filename, "image/png").then((file) =>
                add_files([file])
            );
        });
    });
}
function show_google_drive_picker() {
    close_dialog.value = true;
    let google_drive = new GoogleDrivePicker({
        pickerCallback: (data) => google_drive_callback(data),
        ...google_drive_settings.value,
    });
    google_drive.loadPicker();
}
function google_drive_callback(data) {
    if (data.action == google.picker.Action.PICKED) {
        upload_file({
            file_url: data.docs[0].url,
            file_name: data.docs[0].name,
        });
    } else if (data.action == google.picker.Action.CANCEL) {
        cur_frm.attachments.new_attachment();
    }
}
function url_to_file(url, filename, mime_type) {
    return fetch(url)
        .then((res) => res.arrayBuffer())
        .then((buffer) => new File([buffer], filename, { type: mime_type }));
}

// computed
let upload_complete = computed(() => {
    return (
        files.value.length > 0 &&
        files.value.every(
            (file) => file.total !== 0 && file.progress === file.total
        )
    );
});

/* --- Item Attribute Selection Code --- */

function isOptionDisabled(attribute_name, value) {
    // If there's any selected value for this attribute and it's not this value,
    // then this option should be disabled
    return (
        selectedAttributes.value[attribute_name] &&
        selectedAttributes.value[attribute_name].length > 0 &&
        !selectedAttributes.value[attribute_name].includes(value)
    );
}

async function handleErrorReporting(resp) {
    let { server_messages } = parse_error_response(await resp.text());
    console.error(
        "Error creating variant selection item:",
        resp.statusText,
        server_messages
    );
    if (resp.statusText == "CONFLICT") {
        frappe.msgprint({
            title: __("Conflict"),
            message: __("Entry for this attribute combination already exists."),
            indicator: "orange",
        });
    } else {
        frappe.msgprint({
            title: __("Error"),
            message: server_messages.join("<br>"),
            indicator: "red",
        });
    }
    props.dialog?.get_primary_btn().prop("disabled", false);
    props.dialog?.get_secondary_btn().prop("disabled", false);
}

function updateSelectedAttributes(attribute_name, value, abbr, checked) {
    // Ensure the attribute exists in selectedAttributes
    if (!selectedAttributes.value[attribute_name]) {
        selectedAttributes.value[attribute_name] = [];
    }

    // If checked, clear any existing selection for this attribute and add the new value
    if (checked) {
        // Reset the array and add only this value
        selectedAttributes.value[attribute_name] = [value];

        // Update the variant selection list
        if (!variant_selection_name_list.value.includes(abbr)) {
            // Check if there was a previous selection for this attribute
            const existingVariantForAttribute =
                variant_selection_name_list.value.find((variant) => {
                    // Find if any variants from the same attribute were previously selected
                    return attribute_data.value[attribute_name].some(
                        (attrValue) =>
                            attrValue.abbr === variant &&
                            attrValue.attribute_value !== value
                    );
                });

            // If there was a previous selection, remove it
            if (existingVariantForAttribute) {
                const index = variant_selection_name_list.value.indexOf(
                    existingVariantForAttribute
                );
                if (index > -1) {
                    variant_selection_name_list.value.splice(index, 1);
                }
            }

            // Add the new selection
            variant_selection_name_list.value.push(abbr);
            console.log(`Selected variant: ${abbr}`);
            console.log(
                "Total name:",
                variant_selection_name_list.value.sort().join("-")
            );
        }
    } else {
        // If unchecked, remove the value
        selectedAttributes.value[attribute_name] = selectedAttributes.value[
            attribute_name
        ].filter((item) => item !== value);

        // Remove from variant selection list
        const index = variant_selection_name_list.value.indexOf(abbr);
        if (index > -1) {
            variant_selection_name_list.value.splice(index, 1);
            console.log(`Deselected variant: ${abbr}`);
        }
    }
    console.log(
        `Selected ${attribute_name}: ${selectedAttributes.value[attribute_name]}`
    );
}

async function fetchAllAttributeDetails() {
    console.log("Fetching attribute details for code:", props.item_code);
    let attribute_details = {};
    try {
        let resp = await fetch(
            `/api/method/webshop.webshop.api.get_item_attribute_details?item_code=${props.item_code}`,
            {
                headers: {
                    "Content-Type": "application/json",
                    "X-Frappe-CSRF-Token": frappe.csrf_token,
                },
            }
        );
        if (resp.ok) {
            attribute_details = await resp.json();
            console.log(
                "Fetched attribute details:",
                attribute_details.message
            );
            loading_attribute_details.value = false;
            attribute_data.value = attribute_details.message;

            // Initialize selectedAttributes with empty arrays for each attribute
            Object.keys(attribute_details.message).forEach((attribute) => {
                selectedAttributes.value[attribute] = [];
            });
        }
    } catch (error) {
        console.error("Error fetching attribute details:", error);
        loading_attribute_details.value = false;
    }
    return attribute_details;
}

async function createSlideshow() {
    const slideshowName = props.for_main
        ? `${props.item_code}-webshop`
        : [
              props.item_code,
              variant_selection_name_list.value.sort().join("-"),
              "webshop",
          ].join("-");
    const imageUrls = [];
    console.log("Creating slideshow with name:", slideshowName, fileDocs.value);
    for (const file of fileDocs.value) {
        console.log("File URL:", file.file_url);
        if (file.file_url) {
            imageUrls.push(file.file_url);
        }
    }
    let resp = await fetch(`/api/method/webshop.webshop.api.create_slideshow`, {
        method: "POST",
        body: JSON.stringify({
            name: slideshowName,
            image_urls: imageUrls,
        }),
        headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": frappe.csrf_token,
        },
    });
    if (resp.ok) {
        let data = await resp.json();
        console.log("Slideshow created successfully:", data);
        return data.message;
    } else {
        await handleErrorReporting(resp);
    }
}

async function createVariantSelectionItem() {
    if (variant_selection_name_list.value.length === 0) return;
    const name = [
        props.item_code,
        variant_selection_name_list.value.sort().join("-"),
    ].join("-");
    let resp = await fetch(
        `/api/method/webshop.webshop.api.create_variant_selection`,
        {
            method: "POST",
            body: JSON.stringify({
                name: name,
                for_item: props.item_code,
                attributes: selectedAttributes.value,
            }),
            headers: {
                "Content-Type": "application/json",
                "X-Frappe-CSRF-Token": frappe.csrf_token,
            },
        }
    );
    if (resp.ok) {
        let data = await resp.json();
        console.log("Variant selection item created successfully:", data);
        return data.message;
    } else {
        await handleErrorReporting(resp);
    }
}

async function updateSlideshow() {
    const slideshowName = `${props.item_code}-webshop`;
    const imageUrls = [];
    console.log("Updating slideshow with name:", slideshowName, fileDocs.value);
    for (const file of fileDocs.value) {
        console.log("File URL:", file.file_url);
        if (file.file_url) {
            imageUrls.push(file.file_url);
        }
    }
    console.log("Image URLs:", imageUrls, props.main_asset_images);
    let resp = await fetch(`/api/method/webshop.webshop.api.update_slideshow`, {
        method: "POST",
        body: JSON.stringify({
            name: slideshowName,
            image_urls: [...imageUrls, ...props.main_asset_images],
        }),
        headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": frappe.csrf_token,
        },
    });
    if (resp.ok) {
        let data = await resp.json();
        console.log("Slideshow created successfully:", data);
        return data.message;
    } else {
        await handleErrorReporting(resp);
    }
}

// watcher
watch(
    files,
    (newvalue, oldvalue) => {
        if (!props.allow_multiple && newvalue.length > 1) {
            files.value = [newvalue[newvalue.length - 1]];
        }
    },
    { deep: true }
);

watch(
    selectedAttributes,
    (newvalue, oldvalue) => {
        console.log("Selected attributes changed:", newvalue);
    },
    { deep: true }
);

watch(
    fileDocs,
    async (newvalue, oldvalue) => {
        console.log("File documents changed:", newvalue);
        if (newvalue.length > 0 && upload_complete.value) {
            // Handle the case when there are new file documents
            if (props.for_main) {
                if (props.main_assets) {
                    await updateSlideshow();
                } else {
                    await createSlideshow();
                }
                props.set_main(`${props.item_code}-webshop`);
            } else {
                let slide_show_response = await createSlideshow();
                let variant_response = await createVariantSelectionItem();
                console.log("Slideshow response:", slide_show_response);
                console.log("Variant response:", variant_response);
                if (variant_response && slide_show_response) {
                    props.add_to_table(
                        variant_response?.name,
                        slide_show_response?.name
                    );
                }
            }
            close_dialog.value = true;
        }
    },
    { deep: true }
);

onMounted(async () => {
    // Initialize file uploader
    console.log("File uploader initializedd");
    await fetchAllAttributeDetails();
});
// TODO: follow this_case instead of thisCase
// TODO: Extract out the variant selector component

defineExpose({
    files,
    add_files,
    upload_files,
    toggle_all_private,
    wrapper_ready,
    close_dialog,
    selectedAttributes,
});
</script>

<style scoped>
.file-upload-area {
    min-height: 16rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px dashed var(--dark-border-color);
    border-radius: var(--border-radius);
    cursor: pointer;
    background-color: var(--bg-color);
}

.btn-file-upload {
    background-color: transparent;
    border: none;
    box-shadow: none;
    font-size: var(--text-xs);
}

/* --- Attribute Selection Styles --- */
.attribute-selection-area {
    margin-top: 1.5rem;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    background-color: var(--bg-light);
}

.attribute-heading {
    margin-bottom: 1rem;
    font-weight: 600;
    color: var(--text-color);
}

.attribute-group {
    margin-bottom: 0.75rem;
}

.attribute-name {
    font-weight: 600;
    margin-bottom: 0.25rem;
}

.attribute-values {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.attribute-value-option {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.5rem;
    background-color: var(--control-bg);
    border-radius: var(--border-radius-sm);
    margin-right: 0.5rem;
    cursor: pointer;
}

.attribute-value-option.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: var(--disabled-control-bg, #f2f2f2);
}

.attribute-value-option.disabled input {
    cursor: not-allowed;
}

.attribute-value-option input {
    margin-right: 0.25rem;
}

.attribute-value-label {
    font-size: var(--text-sm);
}

.selected-attributes {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-color);
}

.selected-attributes h6 {
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.selected-attributes ul {
    padding-left: 1.25rem;
    margin: 0;
}

.attribute-loading {
    display: flex;
    justify-content: center;
    padding: 1rem;
    color: var(--text-muted);
}
</style>
