import { defineStore } from "pinia";
import type { SimpleRom } from "@/stores/roms";

interface ScanningPlatforms {
  name: string;
  slug: string;
  fs_slug: string;
  id: number;
  roms: SimpleRom[];
}

export default defineStore("scanning", {
  state: () => ({
    scanning: false,
    scanningPlatforms: [] as ScanningPlatforms[],
    scanStats: {
      scanned_platforms: 0,
      added_platforms: 0,
      metadata_platforms: 0,
      scanned_roms: 0,
      added_roms: 0,
      metadata_roms: 0,
    },
  }),

  actions: {
    set(scanning: boolean) {
      this.scanning = scanning;
    },
    reset() {
      this.scanning = false;
      this.scanningPlatforms = [] as ScanningPlatforms[];
      this.scanStats = {
        scanned_platforms: 0,
        added_platforms: 0,
        metadata_platforms: 0,
        scanned_roms: 0,
        added_roms: 0,
        metadata_roms: 0,
      };
    },
  },
});
