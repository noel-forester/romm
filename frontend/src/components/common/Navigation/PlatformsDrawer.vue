<script setup lang="ts">
import PlatformListItem from "@/components/common/Platform/ListItem.vue";
import storeNavigation from "@/stores/navigation";
import storePlatforms from "@/stores/platforms";
import { storeToRefs } from "pinia";
import { useDisplay } from "vuetify";
import { useI18n } from "vue-i18n";

// Props
const { t } = useI18n();
const navigationStore = storeNavigation();
const { smAndDown } = useDisplay();
const platformsStore = storePlatforms();
const { filteredPlatforms, searchText } = storeToRefs(platformsStore);
const { activePlatformsDrawer } = storeToRefs(navigationStore);

function clear() {
  searchText.value = "";
}
</script>
<template>
  <v-navigation-drawer
    mobile
    :location="smAndDown ? 'top' : 'left'"
    @update:model-value="clear"
    width="500"
    v-model="activePlatformsDrawer"
    :class="{
      'mx-2': smAndDown || activePlatformsDrawer,
      'my-2': !smAndDown || activePlatformsDrawer,
      'drawer-mobile': smAndDown,
      'drawer-desktop': !smAndDown,
    }"
    class="bg-surface pa-1"
    style="height: unset"
    rounded
    :border="0"
  >
    <template #prepend>
      <v-text-field
        v-model="searchText"
        prepend-inner-icon="mdi-filter-outline"
        clearable
        hide-details
        @click:clear="clear"
        @update:model-value=""
        single-line
        :label="t('platform.search-platform')"
        variant="solo-filled"
        density="compact"
      ></v-text-field>
    </template>
    <v-list lines="two" class="py-1 px-0">
      <platform-list-item
        v-for="platform in filteredPlatforms"
        :key="platform.slug"
        :platform="platform"
      />
    </v-list>
  </v-navigation-drawer>
</template>
<style scoped>
.drawer-mobile {
  width: calc(100% - 16px) !important;
}
</style>
