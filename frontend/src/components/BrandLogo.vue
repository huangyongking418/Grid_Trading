<template>
  <svg
    class="brand-logo"
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="网格策 logo"
  >
    <defs>
      <linearGradient :id="gradId" x1="6" y1="6" x2="42" y2="42" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#38bdf8" />
        <stop offset="1" stop-color="#6366f1" />
      </linearGradient>
      <clipPath :id="clipId">
        <rect x="1" y="1" width="46" height="46" rx="11" />
      </clipPath>
    </defs>
    <g :clip-path="`url(#${clipId})`">
      <rect x="1" y="1" width="46" height="46" rx="11" fill="#081428" />
      <path
        d="M13 1V47M25 1V47M37 1V47M1 13H47M1 25H47M1 37H47"
        stroke="#7dd3fc"
        stroke-opacity="0.16"
        stroke-width="1"
      />
      <path
        d="M8 37.5L16 31l5 3 8-10 11-11"
        :stroke="`url(#${gradId})`"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle cx="16" cy="31" r="2.2" fill="#7dd3fc" />
      <circle cx="21" cy="34" r="2.2" fill="#7dd3fc" />
      <circle cx="29" cy="24" r="2.2" fill="#93c5fd" />
      <circle cx="40" cy="13" r="2.6" fill="#38bdf8" />
    </g>
    <rect
      x="1"
      y="1"
      width="46"
      height="46"
      rx="11"
      :stroke="`url(#${gradId})`"
      stroke-width="1.6"
    />
  </svg>
</template>

<script setup>
import { useId } from 'vue'

defineProps({
  size: { type: Number, default: 40 },
})

const uid = useId()
const gradId = `brand-grad-${uid}`
const clipId = `brand-clip-${uid}`
</script>

<style scoped>
.brand-logo {
  display: block;
  flex-shrink: 0;
  filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.35));
}
</style>
