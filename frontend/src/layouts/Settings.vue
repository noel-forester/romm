<script setup lang="ts">
import RFooter from "@/components/Settings/Footer.vue";
</script>

<template>
  <!-- # Bottom padding needed to avoid footer overlap -->
  <div class="pb-12">
    <router-view />
  </div>
  <r-footer />
</template>
