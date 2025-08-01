<script setup lang="ts">
import collectionApi from "@/services/api/collection";
import romApi from "@/services/api/rom";
import socket from "@/services/socket";
import storeAuth from "@/stores/auth";
import storeCollections, { type Collection } from "@/stores/collections";
import storeGalleryView from "@/stores/galleryView";
import storeHeartbeat from "@/stores/heartbeat";
import storeRoms from "@/stores/roms";
import storeScanning from "@/stores/scanning";
import type { Events } from "@/types/emitter";
import type { Emitter } from "mitt";
import { storeToRefs } from "pinia";
import { inject, ref } from "vue";
import { useRoute } from "vue-router";
import { useDisplay } from "vuetify";

// Props
const { smAndDown } = useDisplay();
const romsStore = storeRoms();
const galleryViewStore = storeGalleryView();
const { scrolledToTop } = storeToRefs(galleryViewStore);
const { selectedRoms } = storeToRefs(romsStore);
const emitter = inject<Emitter<Events>>("emitter");
const fabMenu = ref(false);
emitter?.on("openFabMenu", (open) => {
  fabMenu.value = open;
});
const auth = storeAuth();
const scanningStore = storeScanning();
const collectionsStore = storeCollections();
const { favCollection } = storeToRefs(collectionsStore);
const route = useRoute();
const heartbeat = storeHeartbeat();

// Functions
function scrollToTop() {
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: "smooth",
  });
}
async function onScan() {
  scanningStore.set(true);
  const romCount = romsStore.selectedRoms.length;
  emitter?.emit("snackbarShow", {
    msg: `Scanning ${romCount} game${romCount > 1 ? "s" : ""}...`,
    icon: "mdi-loading mdi-spin",
    color: "primary",
  });

  if (!socket.connected) socket.connect();
  socket.emit("scan", {
    platforms: [Number(route.params.platform)],
    roms_ids: romsStore.selectedRoms.map((r) => r.id),
    type: "quick", // Quick scan so we can filter by selected roms
    apis: heartbeat.getEnabledMetadataOptions().map((s) => s.value),
  });
}

function selectAllRoms() {
  romsStore.setSelection(romsStore.allRoms);
}

function resetSelection() {
  romsStore.resetSelection();
  emitter?.emit("openFabMenu", false);
}

async function addToFavourites() {
  if (!favCollection.value) return;
  favCollection.value.rom_ids = favCollection.value.rom_ids.concat(
    selectedRoms.value.map((r) => r.id),
  );
  await collectionApi
    .updateCollection({ collection: favCollection.value as Collection })
    .then(({ data }) => {
      emitter?.emit("snackbarShow", {
        msg: "Roms added to favourites successfully!",
        icon: "mdi-check-bold",
        color: "green",
        timeout: 2000,
      });
    })
    .catch((error) => {
      console.log(error);
      emitter?.emit("snackbarShow", {
        msg: error.response.data.detail,
        icon: "mdi-close-circle",
        color: "red",
      });
      return;
    })
    .finally(() => {
      emitter?.emit("showLoadingDialog", { loading: false, scrim: false });
    });
}

async function removeFromFavourites() {
  if (!favCollection.value) return;
  favCollection.value.rom_ids = favCollection.value.rom_ids.filter(
    (value) => !selectedRoms.value.map((r) => r.id).includes(value),
  );
  if (romsStore.currentCollection?.name.toLowerCase() == "favourites") {
    romsStore.remove(selectedRoms.value);
  }
  await collectionApi
    .updateCollection({ collection: favCollection.value as Collection })
    .then(({ data }) => {
      emitter?.emit("snackbarShow", {
        msg: "Roms removed from favourites successfully!",
        icon: "mdi-check-bold",
        color: "green",
        timeout: 2000,
      });
      favCollection.value = data;
      collectionsStore.update(data);
    })
    .catch((error) => {
      console.log(error);
      emitter?.emit("snackbarShow", {
        msg: error.response.data.detail,
        icon: "mdi-close-circle",
        color: "red",
      });
      return;
    })
    .finally(() => {
      emitter?.emit("showLoadingDialog", { loading: false, scrim: false });
    });
}

function onDownload() {
  romsStore.selectedRoms.forEach((rom, index) => {
    setTimeout(() => {
      romApi.downloadRom({ rom });
    }, index * 100); // Prevents the download from being blocked by the browser
  });
}
</script>

