<script setup lang="ts">
import storeNavigation from "@/stores/navigation";
import { storeToRefs } from "pinia";

// Props
withDefaults(
  defineProps<{
    block?: boolean;
    height?: string;
    rounded?: boolean;
    withTag?: boolean;
  }>(),
  {
    block: false,
    height: "",
    rounded: false,
    withTag: false,
  },
);
const navigationStore = storeNavigation();
const { activePlatformsDrawer } = storeToRefs(navigationStore);
</script>
<template>
  <v-btn
    icon
    :block="block"
    variant="flat"
    rounded="1"
    :height="height"
    class="py-4 bg-background d-flex align-center justify-center"
    :class="{ rounded: rounded }"
    :color="activePlatformsDrawer ? 'toplayer' : 'background'"
    @click="navigationStore.switchActivePlatformsDrawer"
  >
    <div class="d-flex flex-column align-center">
      <v-icon :color="$route.name == 'platform' ? 'primary' : ''"
        >mdi-controller</v-icon
      >
      <v-expand-transition>
        <span
          v-if="withTag"
          class="text-caption text-center"
          :class="{ 'text-primary': $route.name == 'platform' }"
          >Platforms</span
        >
      </v-expand-transition>
    </div>
  </v-btn>
</template>
