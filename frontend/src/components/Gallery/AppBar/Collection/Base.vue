<script setup lang="ts">
import FilterBtn from "@/components/Gallery/AppBar/common/FilterBtn.vue";
import CollectionInfoDrawer from "@/components/Gallery/AppBar/Collection/CollectionInfoDrawer.vue";
import FilterDrawer from "@/components/Gallery/AppBar/common/FilterDrawer/Base.vue";
import FilterTextField from "@/components/Gallery/AppBar/common/FilterTextField.vue";
import GalleryViewBtn from "@/components/Gallery/AppBar/common/GalleryViewBtn.vue";
import RAvatar from "@/components/common/Collection/RAvatar.vue";
import SelectingBtn from "@/components/Gallery/AppBar/common/SelectingBtn.vue";
import { storeToRefs } from "pinia";
import storeNavigation from "@/stores/navigation";
import storeRoms from "@/stores/roms";
import { useDisplay } from "vuetify";

// Props
const { xs, smAndDown } = useDisplay();
const navigationStore = storeNavigation();
const romsStore = storeRoms();
const { currentCollection } = storeToRefs(romsStore);
</script>

<template>
  <v-app-bar
    elevation="0"
    density="compact"
    class="ma-2"
    :class="{
      'gallery-app-bar-mobile': smAndDown,
      'gallery-app-bar-desktop': !smAndDown,
    }"
    rounded
  >
    <template #prepend>
      <r-avatar
        @click="navigationStore.switchActiveCollectionInfoDrawer"
        class="collection-icon cursor-pointer"
        v-if="currentCollection"
        :size="45"
        :collection="currentCollection"
      />
      <filter-btn />
    </template>
    <filter-text-field v-if="!xs" />
    <template #append>
      <selecting-btn />
      <gallery-view-btn />
    </template>
  </v-app-bar>

  <collection-info-drawer />
  <filter-drawer />
</template>

<style scoped>
.gallery-app-bar-desktop {
  width: calc(100% - 76px) !important;
}
.gallery-app-bar-mobile {
  width: calc(100% - 16px) !important;
}
.collection-icon {
  transition:
    filter 0.15s ease-in-out,
    transform 0.15s ease-in-out;
}
.collection-icon:hover,
.collection-icon.active {
  transform: scale(1.1);
}
</style>