<template>
  <div
    id="multi-select-overlay"
    class="text-right sticky-bottom"
    :class="{
      'bottom-0': !smAndDown,
      'bottom-50': smAndDown,
    }"
  >
    <v-speed-dial
      location="left bottom"
      transition="fade-transition"
      v-model="fabMenu"
    >
      <template #activator="{ props }">
        <v-fab-transition>
          <v-btn
            v-show="selectedRoms.length > 0"
            class="rounded border-selected"
            color="primary"
            v-bind="props"
            elevation="8"
            icon
            :size="40"
            rounded="0"
            >{{ selectedRoms.length }}</v-btn
          >
        </v-fab-transition>
      </template>

      <v-btn
        title="Unselect all"
        key="1"
        color="toplayer"
        elevation="8"
        icon="mdi-select"
        class="rounded"
        :size="35"
        rounded="0"
        @click.stop="resetSelection"
      />
      <v-btn
        title="Select all"
        key="2"
        color="toplayer"
        elevation="8"
        icon="mdi-select-all"
        class="rounded"
        :size="35"
        rounded="0"
        @click.stop="selectAllRoms"
      />
      <v-btn
        title="Add to favourites"
        key="3"
        color="toplayer"
        elevation="8"
        icon="mdi-star"
        class="rounded"
        :size="35"
        rounded="0"
        @click="addToFavourites"
      />
      <v-btn
        title="Remove from favourites"
        key="4"
        color="toplayer"
        elevation="8"
        icon="mdi-star-remove-outline"
        class="rounded"
        :size="35"
        rounded="0"
        @click="removeFromFavourites"
      />
      <v-btn
        title="Add to collection"
        key="5"
        color="toplayer"
        elevation="8"
        icon="mdi-bookmark-plus"
        class="rounded"
        :size="35"
        rounded="0"
        @click="
          emitter?.emit('showAddToCollectionDialog', romsStore.selectedRoms)
        "
      />
      <v-btn
        title="Remove from collection"
        key="6"
        color="toplayer"
        elevation="8"
        icon="mdi-bookmark-remove-outline"
        class="rounded"
        :size="35"
        rounded="0"
        @click="
          emitter?.emit(
            'showRemoveFromCollectionDialog',
            romsStore.selectedRoms,
          )
        "
      />
      <v-btn
        title="Download roms"
        key="7"
        color="toplayer"
        elevation="8"
        icon="mdi-download"
        class="rounded"
        :size="35"
        rounded="0"
        @click="onDownload"
      />
      <v-btn
        title="Refresh metadata"
        key="8"
        v-if="auth.scopes.includes('roms.write')"
        color="toplayer"
        elevation="8"
        icon="mdi-magnify-scan"
        class="rounded"
        :size="35"
        rounded="0"
        @click="onScan"
      />
      <v-btn
        title="Delete roms"
        key="9"
        v-if="auth.scopes.includes('roms.write')"
        color="toplayer"
        elevation="8"
        icon
        class="rounded"
        :size="35"
        rounded="0"
        @click="emitter?.emit('showDeleteRomDialog', romsStore.selectedRoms)"
      >
        <v-icon color="romm-red"> mdi-delete </v-icon>
      </v-btn>
    </v-speed-dial>
  </div>

  <div
    class="text-right sticky-bottom"
    :class="{
      'bottom-0': !smAndDown,
      'bottom-50': smAndDown,
    }"
    :style="{
      'padding-bottom': selectedRoms.length > 0 ? '62px' : '10px',
    }"
  >
    <v-scroll-y-reverse-transition>
      <v-btn
        icon
        v-show="!scrolledToTop"
        class="border-selected rounded ml-2"
        color="background"
        elevation="8"
        :size="40"
        rounded="0"
        @click="scrollToTop"
        ><v-icon color="primary">mdi-chevron-up</v-icon></v-btn
      >
    </v-scroll-y-reverse-transition>
  </div>
</template>
<style scoped>
.sticky-bottom {
  position: fixed;
  left: 0;
  width: 100%;
  z-index: 9999;
  pointer-events: none;
  padding-right: 10px !important;
}
#multi-select-overlay {
  padding-bottom: 10px !important;
}
.sticky-bottom * {
  pointer-events: auto; /* Re-enables pointer events for all child elements */
}
</style>
